# FAQ page specification

## Page title
FAQ

## Who asks these questions
Students who publish pages people act on: club officers posting events, people running a department's or organization's page. They've heard AI is "reading the web" and want quick, practical answers: does this affect my page, and what do I do about it? Many will land here from the homepage or the Checklist.

## The questions
Group them under these topics, in this order, in the reader's own words.

**About this project**
- What is the Agentic Web Observatory? (Home, About: a UF student research project for MMC3260; the question is whether an organization's message survives when an AI reads the page for someone.)
- Was the event in the experiments real? (No. The Spring 2027 UF AI & Media Innovation Forum is fictional, but its two venues are real UF buildings. The Experiments.)
- Which AI tools did you test? (Method & Limits: all through UF NaviGator; gpt-oss-20b, Claude Opus 5.5 and Gemini 3 Flash, plus Claude acting as an agent fetching the page itself.)

**How AI reads your page**
- Can an AI read the text on my flyer? (Usually not. Tools that convert pages to plain text drop images; in Experiment 2, none of the four AI readers reported facts that were only in the flyer. Some screenshot-based agents may read images, but this project didn't test that. Findings, AI Agents: A Student Guide.)
- Will an AI read my collapsed FAQ or accordion sections? (Yes: NaviGator's loader kept the collapsed FAQ text. Findings.)
- If I update the flyer but not the page text, will the AI notice? (No. Three of four AI readers trusted the outdated text and sent people to the wrong building. Findings.)
- What happens if the AI can't open my page at all? (Some models say so; others guess. One placed this UF event at Columbia University. Findings, Method & Limits.)
- Would a better AI model fix these problems? (Not on its own. NaviGator's smallest default model got all three questions right when the facts were in plain text. Findings: "It wasn't the model; it was what reached the model.")
- If an AI answer links to my page, can I trust that it described my page correctly? (No. Fluent answers often aren't fully supported by their sources (Liu, Zhang & Liang, 2023), and Google users clicked a link inside an AI summary on just 1% of visits (Pew Research, 2025). Checklist.)

**What to do about it**
- What's the single most important fix? (Every fact in text: if it's on the flyer, it's also in the page text or in alt text that states it. Checklist.)
- What does good alt text look like? (States the facts: "Flyer: Afternoon workshop moved to Weimer Hall 1064. Bring your physical Gator1 card; phone photos are not accepted." Not "Event flyer." Checklist.)
- How can I test my own page? (Ask an AI the questions your audience will ask, giving it your page's link rather than pasted text, then compare its answers with the page sentence by sentence. Checklist, steps 4 and 5.)
- Do humans and AI miss the same things? (No. People miss buried text, like the 9:45 AM check-in cutoff; AI misses images. All four AI readers caught the cutoff. Findings.)

**About this site**
- Was this site made with AI? (Yes, openly. Ethan directed the project and made the judgment calls; an AI agent helped run Experiment 2, build the test page, make the charts and edit the site. This FAQ was drafted by an agent running on UF NaviGator and checked by Ethan. About, How This Was Built.)

## Where the answers come from
Read these pages in full before writing: Home (page 51), About (7), Findings (14), The Experiments (16), Method & Limits (35), Checklist (21), AI Agents: A Student Guide (100), How This Was Built (99). Also check the knowledge folder with list_sources. Use nothing else.

## Voice
Match the Checklist page: direct, practical, short sentences, written for a busy student. First person ("I tested") when talking about the project.

## Must not
- No questions beyond the list above.
- No statistics or claims that aren't in my notes or on the pages listed.
- No links to other websites.
- No images.
- Keep it under about 1,400 words.
