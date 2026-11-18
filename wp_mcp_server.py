"""
wp_mcp_server.py - the NaviPress MCP server: the only "hands" the agent has.

The agent can:
  - read the site's name, its pages, and files in your knowledge/ folder
  - create ONE draft page per spec file, and update that draft
  - run audit_draft, which checks the draft against rules/principles.md

The agent cannot publish, delete, or touch menus, themes, or any page it
didn't create for this spec. Those limits live in this file, not in the
prompt, so the model can't talk its way past them. You publish the page
yourself after you've audited it.

You normally don't run this file directly; agent.py starts it for you.
"""

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as FastMCP
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP

HERE = Path(__file__).resolve().parent
load_dotenv(HERE / ".env")

API_ROOT = os.getenv("WP_API_ROOT", "https://public-api.wordpress.com")
BLOG = os.getenv("WP_BLOG_ID") or os.getenv("WP_SITE", "")
SITE = os.getenv("WP_SITE", "")
TOKEN = os.getenv("WP_TOKEN", "")
SLOT = os.getenv("NAVIPRESS_SLOT", "spec")        # which spec file this run is for
MAX_WORDS = int(os.getenv("NAVIPRESS_MAX_WORDS", "1500"))
STATE_FILE = HERE / "agent_pages.json"             # remembers which page each spec made
KNOWLEDGE = HERE / "knowledge"
KNOWLEDGE_TYPES = {".md", ".txt", ".html", ".htm", ".csv"}

PAGES = f"{API_ROOT}/wp/v2/sites/{BLOG}/pages"
http = requests.Session()
http.headers.update({"Authorization": f"Bearer {TOKEN}"})

mcp = FastMCP("navipress")


# ---------- helpers ----------

def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"slots": {}}
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if "pages" in state:  # older format: one page, made from spec.md
        state = {"slots": {"spec": state["pages"]}}
    return state


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _my_pages() -> list:
    return _load_state()["slots"].get(SLOT, [])


def _call(method: str, url: str, **kwargs):
    """Make an API call and turn errors into something the model can read."""
    if not TOKEN or not BLOG:
        return None, "Not signed in to WordPress yet. Run: python navipress.py login"
    try:
        r = http.request(method, url, timeout=30, **kwargs)
    except requests.RequestException as e:
        return None, f"Network error: {e}"
    if r.status_code >= 400:
        try:
            msg = r.json().get("message", r.text)
        except ValueError:
            msg = r.text
        return None, f"WordPress returned {r.status_code}: {msg[:500]}"
    return r.json(), None


def _text(field) -> str:
    """WordPress returns title/content as {raw, rendered}; prefer raw."""
    if isinstance(field, dict):
        return field.get("raw") or field.get("rendered") or ""
    return field or ""


def _edit_link(page_id: int) -> str:
    return f"https://wordpress.com/page/{BLOG}/{page_id}"


# ---------- reading ----------

@mcp.tool()
def get_site_info() -> dict:
    """Get the site's name, tagline and address. Read-only."""
    data, err = _call("GET", f"{API_ROOT}/rest/v1.1/sites/{BLOG}")
    if err:
        return {"error": err}
    return {"name": data.get("name"), "tagline": data.get("description"), "url": data.get("URL")}


@mcp.tool()
def list_pages() -> list | dict:
    """List the site's pages (id, title, slug, status, link). Read-only."""
    data, err = _call(
        "GET", PAGES,
        params={"per_page": 100, "status": "publish,draft", "context": "edit",
                "_fields": "id,title,slug,status,link"},
    )
    if err:
        return {"error": err}
    return [{"id": p["id"], "title": _text(p["title"]), "slug": p["slug"],
             "status": p["status"], "link": p["link"]} for p in data]


@mcp.tool()
def get_page(page_id: int) -> dict:
    """Read one page's full title and content (WordPress block markup). Read-only.
    Use this to study the voice, structure and facts of existing pages."""
    # Fixed limit on purpose: in testing, a model chose to read only the
    # first 2,000 characters of each page and then wrote from guesses.
    max_chars = 20000
    data, err = _call("GET", f"{PAGES}/{page_id}", params={"context": "edit"})
    if err:
        return {"error": err}
    content = _text(data.get("content"))
    return {"id": data["id"], "title": _text(data.get("title")), "status": data["status"],
            "link": data.get("link"), "content": content[:max_chars],
            "truncated": len(content) > max_chars}


@mcp.tool()
def list_sources() -> list | dict:
    """List the student's source files in the knowledge/ folder (notes, journal
    entries, exported coursework). Build only from these and the site's pages."""
    if not KNOWLEDGE.exists():
        return {"note": "There is no knowledge/ folder. Use the site's pages only."}
    files = [p for p in sorted(KNOWLEDGE.rglob("*"))
             if p.is_file() and p.suffix.lower() in KNOWLEDGE_TYPES and p.name.lower() != "readme.md"]
    return [{"name": str(p.relative_to(KNOWLEDGE)).replace("\\", "/"),
             "characters": p.stat().st_size} for p in files] or {"note": "knowledge/ is empty."}


@mcp.tool()
def read_source(name: str) -> dict:
    """Read one file from the knowledge/ folder, by the name list_sources gives."""
    path = (KNOWLEDGE / name).resolve()
    if KNOWLEDGE.resolve() not in path.parents or not path.is_file():
        return {"error": f"No source called {name!r}. Use list_sources to see what's there."}
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() in {".html", ".htm"}:
        text = re.sub(r"<[^>]+>", " ", text)
    return {"name": name, "content": text[:30000], "truncated": len(text) > 30000}


# ---------- writing (one draft per spec file) ----------

@mcp.tool()
def create_draft_page(title: str, content: str) -> dict:
    """Create the ONE draft page you are building. Content must be WordPress
    block markup. The page is saved as a draft and is not public.
    You can only create one page; after that, use update_draft_page."""
    state = _load_state()
    mine = state["slots"].get(SLOT, [])
    if mine:
        pid = mine[0]["id"]
        return {"error": f"You already created page {pid}. Use update_draft_page(page_id={pid}, ...) instead."}
    data, err = _call("POST", PAGES, json={"title": title, "content": content, "status": "draft"})
    if err:
        return {"error": err}
    state["slots"][SLOT] = [{"id": data["id"], "title": title}]
    _save_state(state)
    return {"ok": True, "page_id": data["id"], "status": data["status"],
            "edit_in_wordpress": _edit_link(data["id"]),
            "next": "Run audit_draft on this page before you finish."}


@mcp.tool()
def update_draft_page(page_id: int, title: str | None = None, content: str | None = None) -> dict:
    """Replace the title and/or full content of the draft page YOU created.
    Content replaces the whole page, so send the complete page every time.
    The page stays a draft."""
    if page_id not in {p["id"] for p in _my_pages()}:
        return {"error": f"Page {page_id} was not created by this agent for this spec, so it can't be edited."}
    current, err = _call("GET", f"{PAGES}/{page_id}", params={"context": "edit", "_fields": "status"})
    if err:
        return {"error": err}
    if current.get("status") != "draft":
        return {"error": "That page is no longer a draft (someone published or trashed it), so the agent stops here."}
    body = {"status": "draft"}
    if title is not None:
        body["title"] = title
    if content is not None:
        body["content"] = content
    data, err = _call("POST", f"{PAGES}/{page_id}", json=body)
    if err:
        return {"error": err}
    return {"ok": True, "page_id": data["id"], "status": data["status"],
            "edit_in_wordpress": _edit_link(data["id"])}


# ---------- audit: rules/principles.md, checked in code ----------

class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.headings, self.images, self.links, self.paragraphs = [], [], [], []
        self._in_p, self._p, self._heading = False, [], None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if re.fullmatch(r"h[1-6]", tag):
            self._heading = [int(tag[1]), ""]
        elif tag == "img":
            self.images.append(a.get("alt"))
        elif tag == "a" and a.get("href"):
            self.links.append(a["href"])
        elif tag == "p":
            self._in_p, self._p = True, []

    def handle_endtag(self, tag):
        if self._heading and tag == f"h{self._heading[0]}":
            self.headings.append((self._heading[0], self._heading[1].strip()))
            self._heading = None
        elif tag == "p" and self._in_p:
            self.paragraphs.append("".join(self._p))
            self._in_p = False

    def handle_data(self, data):
        if self._heading:
            self._heading[1] += data
        if self._in_p:
            self._p.append(data)


GENERIC_ALT = {"image", "photo", "picture", "flyer", "graphic", "logo", "screenshot", "event flyer", "img"}


def audit_content(content: str, site_slugs: set, site_host: str, max_words: int = MAX_WORDS) -> dict:
    """Check block markup against rules/principles.md. Pure function, easy to test."""
    scan = _Scan()
    scan.feed(content)
    text = re.sub(r"<[^>]+>|<!--.*?-->", " ", content, flags=re.S)
    words = len(text.split())
    issues, passed = [], []

    # 1. Every fact in text: images need real alt text
    bad_alt = [a for a in scan.images if not a or a.strip().lower() in GENERIC_ALT]
    if bad_alt:
        issues.append(f"Principle 1: {len(bad_alt)} image(s) have missing or generic alt text.")
    else:
        passed.append(f"Alt text: {len(scan.images)} image(s), all described.")

    # 3. Real structure
    levels = [h[0] for h in scan.headings]
    if 1 in levels:
        issues.append("Principle 3: the page uses an H1; the title is already the H1.")
    for prev, cur in zip([2] + levels, levels):
        if cur > prev + 1:
            issues.append(f"Principle 3: heading jumps from H{prev} to H{cur}.")
            break
    empty = [h for h in scan.headings if not h[1]]
    if empty:
        issues.append(f"Principle 3: {len(empty)} empty heading(s).")
    if not any(i.startswith("Principle 3") for i in issues):
        passed.append(f"Headings: {len(scan.headings)}, in order.")

    # 4. Short paragraphs
    long_ps = [p for p in scan.paragraphs if len(p.split()) > 80]
    if long_ps:
        issues.append(f"Principle 4: {len(long_ps)} paragraph(s) over 80 words, starting: "
                      f"\"{' '.join(long_ps[0].split()[:8])}...\"")
    else:
        passed.append("Paragraphs: all under 80 words.")

    # 5. No invented facts: open [CHECK] markers are listed for the student
    checks = re.findall(r"\[CHECK:?([^\]]*)\]", text)
    if checks:
        issues.append(f"Principle 5: {len(checks)} [CHECK] item(s) for the student to verify: "
                      + "; ".join(c.strip() for c in checks[:5]))

    # 7. Link inside the site; and internal links must point to real pages
    external, broken = [], []
    for href in scan.links:
        u = urlparse(href)
        if u.scheme in ("http", "https") and u.netloc and site_host and u.netloc != site_host:
            external.append(href)
        elif not u.scheme or u.netloc == site_host:
            slug = u.path.strip("/").split("/")[-1] if u.path.strip("/") else ""
            if slug and site_slugs and slug not in site_slugs:
                broken.append(href)
    if external:
        issues.append(f"Principle 7: {len(external)} link(s) to other websites: {', '.join(external[:3])}")
    if broken:
        issues.append(f"Broken internal link(s), no page with that address: {', '.join(broken[:5])}")
    if not external and not broken:
        passed.append(f"Links: {len(scan.links)}, all to real pages on this site.")

    # Blocks and length
    if "<!-- wp:" not in content:
        issues.append("Format: no WordPress block markup; the editor will show one big Classic block.")
    if words > max_words:
        issues.append(f"Length: about {words} words, over the {max_words}-word limit.")
    else:
        passed.append(f"Length: about {words} words (limit {max_words}).")

    return {"issues": issues, "passed": passed, "words": words}


@mcp.tool()
def audit_draft(page_id: int) -> dict:
    """Check your draft against the site's design principles (alt text, heading
    order, paragraph length, [CHECK] markers, links, length). Run this before
    you finish and fix every issue you can."""
    data, err = _call("GET", f"{PAGES}/{page_id}", params={"context": "edit"})
    if err:
        return {"error": err}
    pages, _ = _call("GET", PAGES, params={"per_page": 100, "status": "publish,draft", "_fields": "slug"})
    slugs = {p["slug"] for p in (pages or [])}
    host = urlparse(data.get("link", "")).netloc or SITE
    result = audit_content(_text(data.get("content")), slugs, host)
    result["page_id"] = page_id
    result["note"] = ("This checks structure only. Accuracy, voice and image rights still need "
                      "a human (Module 9.2 audit).")
    return result


if __name__ == "__main__":
    mcp.run()  # speaks MCP over stdin/stdout
