# NaviPress

**Build your WordPress site with AI agents running on UF NaviGator, and
learn to check their work.**

An [Agentic Web Observatory](https://agenticwebobservatory.wordpress.com)
project by Ethan Pecora · MMC3260 Trends in Media Technology · Fall 2026 ·
Module 9: AI Agents and the Build

> The Agentic Web Observatory found that AI readers miss facts that live in
> images, trust outdated text, and invent answers when a page doesn't reach
> them. NaviPress is the other side of that research: a workspace where an
> agent **builds** pages following those same rules, using models UF already
> gives students through NaviGator, on a **free** WordPress.com site.

**Trying it in class?** Start with [`TRY_IN_CLASS.md`](TRY_IN_CLASS.md):
three short levels, Mac first. **Want the story first?**
[`examples/README.md`](examples/README.md) shows a real run, mistakes included.

---

## The workspace

```
navipress/
├── navipress.py        ← every command starts here
├── knowledge/
│   ├── project/        ← YOUR research: topic.md, sources/, journal/, notes/
│   └── site/           ← your current site, pulled automatically
├── rules/              ← what "good" means: principles.md (written), voice.md (yours)
├── skills/             ← page types: faq, glossary, page
├── specs/              ← one spec per page you build
├── examples/           ← the demo: real specs, real mistakes
└── (engine)            agent.py · wp_mcp_server.py · wp_auth.py · check_setup.py
```

## Which commands call the AI?

| Command | AI? | What it does | Cost |
|---|---|---|---|
| `check` | no | Tests your NaviGator key and WordPress sign-in | free |
| `login` | no | One-time WordPress sign-in (you click Approve) | free |
| `pull-site` | **no** | Copies your published pages into `knowledge/site/` as text | free |
| `audit-site` | **no** | Checks every page against `rules/principles.md` | free |
| `plan` | **yes**, one call | Reads `knowledge/project/` and proposes a site map plus draft specs | ~1¢ |
| `build` | **yes**, agent | Builds ONE draft page from a spec, using tools | a few ¢ |
| `revise` | **yes**, agent | Revises the draft a spec already made | a few ¢ |

"No AI" commands are ordinary programs: same input, same output, every
time. Knowing which is which is half of using AI well: the audit is only
trustworthy *because* it isn't AI.

---

## Step 0. Back up your site
WordPress.com → your site → **Tools → Export → Export all**. Do this first.

## Step 1. Set up (one time, ~20 minutes)

**1a. Python 3.10+** from https://www.python.org/downloads/. Mac: the
built-in `python3` is 3.9, too old, so install from python.org even if
`python3` already works. Windows: tick **"Add python.exe to PATH"**.

**1b. Install.** Download this repository (green **Code** button →
**Download ZIP**, then unzip), open a terminal in the folder, and run:
- **Mac:** in Terminal type `cd ` (with a space), drag the folder in, press
  Return, then `bash setup.sh`
- **Windows:** right-click the folder → Open in Terminal →
  `powershell -ExecutionPolicy Bypass -File setup.ps1`

On a Mac, `.env` is hidden in Finder; reopen it any time with `open -e .env`
(Windows: `notepad .env`).

It creates `.venv`, installs four packages, creates `.env` and opens it.

**1c. NaviGator key.** https://api.navigator.ai.ufl.edu/ui/api-keys →
**+ Create New Key** → Team `navigator-toolkit`, a name, Models
`nemotron-3-super-120b-a12b` (and `gpt-oss-120b`), a small Max Budget
(e.g. 5) and an expiry like `28d`. Copy the key into `.env`. It's shown once.

**1d. WordPress.com app.** https://developer.wordpress.com/apps/new/ →
Redirect URL `http://localhost:8765/callback`, Type **Web**. Copy the
Client ID and Client Secret into `.env`, and your site address into
`WP_SITE`.

**1e. Activate, sign in, check.** Every new terminal, activate first
(Mac `source .venv/bin/activate`, Windows `.\.venv\Scripts\Activate.ps1`),
then, **one command at a time**:
```
python navipress.py login
python navipress.py check
```

**Never share `.env`.** It holds your key and your site's access token.

## Step 2. Build your knowledge base
1. Fill in **`knowledge/project/topic.md`**: topic, research question,
   audience, main finding, key facts with sources, key terms.
2. Add your material to `knowledge/project/sources/`, `journal/` and
   `notes/`: citations, journal entries, slide text, exported Canvas
   work. Your own work only.
3. If you already have a site: `python navipress.py pull-site`. Open
   `knowledge/site/_index.md` to see your site the way the agent will.
4. Fill in **`rules/voice.md`**.

## Step 3. Audit what you have (free)
```
python navipress.py audit-site
```
A report in `reports/` lists, page by page, missing alt text, skipped
headings, long paragraphs, broken internal links and open `[CHECK]`
items. Fix these by hand; they count toward your grade either way.

## Step 4. Plan (optional, one AI call)
```
python navipress.py plan
```
Writes `plans/site-plan-<date>.md` (a site map, which pages to build with
which skill, and **gaps** in your knowledge) plus DRAFT specs in `specs/`.
The plan marks the page carrying your main argument as yours to write.
Every `[STUDENT: ...]` in a draft spec is something only you can answer.

**For Module 9.2, write your spec yourself** (or rewrite the draft
heavily) and record in your journal how much you wrote.

## Step 5. Build one page
```
python navipress.py skills
python navipress.py build --skill faq --spec specs/faq.md
```
Watch the tool calls: which pages and files did it actually open? When it
stops, open the draft link, then type feedback **on one line** or press
Enter to finish. The design audit then runs automatically, in code.

Ended too soon? Put feedback in a file and run
`python navipress.py revise --skill faq --spec specs/faq.md --feedback fix.md`.

The agent **cannot** publish, delete, edit other pages, touch menus or
themes, or read files outside `knowledge/`. Those limits are in code.

## Step 6. Check it like an editor, then publish
- [ ] Compare the tool calls in `runs/` with what the agent *says* it read
- [ ] Search the draft for `[CHECK` and verify each one
- [ ] Check every fact against `knowledge/` or your pages, especially
      numbers and citations (agents drop citations when revising)
- [ ] Headings, alt text, links (the audit helps), and voice
- [ ] Project checklist on Canvas 100.8.6

Then publish it yourself and add it to your menu.

## Step 7. Journal
`runs/` has the spec, every tool call, the audit, time and cost. Add what
the log can't hold: what was wrong, how you noticed, what it decided that
you never asked for, and your real time against your estimate.

---

## Add a skill
Copy `skills/page` to `skills/<name>`, edit `SKILL.md` (how to build it,
a block template, an audit list) and `spec_template.md`. Ideas: timeline,
resources, people, event page (with your research's deal-breakers rule).

## Troubleshooting

| Problem | Fix |
|---|---|
| `can't open file` | You're not in the workspace folder; `cd` into it |
| `KeyboardInterrupt` during setup | You pasted several commands at once; run one at a time |
| NaviGator dashboard: "Invalid duration format" when editing a key | Fill in **Expire Key** (e.g. `27d`) before saving |
| `invalid_client: Unknown client_id` after Approve | The Client Secret in `.env` doesn't match the app; copy it again (don't reset it) |
| Browser doesn't return after Approve | `python navipress.py login --manual` |
| "(empty reply from the model)" | Normal for reasoning models; NaviPress retries automatically |
| Model answers without calling tools | Use `--model nemotron-3-super-120b-a12b` |
| `401` from NaviGator | Key mistyped, expired, or over budget |

## Other ways to connect AI to WordPress
- **WordPress's built-in AI** (Canvas Module 5.9): easiest, no setup.
- **WordPress.com's official connector** for Claude or ChatGPT: works on
  paid plans, and should work on the free **Student Plan** your instructor can
  request at wp.com/edu (check before relying on it); on free sites only
  through November 30, 2026. Choose **Read only** first.
- **NaviPress**: uses the ordinary WordPress.com API, so it should keep working on free sites after November 30; runs on UF's
  models, and lets you see and change every part of the agent.

## About the packages
`openai` (the client NaviGator speaks), `mcp` (the official Model Context
Protocol SDK), `requests`, `python-dotenv`. Module 9.3 explains why you
check any package an AI tells you to install. Look these four up on
pypi.org yourself.
