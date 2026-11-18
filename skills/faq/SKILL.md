---
name: faq
description: A frequently asked questions page, grouped by topic, answers first.
max_words: 1400
---

# FAQ skill

## How to build it
- Group questions under 2 to 5 topic headings (H2). Each question is an
  H3 written the way a real person would ask it, ending in "?".
- **Answer first.** The first sentence of every answer is the direct
  answer ("Yes.", "No.", "By 9:45 AM.", "$15."), then one to three short
  sentences of detail. This is principle 2 (deal-breakers up front)
  applied to every question.
- If an answer has conditions, list them explicitly: "Only if all three
  are true:" followed by a list.
- Where another page on the site explains the topic in depth, end the
  answer with one "More: " link to that page.
- Every question must be answerable from the specification, the knowledge
  folder or the site's pages. If a question the student listed can't be
  answered from those, write the answer as [CHECK: ...].
- Open with a one or two sentence intro saying who the FAQ is for.

## Block template
Use exactly this markup pattern (fill in the brackets):

```
<!-- wp:paragraph -->
<p>[Intro: who this page is for]</p>
<!-- /wp:paragraph -->

<!-- wp:heading -->
<h2 class="wp-block-heading">[Topic]</h2>
<!-- /wp:heading -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">[Question?]</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p><strong>[Direct answer.]</strong> [Detail.]</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>More: <a href="/[slug]/">[Page title]</a></p>
<!-- /wp:paragraph -->
```

For a list of conditions:

```
<!-- wp:list -->
<ul class="wp-block-list"><!-- wp:list-item -->
<li>[Condition]</li>
<!-- /wp:list-item --></ul>
<!-- /wp:list -->
```

## Skill-specific audit
- Does every answer start with the direct answer?
- Is every question something a real reader would ask, in their words?
- Are any two questions really the same question?
