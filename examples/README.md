# Examples: the demo, step by step

These files are from the night NaviPress was built (November 17, 2026),
working on the [Agentic Web Observatory](https://agenticwebobservatory.wordpress.com).
They're real, mistakes included. The mistakes are the point.

## 1. Glossary (`glossary-spec.md`)
- **Who wrote the spec:** Ethan wrote the title and audience; the rest was
  drafted with Claude from the site's own pages. (Module 9.2 asks you to
  notice this kind of thing, so it's recorded.)
- **Round 1, gpt-oss-120b:** the spec said to read 8 pages. The agent read
  3, and only the first 2,000 characters of each, then reported that
  "all statements are taken directly from the listed site pages." It
  dropped every author citation and pointed three "On this site" links at
  the wrong pages. Its list of "decisions you didn't ask for" just
  restated the spec.
- **Fix in the tool, not the prompt:** `get_page` now always returns the
  whole page.
- **Round 2** (`glossary-feedback-round2.md`): it fixed exactly the five
  things named, and nothing else.

## 2. FAQ: two NaviGator models, one spec (`faq-spec.md`)

| | gpt-oss-120b | Nemotron 3 Super 120B |
|---|---|---|
| Opened every page it said it read | No: claimed one it never opened | Yes, all 8 |
| "One model placed the event at Columbia University" | Wrong ("two models") | Correct |
| Kept the "drafted by an agent" disclosure | No | Yes |
| Kept author citations | No | No |
| Used `audit_draft` to fix its own broken link | No | Yes |
| Rounds needed | 2, plus 4 hand fixes | 1 |

The automatic audit passed the gpt-oss draft **while it still contained
the Columbia error.** Code can check structure; it can't check truth.

## 3. A second AI's review
Jetpack AI reviewed the Nemotron FAQ and suggested a date note, scope
limits, and a sources link (good), but missed the dropped citations, the
one real accuracy problem, because it never compared the page with the
sources. `faq-feedback-after-review.md` is the fix list that came out of
sorting its advice.

## The lessons, short
1. The agent can only use what reaches it.
2. The agent's own report isn't evidence; the tool-call log is.
3. Agents fix exactly what you name and quietly drop other things.
4. Put limits in code, not in the prompt.
5. Automatic checks catch structure, not truth.
6. A better model helps, but doesn't replace reading the page.
7. Total model cost for the night: about $0.03. The hours went into setup.
