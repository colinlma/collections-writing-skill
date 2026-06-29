# Collections Writing Skill

A [Claude](https://claude.com/claude-code) skill that writes SEO copy for ecommerce product listing pages (PLPs / collection / category pages). Give it a CSV of URLs and target keywords; it crawls each page to see what products are actually there, then writes factually grounded HTML copy in your brand's voice, with internal links to related pages.

The point of difference is grounding. Most AI copy invents product details. This skill crawls the live page first and audits every claim against what it found, so the copy describes the products that actually exist — not a plausible-sounding hallucination.

## What it does

For each URL, the skill runs an 8-step process:

1. **Skip logic** — leaves already-written rows alone, preserves and expands existing copy.
2. **Primary keyword** — takes the topic from the keyword, not the (often misleading) URL slug.
3. **Crawl the PLP, then its PDPs** — fetches the collection page, extracts its product links, then crawls each product page to build a per-page verification corpus (real product names, composition, construction details). This two-level crawl is what makes the copy verifiable.
4. **Write** — produces `<h2>` + `<p>` HTML copy in brand voice, leads each paragraph with a citable standalone claim, goes deep on 2–3 products, weaves in 3–4 internal links as absolute URLs.
5. **Voice check** — catches hype, corporate speak, exclamation marks, em-dash asides, third-person distancing.
6. **Verifiability loop (validate → fix → re-validate)** — a deterministic verifier (`verify_claims.py`) plus per-piece validator and fixer subagents check every spec, material, and product name against the PDP corpus and rewrite anything unsupported. The loop runs until two consecutive clean passes (max 3 rounds); unresolved claims are flagged for human review, never invented around.
7. **Format + write to CSV** — valid HTML, word count, link count, and audit flags written back to the sheet.

It avoids anything that goes stale — product counts, prices, size ranges, length measurements — by rule.

## What's in here

```
skills/ecommerce-plp-copy/
├── SKILL.md                  # the skill definition + full process
└── scripts/
    ├── crawl_page.py         # Playwright crawler: rendered text + (--links) all page links
    └── verify_claims.py      # deterministic claim verifier against the PDP corpus
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

## Using the scripts directly

**Crawl a page** (rendered text). Add `--links` to also dump every anchor href — use it on a collection page to discover the product (PDP) URLs to crawl next:

```bash
# PLP: text + all links
python3 skills/ecommerce-plp-copy/scripts/crawl_page.py \
  "https://example.com/collections/some-category" plp.txt --links plp.links.json

# PDP: text only
python3 skills/ecommerce-plp-copy/scripts/crawl_page.py \
  "https://example.com/products/some-product" pdp.txt
```

It launches headless Chromium with a real-browser user agent, waits for the page to render, and writes the visible text to the output file.

**Verify copy claims** against the corpus you build from the PDP crawls:

```bash
python3 skills/ecommerce-plp-copy/scripts/verify_claims.py corpus.json copy.json --output findings.json
```

`verify_claims.py` flags numeric specs, materials, and construction terms that appear in the copy but not in any product page for that collection. Its default patterns are apparel-oriented — pass `--patterns patterns.txt` for other verticals.

## Output

A CSV with your original columns plus the finished HTML copy, word count, internal-link count, and a flags/notes column (404s, low inventory, keyword/page mismatches, verifiability findings).

## License

MIT — see [LICENSE](LICENSE).
