# knowledge/

The agent builds only from what's in here and on your site. If a fact
isn't in the knowledge base, the agent is told to write `[CHECK: ...]`
instead of guessing. The lesson from Module 9 and from the Agentic Web
Observatory: **the agent can only use what reaches it.**

There are two areas, and they work differently.

## project/: your research (you write it)
Everything about your topic that isn't on your site yet: your research
question, sources, notes, journal entries, slide text, interview notes,
exported Canvas submissions. Start with `project/topic.md`, the most
important file in the workspace.

- Plain text or Markdown (`.md`, `.txt`, `.csv`). Copy-paste is fine.
  For slides, export or copy the text.
- Use **your own** work. Don't add other students' work, grades, IDs or
  anyone's personal information.
- Organize it into the subfolders: `sources/`, `journal/`, `notes/`.
  Sorting it is part of the work: a messy folder gives a messy site.

## site/: your current site (the computer writes it)
Run `python navipress.py pull-site`. It copies every published page into
this folder as readable text, plus `_index.md`: an overview with word
counts, outlines, and images missing alt text. It's plain code, with no
AI, so it's exact. Don't edit these files; pull again after you change the
site.

## Why two areas?
`site/` is what you've **already said** publicly; `project/` is what you
**know**. Keeping them apart lets the agent match your existing voice
(site) without mistaking an old draft for a source (project), and lets
`plan` see what your site is missing.
