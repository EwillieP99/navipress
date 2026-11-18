---
name: glossary
description: An alphabetical glossary of the terms a newcomer needs to read the rest of the site.
max_words: 1400
---

# Glossary skill

## How to build it
- Open with a two or three sentence intro: who the glossary is for and
  what they'll be able to do after reading it.
- Terms in alphabetical order. Each term is an H3; no H2 needed unless
  the student asks for groups.
- Definitions are one to three plain sentences. Lead with what the thing
  is, then why it matters to this site's reader.
- Where the site's own research involves the term, add one short line
  starting "On this site:" with a link to the page that explains it.
  Only link pages that actually discuss the term; check with get_page.
- Keep the author and year with any study the notes cite, e.g.
  (Liu, Zhang & Liang, 2023). Never drop a citation the notes include.

## Block template
```
<!-- wp:paragraph -->
<p>[Intro]</p>
<!-- /wp:paragraph -->

<!-- wp:heading {"level":3} -->
<h3 class="wp-block-heading">[Term]</h3>
<!-- /wp:heading -->

<!-- wp:paragraph -->
<p>[Definition.]</p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>On this site: <a href="/[slug]/">[Page title]</a> [what it shows].</p>
<!-- /wp:paragraph -->
```

## Skill-specific audit
- Is every term in the student's list, and only those terms?
- Does each "On this site" page actually mention the term?
- Did any citation from the notes go missing?
