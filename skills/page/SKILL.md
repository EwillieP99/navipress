---
name: page
description: A general content page (background, how-it-works, timeline, resources, people) built from your knowledge folder.
max_words: 1500
---

# Page skill (general)

Use this for any page that isn't an FAQ or a glossary: background, a
timeline, a resources list, profiles of key people or organizations,
"how it works". Not for the page carrying your central argument; write
that one yourself.

## How to build it
- Read `knowledge/project/topic.md` first, then every file the spec names.
- Open with two or three sentences: what this page covers and why the
  reader needs it. Put the most important point in the first paragraph.
- Use H2 for sections and H3 inside them. Every heading should tell a
  skimming reader what's below it ("Why the flyer failed", not "Results").
- Facts come only from the knowledge folder and the site. Keep the source
  next to each fact the first time: "(Author, Year)" or "On Findings".
- Lists for steps, criteria and comparisons; paragraphs for explanation.
- A timeline uses one H3 per date ("November 11, 2026: Experiment 2")
  with one or two sentences each, in order.
- A resources page groups links under H2s by purpose, with one sentence
  per resource saying what it's for. Outside links are allowed only if
  the spec or the knowledge folder gives the exact URL.
- End with a short "Where to go next" paragraph linking two of the site's
  own pages.

## Block template
```
<!-- wp:paragraph -->
<p>[Opening: what this page covers and the most important point.]</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading">[Section heading that says what's below]</h2>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>[Short paragraph, under 80 words.]</p>
<!-- /wp:paragraph -->

<!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
<li>[Item]</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->
```

## Skill-specific audit
- Could a reader get the main point from the first paragraph alone?
- Does every fact trace back to a file in knowledge/ or a page on the site?
- Is this page staying in its lane, not repeating another page?
