# Try NaviPress in class

Three levels. Stop wherever class time runs out; each level works on its
own. Written for **Mac** first (Windows notes in *italics*).

You need: a laptop, your GatorLink, and Python 3.10 or newer.

---

## Level 1: Your first AI plan (about 15 minutes)

You'll get a NaviGator key and have a UF model propose a site plan from
your own project. No WordPress setup needed yet.

**1. Check Python.** Open **Terminal** (Cmd+Space, type Terminal) and run:
```
python3 --version
```
If it says 3.9 or lower, or "command not found", install Python from
https://www.python.org/downloads/ (the macOS installer), close Terminal,
and open a new one. The Python that comes with macOS is too old.
*Windows: run `py --version`; when installing, tick "Add python.exe to PATH".*

**2. Download NaviPress.** https://github.com/EwillieP99/navipress →
green **Code** button → **Download ZIP**. Double-click the ZIP in
Downloads to unzip it.

**3. Install.** In Terminal, type `cd ` (with a space), drag the unzipped
`navipress-main` folder into the window, press Return, then run:
```
bash setup.sh
```
It installs everything and opens a file called `.env` in TextEdit.
*Windows: right-click the folder → Open in Terminal →
`powershell -ExecutionPolicy Bypass -File setup.ps1`.*

**4. Get a NaviGator key.** Go to https://api.navigator.ai.ufl.edu/ui/api-keys
→ **+ Create New Key**:
- Team: `navigator-toolkit` · Key Name: anything
- Models: `nemotron-3-super-120b-a12b`
- Optional Settings: Max Budget `2`, Expire Key `14d`
- **Create Key**, then copy the key. It's shown only once.

Paste it after `NAVIGATOR_API_KEY=` in `.env` and save. Never share it.

**5. Describe your project.** Open `knowledge/project/topic.md` and fill in
at least Topic, Research question, Audience and three Key facts with sources.
Five minutes is plenty; rough is fine.

**6. Ask for a plan.** Back in Terminal, run these one at a time:
```
source .venv/bin/activate
python navipress.py plan
```
*Windows: `.\.venv\Scripts\Activate.ps1` instead of `source ...`.*

Open the newest file in `plans/`. You'll see a proposed site map, **gaps**
in your knowledge, and draft page specs in `specs/`.

**Discuss:** What did it suggest that you'd never have thought of? What did
it get wrong about your project? Every `[STUDENT: ...]` marks something it
didn't know. Did it invent anything instead?

---

## Level 2: Connect your site and audit it (about 15 minutes)

**7. Register a WordPress app.** https://developer.wordpress.com/apps/new/
- Name and description: anything · Website URL: your site
- Redirect URL: `http://localhost:8765/callback` · Type: **Web**
- Answer the math question → **Create**

Reopen `.env` (Finder hides files that start with a dot, so use Terminal):
```
open -e .env
```
*Windows: `notepad .env`.* Paste the **Client ID** and **Client Secret**, and
your site address (e.g. `mysite.wordpress.com`) after `WP_SITE=`. Save.
Don't click Reset Key on the app page afterwards.

**8. Sign in and check:**
```
python navipress.py login
python navipress.py check
```
Your browser opens; pick your site and click **Approve**.

**9. Copy your site and audit it.** No AI is used, and it costs nothing:
```
python navipress.py pull-site
python navipress.py audit-site
```
Open `knowledge/site/_index.md` (your site as the agent sees it) and the
report in `reports/`: missing alt text, skipped headings, broken links.
Those are real fixes for your project website.

---

## Level 3: Let the agent build one page (homework, Module 9.2)

Back up your site first (WordPress.com → Tools → Export).
Pick one of the specs from Level 1 (or write your own), fix every
`[STUDENT: ...]`, then:
```
python navipress.py build --skill faq --spec specs/faq.md
```
Watch which pages it actually opens. It only makes a **draft**. Before you
publish, compare every fact with your sources. See `examples/README.md`
for what went wrong in the demo and how it was caught.

---

## If something goes wrong

| What you see | Do this |
|---|---|
| `command not found: python` | On Mac use `python3` before activating; after `source .venv/bin/activate`, `python` works |
| Can't find `.env` in Finder | It's hidden; run `open -e .env` in Terminal |
| `No such file or directory` | You're not in the navipress folder. `cd ` and drag the folder in again |
| Setup stops partway | Run commands one at a time; don't paste several at once |
| NaviGator: "Invalid duration format" | Fill in **Expire Key** (e.g. `14d`) before saving |
| `401` from NaviGator | Key pasted wrong in `.env` (no spaces, no quotes) |
| `Unknown client_id` after Approve | Copy the Client Secret again from your app page |
| Browser doesn't come back after Approve | `python navipress.py login --manual` |
| "(empty reply from the model)" | Normal; it retries automatically |
