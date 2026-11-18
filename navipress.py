"""
navipress.py - one entry point for the NaviPress workspace.

  python navipress.py check        is everything connected?            (code)
  python navipress.py login        one-time WordPress sign-in          (code)
  python navipress.py pull-site    copy your published pages into
                                   knowledge/site/ as readable text    (code, no AI)
  python navipress.py audit-site   check every page against rules/     (code, no AI)
  python navipress.py plan         propose a site map + draft specs
                                   from knowledge/project/             (AI: one NaviGator call)
  python navipress.py build  --skill faq --spec specs/faq.md           (AI: the agent)
  python navipress.py revise --spec specs/faq.md --feedback fix.md     (AI: the agent)

"(code)" commands are ordinary programs: same input, same output, free.
"(AI)" commands send text to a UF NaviGator model and cost a few cents.
"""

import json
import os
import re
import subprocess
import sys
from datetime import date, datetime
from html import unescape
from pathlib import Path

HERE = Path(__file__).resolve().parent
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def env():
    from dotenv import load_dotenv
    load_dotenv(HERE / ".env")
    return os.environ


# ---------------------------------------------------------------- WordPress (read-only)

def wp_get(path: str, params: dict | None = None):
    import requests
    e = env()
    blog, token = e.get("WP_BLOG_ID") or e.get("WP_SITE"), e.get("WP_TOKEN")
    if not (blog and token):
        sys.exit("Not signed in to WordPress yet. Run: python navipress.py login")
    root = e.get("WP_API_ROOT", "https://public-api.wordpress.com")
    r = requests.get(f"{root}/wp/v2/sites/{blog}/{path}", params=params or {},
                     headers={"Authorization": f"Bearer {token}"}, timeout=30)
    if r.status_code >= 400:
        sys.exit(f"WordPress returned {r.status_code}: {r.text[:300]}")
    return r.json()


def published_pages() -> list[dict]:
    pages = wp_get("pages", {"per_page": 100, "status": "publish", "context": "edit",
                             "_fields": "id,slug,title,link,modified,content,menu_order"})
    for p in pages:
        p["title"] = p["title"].get("raw") or p["title"].get("rendered", "")
        p["html"] = p["content"].get("rendered") or p["content"].get("raw", "")
        p["blocks"] = p["content"].get("raw") or p["html"]
    return pages


def html_to_text(html: str) -> str:
    """Turn page HTML into readable Markdown-ish text. Deterministic, no AI."""
    s = re.sub(r"<!--.*?-->", "", html, flags=re.S)
    s = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", s, flags=re.S | re.I)
    for n in range(1, 7):
        s = re.sub(rf"<h{n}[^>]*>(.*?)</h{n}>", lambda m, n=n: f"\n\n{'#' * n} {m.group(1)}\n\n", s, flags=re.S | re.I)
    s = re.sub(r'<img[^>]*?alt="([^"]*)"[^>]*>',
               lambda m: f"\n[Image: {m.group(1).strip() or 'NO ALT TEXT'}]\n", s, flags=re.I)
    s = re.sub(r"<img[^>]*>", "\n[Image: NO ALT TEXT]\n", s, flags=re.I)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>(.*?)</a>', r"[\2](\1)", s, flags=re.S | re.I)
    s = re.sub(r"<li[^>]*>", "\n- ", s, flags=re.I)
    s = re.sub(r"<(td|th)[^>]*>", " | ", s, flags=re.I)
    s = re.sub(r"</(p|div|tr|ul|ol|table|figure|figcaption|blockquote|summary|details)>", "\n\n", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = unescape(s).replace(" ", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n\s*\n\s*\n+", "\n\n", s)
    return s.strip()


def cmd_pull_site(_args):
    """Copy every published page into knowledge/site/ as text, plus an index."""
    out = HERE / "knowledge" / "site"
    out.mkdir(parents=True, exist_ok=True)
    pages = sorted(published_pages(), key=lambda p: (p.get("menu_order", 0), p["title"]))
    rows = []
    for p in pages:
        text = html_to_text(p["html"])
        words = len(text.split())
        headings = re.findall(r"^#{2,3} (.+)$", text, re.M)
        images = text.count("[Image:")
        no_alt = text.count("[Image: NO ALT TEXT]")
        (out / f"{p['slug']}.md").write_text(
            f"---\npage_id: {p['id']}\ntitle: {p['title']}\nurl: {p['link']}\n"
            f"modified: {p['modified']}\nwords: {words}\n---\n\n# {p['title']}\n\n{text}\n",
            encoding="utf-8")
        rows.append((p, words, headings, images, no_alt))
    index = [f"# Site snapshot\n\nPulled {datetime.now():%Y-%m-%d %H:%M} by `navipress.py pull-site` "
             f"(plain code, no AI). Don't edit these files; pull again instead.\n",
             "| Page | ID | Words | Images (no alt) | File |", "|---|---|---|---|---|"]
    for p, words, _, images, no_alt in rows:
        index.append(f"| {p['title']} | {p['id']} | {words} | {images} ({no_alt}) | {p['slug']}.md |")
    index.append("\n## Outline\n")
    for p, _, headings, _, _ in rows:
        index.append(f"- **{p['title']}** ({p['link']})")
        index += [f"  - {h}" for h in headings[:12]]
    (out / "_index.md").write_text("\n".join(index) + "\n", encoding="utf-8")
    print(f"Pulled {len(rows)} published pages into knowledge/site/. Overview: knowledge/site/_index.md")


def cmd_audit_site(_args):
    """Run the design-principles audit on every published page. Read-only."""
    os.environ.setdefault("WP_TOKEN", env().get("WP_TOKEN", ""))
    from urllib.parse import urlparse
    sys.path.insert(0, str(HERE))
    from wp_mcp_server import audit_content  # same checks the agent uses
    pages = published_pages()
    slugs = {p["slug"] for p in pages}
    (HERE / "reports").mkdir(exist_ok=True)
    report = HERE / "reports" / f"site-audit-{date.today()}.md"
    lines = [f"# Site audit, {date.today()}\n",
             "Plain code, no AI: checks structure against rules/principles.md. "
             "Accuracy, voice and image rights still need a person.\n",
             "| Page | Words | Issues |", "|---|---|---|"]
    detail, total = [], 0
    for p in sorted(pages, key=lambda p: p["title"]):
        host = urlparse(p["link"]).netloc
        r = audit_content(p["blocks"], slugs, host, max_words=100000)
        issues = [i for i in r["issues"] if not i.startswith("Length")]
        total += len(issues)
        lines.append(f"| [{p['title']}]({p['link']}) | {r['words']} | {len(issues) or 'none'} |")
        if issues:
            detail.append(f"\n## {p['title']}\n" + "\n".join(f"- {i}" for i in issues))
    report.write_text("\n".join(lines + detail) + "\n", encoding="utf-8")
    print(f"Audited {len(pages)} pages: {total} issue(s). Report: {report.relative_to(HERE)}")
    for d in detail:
        print(d)


# ---------------------------------------------------------------- planning (one AI call)

PLAN_PROMPT = """You are helping a student plan a WordPress website about their own semester project.
You will get: the student's project knowledge (topic, research, journal, notes), optionally a snapshot of
their current site, the site's design rules, and the page skills NaviPress can build.

Write a site plan in Markdown with these sections:
1. "## Site map": a table of 5 to 8 pages (Page, Purpose, Skill to use: faq, glossary, page, or "write by hand").
   Mark which page carries the central argument and should be written by the student, not an agent.
2. "## Gaps": what the knowledge folder does not yet contain that the site will need.
3. One section per agent-buildable page, titled "## Spec: <slug>", containing a DRAFT spec that follows
   the matching template below, filled in ONLY from the student's knowledge. Where the knowledge doesn't
   say, write "[STUDENT: ...]" instead of inventing.
Use only the knowledge given. Do not invent facts, sources, statistics or quotes."""


def read_tree(folder: Path, limit: int) -> str:
    parts, used = [], 0
    for f in sorted(folder.rglob("*")):
        if f.is_file() and f.suffix.lower() in {".md", ".txt", ".csv"} and f.name.lower() != "readme.md":
            t = f.read_text(encoding="utf-8", errors="replace")
            if "[One sentence.]" in t and "[The question your project answers.]" in t:
                continue  # topic.md template not filled in yet
            chunk = f"\n\n=== {f.relative_to(HERE)} ===\n{t}"
            if used + len(chunk) > limit:
                parts.append(f"\n\n=== {f.relative_to(HERE)} === [skipped: knowledge limit reached]")
                continue
            parts.append(chunk)
            used += len(chunk)
    return "".join(parts)


def cmd_plan(args):
    from openai import OpenAI
    e = env()
    project = read_tree(HERE / "knowledge" / "project", 60000)
    if not project.strip():
        sys.exit("knowledge/project/ is empty. Fill in topic.md (and add notes) first; see knowledge/README.md.")
    site_index = HERE / "knowledge" / "site" / "_index.md"
    site = site_index.read_text(encoding="utf-8") if site_index.exists() else "(No site snapshot. Run pull-site if you have a site.)"
    rules = "\n\n".join(f.read_text(encoding="utf-8") for f in sorted((HERE / "rules").glob("*.md")))
    templates = "\n\n".join(f"### Template for skill '{d.name}'\n" + (d / "spec_template.md").read_text(encoding="utf-8")
                            for d in sorted((HERE / "skills").iterdir()) if (d / "spec_template.md").exists())
    model = args.model or e.get("NAVIGATOR_MODEL", "gpt-oss-120b")
    llm = OpenAI(api_key=e["NAVIGATOR_API_KEY"], base_url=e.get("NAVIGATOR_BASE_URL", "https://api.navigator.ai.ufl.edu/v1"))
    print(f"Planning with {model} (one NaviGator call)...")
    resp = llm.chat.completions.create(model=model, messages=[
        {"role": "system", "content": PLAN_PROMPT},
        {"role": "user", "content": f"# Project knowledge\n{project}\n\n# Current site\n{site}\n\n"
                                    f"# Design rules\n{rules}\n\n# Spec templates\n{templates}"}])
    plan = resp.choices[0].message.content or ""
    if not plan.strip():
        sys.exit("The model returned an empty plan. Run the command again.")
    (HERE / "plans").mkdir(exist_ok=True)
    out = HERE / "plans" / f"site-plan-{datetime.now():%Y-%m-%d_%H%M}.md"
    out.write_text(f"# Site plan (DRAFT from {model}; edit before using)\n\n{plan}\n", encoding="utf-8")
    made = []
    for slug, body in re.findall(r"^## Spec: *([\w-]+)\s*\n(.*?)(?=^## |\Z)", plan, re.M | re.S):
        spec = HERE / "specs" / f"{slug}.md"
        if spec.exists():
            continue  # never overwrite a spec the student may have edited
        spec.write_text(f"<!-- DRAFT written by {model} from your knowledge folder. "
                        f"Edit it; replace every [STUDENT: ...] before building. -->\n\n{body.strip()}\n", encoding="utf-8")
        made.append(spec.relative_to(HERE))
    print(f"Plan saved: {out.relative_to(HERE)}")
    print("Draft specs: " + (", ".join(map(str, made)) if made else "none new (existing specs are never overwritten)"))
    print("Next: read the plan, fix the specs, then build ONE page:  python navipress.py build --skill <skill> --spec specs/<page>.md")


# ---------------------------------------------------------------- the agent

def run_agent(extra: list[str]):
    sys.exit(subprocess.call([sys.executable, str(HERE / "agent.py"), *extra]))


def main():
    import argparse
    ap = argparse.ArgumentParser(prog="navipress", description="NaviPress workspace commands.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("check", help="test your NaviGator key and WordPress sign-in")
    lg = sub.add_parser("login", help="one-time WordPress sign-in")
    lg.add_argument("--manual", action="store_true", help="paste the address instead of using the local callback")
    sub.add_parser("pull-site", help="copy published pages into knowledge/site/ (no AI)")
    sub.add_parser("audit-site", help="audit every published page against rules/ (no AI)")
    p = sub.add_parser("plan", help="propose a site map and draft specs (one AI call)")
    p.add_argument("--model")
    b = sub.add_parser("build", help="build one draft page with the agent")
    b.add_argument("--skill", required=True)
    b.add_argument("--spec", required=True)
    b.add_argument("--model")
    r = sub.add_parser("revise", help="revise the draft a spec already made")
    r.add_argument("--spec", required=True)
    r.add_argument("--feedback", required=True)
    r.add_argument("--skill")
    r.add_argument("--model")
    sub.add_parser("skills", help="list page skills")
    args = ap.parse_args()

    if args.cmd == "check":
        sys.exit(subprocess.call([sys.executable, str(HERE / "check_setup.py")]))
    if args.cmd == "login":
        sys.exit(subprocess.call([sys.executable, str(HERE / "wp_auth.py"), *(["--manual"] if args.manual else [])]))
    if args.cmd == "pull-site":
        return cmd_pull_site(args)
    if args.cmd == "audit-site":
        return cmd_audit_site(args)
    if args.cmd == "plan":
        return cmd_plan(args)
    if args.cmd == "skills":
        run_agent(["--list-skills"])
    extra = ["--spec", args.spec]
    if getattr(args, "skill", None):
        extra += ["--skill", args.skill]
    if getattr(args, "model", None):
        extra += ["--model", args.model]
    if args.cmd == "revise":
        extra += ["--feedback", args.feedback]
    run_agent(extra)


if __name__ == "__main__":
    main()
