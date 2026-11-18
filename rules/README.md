# rules/

Everything in this folder is given to the agent on every run. It's how you
tell the agent what "good" means for *your* site.

| File | What it is | Who writes it |
|---|---|---|
| `principles.md` | Design rules from the Agentic Web Observatory research: every fact in text, deal-breakers up front, real headings, short paragraphs, no invented facts. The `audit` commands check these in code. | Already written; edit if your site needs different rules |
| `voice.md` | How your site sounds: audience, tone, person, words to use and avoid. | **You** |

Add more files if you need them, for example `citations.md` ("cite as
Author, Year") or `accessibility.md`. A rule only gets *checked* if it's
also in the audit code (`audit_content` in `wp_mcp_server.py`); otherwise
it's guidance the model may or may not follow. That difference is one of
the lessons of this project.
