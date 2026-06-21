# Cursor IDE Setup & AI-Powered SEO Research Project

This repository documents two stages of a portfolio project:
1. **Setup** — installing Cursor IDE with the Claude Code and Codex extensions.
2. **Research** — a curated research project on **AI-Powered SEO Content Production**.

---

## Part 1 — Tools & Setup

### Tools Installed
- **Cursor IDE** — AI-powered code editor (cursor.com)
- **Claude Code for VS Code** — extension by Anthropic
- **Codex** — coding agent extension by OpenAI

### Steps Completed
1. Installed Cursor IDE and signed in.
2. Installed the Claude Code extension and logged in with my Anthropic account.
3. Installed the Codex extension and logged in with my OpenAI account.
4. Created this public GitHub repository.
5. Cloned and opened it in Cursor.
6. Built out the research project documented below.
7. Committed and pushed incrementally throughout.

### Issues & Solutions
- **Couldn't find the Extensions panel at first.** Cursor opened in the Agent Window, which hides the editor sidebar. Switched to the Editor Window, then opened Extensions via `View → Extensions`.
- **Both extensions installed but not logged in.** Used the Command Palette (`Ctrl+Shift+P`) to open each extension's sidebar and signed in to both.
- **YouTube IP-blocked the transcript scraper.** The first approach used the `youtube-transcript-api` Python library, which scrapes YouTube's InnerTube endpoint from the local machine. Every request came back `RequestBlocked` — YouTube IP-blocks transcript requests from this network (confirmed across multiple attempts, including a delayed retry; the channel RSS feeds were unaffected). **Fix:** switched transcript collection to the [Supadata](https://supadata.ai) API, which fetches server-side, so the local IP block doesn't apply. All 18/18 transcripts then fetched successfully. (A first Supadata run hit a Cloudflare `1010` block on the default `Python-urllib` User-Agent — fixed by sending a browser User-Agent.)

---

## Part 2 — Research Project: AI-Powered SEO Content Production

### Topic chosen
**AI-Powered SEO Content Production** — how practitioners use AI to research, produce, structure, and optimize content for both traditional search and AI/generative engines (GEO/AEO).

### Why this topic
It sits at the intersection of two fast-moving fields and lets the research surface genuinely technical practitioners (people building tools and running experiments), not just commentators. It's also where AI changes the playbook most right now, so recent content is plentiful and substantive.

### The 10 experts (and why these ones)
I weighted the list toward people who **practice** what they teach — documented case studies, original research, shipped tools, or real client results — over pure "SEO influencer" listicle names. Full annotations with links live in [`/research/sources.md`](research/sources.md).

**Operators with visible results:** Mike King (iPullRank — Relevance Engineering, 661% ChatGPT-visibility case), Ross Simmonds (Foundation — GEO, original keyword studies), Aleyda Solís (Orainti — documented client growth, Crawling Mondays), Eli Schwartz (Product-Led SEO), Tim Soulo (Ahrefs' content engine).

**Technical / tool builders:** Ryan Law (Ahrefs AI Content Helper), Jori Ford (Octopus Labs — AI crawler log experiments), Koray Tuğberk Gübür (Semantic SEO / Topical Authority experiments), Bernard Huang (Clearscope — content optimization platform).

**Standout educator:** Nathan Gotch (Gotch SEO / Rankability — AI-powered systems, large instructional library).

I deliberately excluded high-follower generalists and "YouTube automation" creators — see the exclusion notes in `sources.md` for the reasoning.

### Repository structure
```
/research
  sources.md                 # all 10 experts: links, dates, annotations
  /linkedin-posts            # recent posts, organized by author
  /youtube-transcripts       # transcripts, organized by video
  /other                     # articles, studies, frameworks
/scripts
  fetch_transcripts.py       # programmatic YouTube transcript collection
  channels.json              # channel/video sources for the fetch script
```

### How content was collected
- **YouTube transcripts:** fetched programmatically via the [Supadata](https://supadata.ai) transcript API (`GET /v1/transcript`) using [`/scripts/fetch_transcripts.py`](scripts/fetch_transcripts.py), driven by Claude Code. The 18 source videos (3 each for the 6 authors with channels) are listed in [`/scripts/channels.json`](scripts/channels.json); their IDs were pulled straight from each channel's YouTube RSS feed, so every ID is genuine. The script reads the API key from `SUPADATA_API_KEY` (env var or a gitignored `.env`), polls Supadata's async job endpoint for long videos, and logs any video without a transcript to a gitignored `_skipped.log`. Supadata replaced an initial `youtube-transcript-api` attempt that YouTube IP-blocked (see Issues above).
- **LinkedIn posts:** collected manually per each author's recent activity (in line with LinkedIn's terms of service) and saved as Markdown, one folder per author.
- **Other materials:** key articles, case studies, and frameworks saved/linked under `/research/other`.

### Why these sources support a real playbook later
The mix spans the full production pipeline — strategy (Schwartz, Soulo), AI-search mechanics (King, Ford), content structuring for LLMs (Gübür, Huang), distribution (Simmonds), and repeatable systems (Gotch, Law, Solís). That breadth is what a credible "AI SEO content production" playbook needs: not 50 versions of the same tactical post, but complementary, evidence-backed perspectives.
