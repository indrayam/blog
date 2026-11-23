# indrayam.com blog

This repository contains the static HTML blog published at [blog.indrayam.com](https://blog.indrayam.com/). It is one of the sites in the wider `indrayam.com` experience, alongside the home page at `indrayam.com`, the resume, Daily Diff, and Field Notes. Every page uses the shared site nav, and blog pages nest a small sub-nav under Writings with By Year (`/`) and By Category (`/archives/categories.html`). The parent [`AGENTS.md`](../AGENTS.md) describes how those sites fit together and applies to work that crosses repository boundaries.

## Project map

- `index.html` — home page: every post grouped by year in collapsed sections.
- `archives/` — the posts (`archives/<category>/NNNNNN.html`) and `categories.html`. `/archives/index.html` redirects to `/`.
- `aboutme.html`, `disclaimer.html`, and `404.html` — supporting site pages.
- `style.css` — shared blog styling and responsive layout.
- `js/` — browser scripts used by the pages; `archive.js` runs the year and category lists.
- `tools/redesign.py` — the one-time script that moved every page to the shared layout (kept for reference, not deployed).
- `favicon.ico`, `apple-touch-icon.png` — the icon shared by every indrayam.com site.
- `images/` — images and other media referenced by the site.
- `robots.txt` and `sitemap.xml` — crawler guidance and published URL inventory.
- `vercel.json` — Vercel redirects for legacy post URLs.

## Working on the site

Read [`AGENTS.md`](AGENTS.md) before editing. It covers preservation, scope, and verification expectations. This is a static site; no general build or test command is documented. Check the relevant files and identify an appropriate way to preview any page or behavior you change. Do not assume editing a source file regenerates other pages or assets.
