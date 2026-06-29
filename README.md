# Collections Writing Skill

A [Claude](https://claude.com/claude-code) skill that writes SEO copy for ecommerce product listing pages (PLPs / collection / category pages). Give it a CSV of URLs and target keywords; it crawls each page to see what products are actually there, then writes factually grounded HTML copy in your brand's voice, with internal links to related pages.

The point of difference is grounding. Most AI copy invents product details. This skill crawls the live page first and audits every claim against what it found, so the copy describes the products that actually exist — not a plausible-sounding hallucination.

## What it does

For each URL, the skill runs an 8-step process:

1. **Skip logic** — leaves already-written rows alone, preserves and expands existing copy.
2. **Primary keyword** — takes the topic from the keyword, not the (often misleading) URL slug.
3. **Crawl** — fetches the live page with the bundled Playwright script to capture real product names, materials, and construction details.
4. **Write** — produces `<h2>` + `<p>` HTML copy in brand voice, leads each paragraph with a citable standalone claim, goes deep on 2–3 products, weaves in 3–4 internal links as absolute URLs.
5. **Voice check** — catches hype, corporate speak, exclamation marks, em-dash asides, third-person distancing.
6. **Fact check** — every product name and spec is verified verbatim against the crawl data.
7. **Verifiability audit** — a structured pass that flags any claim not backed by a product's page (the classic failure mode: extrapolating one product's feature onto a sibling that doesn't have it).
8. **Format + write to CSV** — valid HTML, word count, link count, and flags written back to the sheet.

It avoids anything that goes stale — product counts, prices, size ranges, length measurements — by rule.

## What's in here

```
skills/ecommerce-plp-copy/
├── SKILL.md                  # the skill definition + full 8-step process
└── scripts/
    └── crawl_page.py         # Playwright crawler: fetches a page's rendered text
```

## Install

### Claude Code

Copy the skill folder into your project (or personal) skills directory:

```bash
# project-level
mkdir -p .claude/skills
cp -R skills/ecommerce-plp-copy .claude/skills/

# or personal-level (available across all projects)
cp -R skills/ecommerce-plp-copy ~/.claude/skills/
```

Restart Claude Code (or start a new session). Trigger it by asking something like *"write PLP copy for these collection URLs"* or *"generate category-page SEO copy from this CSV."*

### Other agents

`SKILL.md` is plain Markdown with YAML frontmatter, so any agent framework that loads skills from a folder can use it — point your loader at `skills/ecommerce-plp-copy/`.

## Prerequisites

The crawl step needs Playwright:

```bash
pip install playwright --break-system-packages
python3 -m playwright install chromium
```

## Inputs you provide

1. **A CSV** with a URL column and (ideally) a target-keyword column. Optional columns for existing copy and a destination column for the new copy.
2. **Brand voice guideline** (optional but recommended) — tone, words to avoid, words to prefer, good/bad examples. The richer it is, the better the output.
3. **Parameters** (or use defaults) — word count (200–300), internal links per page (3–4), max sentences per paragraph (3).

## Using the crawler directly

The crawler works on its own:

```bash
python3 skills/ecommerce-plp-copy/scripts/crawl_page.py \
  "https://example.com/collections/some-category" \
  output.txt
```

It launches headless Chromium with a real-browser user agent, waits for the page to render, and writes the visible text to `output.txt`.

## Output

A CSV with your original columns plus the finished HTML copy, word count, internal-link count, and a flags/notes column (404s, low inventory, keyword/page mismatches, verifiability findings).

## License

MIT — see [LICENSE](LICENSE).
