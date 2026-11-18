"""
agent.py - NaviPress: build one WordPress page with a UF NaviGator agent.
An Agentic Web Observatory project (https://agenticwebobservatory.wordpress.com).

How it works:
  1. Starts wp_mcp_server.py and asks it which tools it offers.
  2. Sends your spec, the site's design rules (rules/*.md) and,
     if you pick one, a skill (skills/<name>/SKILL.md) to a NaviGator model
     through your LiteLLM virtual key.
  3. Whenever the model asks to use a tool, runs it and hands back the result.
     Repeats until the model says it's done.
  4. Asks you for feedback. Type changes and it keeps going; press Enter to stop.
  5. Runs the design-principles audit on the draft and prints the result.
     This happens in code, so it runs even if the model forgot to.

Everything (your words, the model's replies, every tool call and result,
the audit, time and cost) is saved to runs/<date-time>.md for your journal.

Usage:
  python agent.py --skill faq --spec specs/faq.md   (or: python navipress.py build ...)
  python agent.py --spec specs/about.md               # no skill
  python agent.py --spec specs/faq.md --feedback fix.md # revise an earlier draft
  python agent.py --list-skills
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles

SYSTEM_PROMPT = """You are NaviPress, a web-building agent working on ONE page of a WordPress.com website.

How to work:
1. Call get_site_info and list_pages. Call list_sources to see the student's knowledge folder.
2. Read EVERY page and source file the specification names (get_page, read_source) before writing. Read at least two other pages to match the site's voice.
3. Build the page. Create it once with create_draft_page, then improve it with update_draft_page. Each update replaces the whole page, so always send the complete content.
4. Run audit_draft on your page. Fix every issue you can with update_draft_page, then audit again.
5. Write content as WordPress block markup, for example:
   <!-- wp:heading --><h2 class="wp-block-heading">Title</h2><!-- /wp:heading -->
   <!-- wp:paragraph --><p>Text.</p><!-- /wp:paragraph -->
- Do not invent facts, statistics, quotes, links or sources. Use only the specification, the knowledge folder and the site's pages. If you aren't certain, write [CHECK: what needs verifying] in the page.
- You cannot publish. The student will review and publish the page themselves.

When you are finished, reply (without calling a tool) with:
1. What you built, with the page ID, and which pages and sources you actually read.
2. Decisions you made that the specification did NOT ask for. Don't list things the spec told you to do.
3. Anything marked [CHECK], and anything the sources didn't answer."""


def load_skill(name: str) -> tuple[str, int]:
    """Return (skill text, max_words) for skills/<name>/SKILL.md."""
    path = HERE / "skills" / name / "SKILL.md"
    if not path.exists():
        available = ", ".join(sorted(p.name for p in (HERE / "skills").iterdir() if p.is_dir()))
        sys.exit(f"No skill called '{name}'. Available: {available}")
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^max_words:\s*(\d+)", text, re.M)
    return text, int(m.group(1)) if m else 1500


class RunLog:
    """Writes a readable Markdown record of the run."""

    def __init__(self, model: str, spec_path: Path, skill: str | None):
        runs = HERE / "runs"
        runs.mkdir(exist_ok=True)
        self.path = runs / f"{datetime.now():%Y-%m-%d_%H%M%S}.md"
        self.start = time.time()
        self.cost = 0.0
        self.tokens = 0
        self.write(f"# NaviPress run {datetime.now():%Y-%m-%d %H:%M}\n\n"
                   f"- Model: `{model}`\n- Spec: `{spec_path.name}`\n- Skill: `{skill or 'none'}`\n")

    def write(self, text: str) -> None:
        with self.path.open("a", encoding="utf-8") as f:
            f.write(text + "\n")

    def finish(self) -> None:
        mins = (time.time() - self.start) / 60
        self.write(f"\n---\n**Totals:** {mins:.1f} minutes, {self.tokens:,} tokens, "
                   f"${self.cost:.4f} reported by NaviGator.\n")


def short(text: str, n: int = 1500) -> str:
    return text if len(text) <= n else text[:n] + f"\n... [{len(text) - n} more characters]"


def my_page_id(slot: str) -> int | None:
    state_file = HERE / "agent_pages.json"
    if not state_file.exists():
        return None
    state = json.loads(state_file.read_text(encoding="utf-8"))
    slots = {"spec": state["pages"]} if "pages" in state else state.get("slots", {})
    pages = slots.get(slot, [])
    return pages[0]["id"] if pages else None


async def main() -> None:
    ap = argparse.ArgumentParser(description="NaviPress: build one WordPress page with a NaviGator agent.")
    ap.add_argument("--spec", default="spec.md", help="your page specification (Markdown)")
    ap.add_argument("--skill", help="page type to build: see --list-skills")
    ap.add_argument("--model", default=os.getenv("NAVIGATOR_MODEL", "gpt-oss-120b"))
    ap.add_argument("--max-steps", type=int, default=25, help="tool calls allowed per round")
    ap.add_argument("--feedback", help="revise the draft this spec already made, using feedback from this file")
    ap.add_argument("--list-skills", action="store_true", help="show available skills and exit")
    args = ap.parse_args()

    if args.list_skills:
        for d in sorted((HERE / "skills").iterdir()):
            if (d / "SKILL.md").exists():
                desc = re.search(r"^description:\s*(.+)$", (d / "SKILL.md").read_text(encoding="utf-8"), re.M)
                print(f"  {d.name:12} {desc.group(1) if desc else ''}")
        return

    spec_path = (HERE / args.spec) if not Path(args.spec).is_absolute() else Path(args.spec)
    if not spec_path.exists():
        hint = f"skills/{args.skill}/spec_template.md" if args.skill else "a spec template"
        sys.exit(f"Can't find {spec_path.name}. Copy {hint} to {spec_path.name} and fill it in.")
    spec = spec_path.read_text(encoding="utf-8")

    system = SYSTEM_PROMPT
    # Every file in rules/ is given to the agent: design principles, voice, anything you add.
    rules_dir = HERE / "rules"
    rule_files = sorted(rules_dir.glob("*.md")) if rules_dir.exists() else [HERE / "principles.md"]
    for rf in rule_files:
        if rf.exists() and rf.name.lower() != "readme.md":
            system += f"\n\n# Site rules: {rf.stem}\n\n" + rf.read_text(encoding="utf-8")
    max_words = 1500
    if args.skill:
        skill_text, max_words = load_skill(args.skill)
        system += f"\n\n# Skill: {args.skill}\n\n{skill_text}"

    # One draft page per spec file: spec_faq.md and spec.md each get their own page.
    slot = spec_path.stem
    env = dict(os.environ, NAVIPRESS_SLOT=slot, NAVIPRESS_MAX_WORDS=str(max_words))

    llm = OpenAI(api_key=os.environ["NAVIGATOR_API_KEY"],
                 base_url=os.getenv("NAVIGATOR_BASE_URL", "https://api.navigator.ai.ufl.edu/v1"))
    log = RunLog(args.model, spec_path, args.skill)
    log.write(f"\n## Specification\n\n{spec}\n")

    server = StdioServerParameters(command=sys.executable, args=[str(HERE / "wp_mcp_server.py")], env=env)
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools = (await session.list_tools()).tools
            tools = [{"type": "function",
                      "function": {"name": t.name, "description": t.description or "",
                                   # MCP SDK 2.x says input_schema, 1.x says inputSchema
                                   "parameters": getattr(t, "input_schema", None) or t.inputSchema}}
                     for t in mcp_tools]
            print(f"NaviPress connected. Tools: {', '.join(t.name for t in mcp_tools)}")
            print(f"Model: {args.model}   Skill: {args.skill or 'none'}   Log: {log.path.relative_to(HERE)}\n")

            first = f"Here is my specification:\n\n{spec}"
            if args.feedback:
                fb_path = HERE / args.feedback if not Path(args.feedback).is_absolute() else Path(args.feedback)
                feedback_text = fb_path.read_text(encoding="utf-8").strip()
                pid = my_page_id(slot)
                if not pid:
                    sys.exit(f"No earlier draft found for {spec_path.name}. Run without --feedback first.")
                first += (f"\n\nYou already created the draft page (ID {pid}) in an earlier session. "
                          f"Do not create a new page. Read the current draft with get_page({pid}), "
                          f"then apply my feedback below with update_draft_page({pid}).\n\n"
                          f"My feedback:\n{feedback_text}")
                log.write(f"\n## Continuing draft {pid} with feedback from `{fb_path.name}`\n\n{feedback_text}\n")
            messages = [{"role": "system", "content": system}, {"role": "user", "content": first}]

            round_no = 1
            while True:
                log.write(f"\n## Round {round_no}\n")
                for _ in range(args.max_steps):
                    raw = llm.chat.completions.with_raw_response.create(
                        model=args.model, messages=messages, tools=tools, tool_choice="auto")
                    resp = raw.parse()
                    log.cost += float(raw.headers.get("x-litellm-response-cost") or 0)
                    log.tokens += resp.usage.total_tokens if resp.usage else 0
                    msg = resp.choices[0].message

                    turn = {"role": "assistant", "content": msg.content or ""}
                    if msg.tool_calls:
                        turn["tool_calls"] = [{"id": tc.id, "type": "function",
                                               "function": {"name": tc.function.name,
                                                            "arguments": tc.function.arguments or "{}"}}
                                              for tc in msg.tool_calls]
                    messages.append(turn)

                    if msg.content:
                        print(f"\nAgent: {msg.content}\n")
                        log.write(f"\n**Agent:**\n\n{msg.content}\n")
                    if not msg.tool_calls and not (msg.content or "").strip():
                        # Some reasoning models occasionally return an empty reply.
                        # Nudge once or twice instead of silently ending the round.
                        empties = getattr(log, "empties", 0) + 1
                        log.empties = empties
                        reason = resp.choices[0].finish_reason
                        log.write(f"\n_Empty reply from the model (finish_reason: {reason}); nudging it to continue._\n")
                        if empties <= 2:
                            print("  (empty reply from the model; asking it to continue)")
                            messages.pop()  # drop the empty assistant turn
                            messages.append({"role": "user", "content":
                                             "Continue the task now. Use the tools: read what you need, "
                                             "make the changes with create_draft_page or update_draft_page, "
                                             "run audit_draft, then give your final summary."})
                            continue
                    if not msg.tool_calls:
                        break

                    for tc in msg.tool_calls:
                        try:
                            tool_args = json.loads(tc.function.arguments or "{}")
                        except json.JSONDecodeError:
                            tool_args = {}
                        shown = {k: (short(v, 80) if isinstance(v, str) else v) for k, v in tool_args.items()}
                        print(f"  -> {tc.function.name}({shown})")
                        result = await session.call_tool(tc.function.name, tool_args)
                        text = "\n".join(getattr(c, "text", "") for c in result.content)
                        log.write(f"\n**Tool call:** `{tc.function.name}`\n\n```json\n"
                                  f"{short(json.dumps(tool_args, indent=2, ensure_ascii=False), 4000)}\n```\n"
                                  f"\n**Result:**\n\n```\n{short(text)}\n```\n")
                        messages.append({"role": "tool", "tool_call_id": tc.id, "content": text[:12000]})
                else:
                    print(f"Stopped after {args.max_steps} tool calls this round.")
                    log.write(f"\n_Stopped after {args.max_steps} tool calls._\n")

                feedback = input("Your feedback, one line (press Enter to finish): ").strip()
                if not feedback:
                    break
                log.write(f"\n**Me:** {feedback}\n")
                messages.append({"role": "user", "content": feedback})
                round_no += 1

            # Final audit, run by the program itself, not by the model.
            pid = my_page_id(slot)
            if pid:
                result = await session.call_tool("audit_draft", {"page_id": pid})
                audit = json.loads("\n".join(getattr(c, "text", "") for c in result.content) or "{}")
                print("\n== Design-principles audit (run by NaviPress, not the model) ==")
                for line in audit.get("passed", []):
                    print(f"  OK    {line}")
                for line in audit.get("issues", []):
                    print(f"  CHECK {line}")
                print(f"  Note: {audit.get('note', '')}")
                log.write("\n## Final audit (run by the program)\n\n"
                          + "\n".join(f"- OK: {x}" for x in audit.get("passed", []))
                          + ("\n" if audit.get("passed") else "")
                          + "\n".join(f"- CHECK: {x}" for x in audit.get("issues", [])) + "\n")

    log.finish()
    print(f"\nDone. Full record saved to {log.path.relative_to(HERE)}")
    print("The page is a DRAFT. Audit it (Module 9.2 checklist), then publish it yourself.")


if __name__ == "__main__":
    asyncio.run(main())
