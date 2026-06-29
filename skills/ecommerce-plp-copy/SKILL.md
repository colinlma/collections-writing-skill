---
name: ecommerce-plp-copy
description: >
  Use this skill whenever the user wants to write, rewrite, or audit SEO copy for ecommerce
  product listing pages (PLPs), collection pages, or category pages. This includes writing
  footer copy, category descriptions, or editorial content that sits below the product grid
  on pages like /collections/* or /category/*. Trigger this skill any time the user mentions
  writing PLP copy, collection page descriptions, category page SEO content, product listing
  page copy, or needs to generate HTML-formatted marketing copy for multiple ecommerce URLs
  from a CSV or spreadsheet. Also trigger when the user wants to crawl product pages and write
  copy based on what's actually on the page, or when they mention internal linking across
  collection pages. Works for any ecommerce brand (Shopify, custom platforms, etc.), not just
  one specific store.
---

## Pre-flight: Writing Conventions (MANDATORY)

**Before drafting ANY written output from this skill, read the brand voice guideline the user provides, in full.**

That guideline is the source of truth for every sentence you write. A good one covers: voice and audience defaults, banned tics (e.g. "let's dive in", "buckle up", "the bottom line"), banned phrases (e.g. "leverage", "unlock", "robust", "seamless", "delve", "in today's fast-paced digital landscape", "moreover", "ultimately"), opening rules (lead with a specific claim, number, or anecdote — never with setup or a definition), rhythm rules (e.g. at least one short sentence per paragraph, no more than three long sentences in a row, at most one em-dash per paragraph), formatting rules, and a fact-pass rule (never invent stats, names, or quotes — flag anything unverified instead).

If you split work across writer + editor subagents, include the brand voice guideline in each one's "inputs to read" block. Keep a single source of truth — when conventions change, update only the guideline so every run inherits it.

If no guideline is provided, write in a clean, direct, conversational tone: second person, no hype, no exclamation marks, no em dashes, short varied sentences. Warn the user that results improve with a brand-specific guideline.

---

# Ecommerce PLP Copy Writer

Writes SEO-optimized copy for ecommerce product listing pages (PLPs / collection pages). Takes a CSV of URLs with target keywords, crawls each page to gather real product data, then writes factually accurate HTML copy in the brand's voice with internal links to related pages.

## When to Use This Skill

Any time a user needs copy written for ecommerce category/collection/PLP pages, especially when:
- They have a CSV of URLs and keywords
- They want copy that's factually grounded in what's actually on each page
- They need internal links between related pages
- They have brand voice guidelines to follow
- They want batch processing across many pages

## Setup

Install Playwright if not already present:
```bash
pip install playwright --break-system-packages
python3 -m playwright install chromium
```

## Inputs

The user will typically provide:

1. **A CSV file** with at minimum a URL column and ideally a keywords column. Common column patterns:
   - `URL` or `Top pages` — the page URLs
   - `Keywords` — target keywords with format like `Primary KW: keyword (volume/mo)`
   - `Existing Copy` — current copy on the page (blank = no existing copy)
   - `Reworked Copy` — where your new copy goes (if populated, skip this row)

2. **Brand voice guidelines** — a PDF, document, or description of how to write. If none provided, write in a clean, direct, conversational tone without hype or marketing fluff.

3. **Parameters** (confirm with user or use defaults):
   - Word count range: 200–300 words (default)
   - Internal links per page: 3–4 (default)
   - Max sentences per `<p>` tag: 3 (default)
   - H2 tag: include with primary keyword, pluralized (default)

## Before You Start

Before writing any copy, do two things:

1. **Read the brand voice guidelines** — if the user provided a PDF or doc, read it fully. Internalize the tone, the do/don't lists, and the example transformations. These guidelines should influence every sentence you write, not just serve as a checklist at the end.

2. **Scan the full CSV** — understand the complete set of URLs so you can make smart internal linking decisions. You need to know what pages exist before you can pick which ones to link to.

## The 8-Step Process

For each URL that needs copy, follow these steps in order. This is the heart of the skill — each step matters because skipping one leads to copy that's either factually wrong, off-voice, or poorly formatted.

### Step 0: Check Skip Logic

Before doing any work on a URL, check:
- If `Reworked Copy` already has content → **skip** (already done)
- If `Existing Copy` is blank → proceed to write fresh copy
- If `Existing Copy` has content → proceed, but preserve/expand the existing copy rather than replacing it. Keep the original voice and key points while adding internal links and expanding to meet word count.

### Step 1: Identify the Primary Keyword

Extract the primary keyword from the Keywords column. The main topic of the copy should come from this keyword, not the URL slug — URL slugs are often unoptimized and misleading. If the keyword says "mens hybrid shorts" but the URL slug says "elastic-waist-walkshorts", write about mens hybrid shorts.

### Step 2: Crawl the Page

Use the bundled crawl script at `scripts/crawl_page.py` to fetch the page content:

```bash
python3 scripts/crawl_page.py "https://example.com/collections/page" "/tmp/crawl_output.txt"
```

Read the crawl output to understand:
- What products are actually on the page (names, types, styles)
- What product attributes are available (colors, materials, construction features, fit styles)
- Any filters or categories shown

Note: the crawl data will contain prices, size options, and product counts. Use these only to understand the page — never write them into the copy. Prices, sizes, and counts all change frequently and make copy go stale.

This step prevents the most common failure in ecommerce copy: making claims about products that aren't there. If the page shows 3 products all in the same style, the copy should reflect that narrow selection rather than implying a wide range.

### Step 3: Write the Copy

Write the copy following these principles:

**Structure:**
- Start with an `<h2>` tag containing the primary keyword (pluralized, title-cased). If the keyword contains "mens", use "Men's" with an apostrophe.
- Use `<p>` tags with a maximum of 3 sentences each. This prevents walls of text.
- Target the user's specified word count range (default 200–300 words).
- Include 3–4 internal links as `<a href="...">` tags using absolute URLs. Link to the most semantically related pages from the CSV — pages that a shopper on this page would naturally want to browse next.

**AEO chunk rule:** The opening sentence of each `<p>` block should be the most citable, standalone claim about this category. If an LLM pulled just that sentence, it should tell a reader something specific and complete — not set up what's coming, not orient them to the section. Lead with the answer, then explain it.

Bad: "When it comes to men's boardshorts, there are a few things to consider..."
Good: "Our men's boardshorts combine quick-dry stretch fabric with outseam lengths built for water transitions. They go from surf to sidewalk without a change."

**Content approach — depth over breadth:**
- Lead with what makes this category distinct — what differentiates these products from adjacent categories.
- **Pick 2–3 products to go deep on.** Each gets 1–3 sentences with real differentiating detail (fabric, fit, construction, use case) pulled directly from the PDP. Don't list ten products with one adjective each — that reads like a search result, not editorial copy.
- **Sub-category sweep is allowed.** When several products share an attribute (e.g. all hoodies in the drop are made from the same heavyweight fleece), one general statement covers the group: "Our hoodies are sized for cooler mornings and post-surf coverage." This avoids repetition and keeps word count down.
- Name specific product lines, styles, or key features that appear in the crawl data. Concrete names (like "the Tidewater Hybrid Short" or "the Ridgeline Pullover") are more useful to shoppers than vague descriptions. **Use the verbatim product name from the PDP.** Don't shorten ("4/3mm Thermal Sealed Chest-Zip Wetsuit" → "Thermal Wetsuit") — the shortened version isn't the actual product name and won't verify against crawl data.
- Include factual details: fabric types, fit styles (e.g., straight, scallop, regular), construction features. **Pull these verbatim from the PDP** ("4-way stretch", "GBS seams", "180g cotton"). Don't substitute generic descriptors like "cotton-rich" or "garment-washed" unless those exact phrases appear in the source PDP.
- End with a natural transition to related categories via internal links.

**Vary internal link placement.** Don't dump all 3–4 links in the closing paragraph — that reads as a footer dump. Place at least one link mid-paragraph where it fits the sentence naturally, and let the closing paragraph carry one or two transitional links. A good model: one link at the end of paragraph 2 (mid-copy), and two or three transitional links in the closing sentence.

**Phrasing to avoid as paragraph openers:**
- "For carry, see..." / "For wear, see..." / "For X, see..." — these are awkward telegraphic intros that read as catalog navigation rather than editorial copy. Open with a complete sentence about the products or use case, then weave the link inline. Example: instead of "For carry, see backpacks where the smaller crossbody and waistbag options sit alongside the bigger totes," write "Backpacks, crossbody bags, and waistbags round out the carry side, sized to wash sand off and keep going."
- Stacked "For X..." bullets across multiple paragraphs read as a sitemap. Mix sentence shapes.

**More anti-patterns (don't do):**

- **"Edit" as a noun for a curated collection.** Phrases like "Fall Shop is the cooler-weather edit" or "the summer edit" read as agency/fashion-magazine speak — nobody actually talks that way. Use *collection*, *drop*, *range*, *selection*, or just describe what's in the page. Example: instead of "Fall Shop is the cooler-weather edit. Heavier knits..." write "Fall Shop pulls together cooler-weather pieces. Heavier knits..." This applies even when fashion brands themselves use "edit" internally — strip it from copy.

- **"Lineup" as a connector or wrapper.** Phrases like "the men's gift lineup," "the wetsuit lineup," "the pro boardshort lineup," or "the rest of the lineup" read as filler. Same agency-speak problem as "edit" — nobody talks like that. Use *range*, *collection*, *drop*, *selection*, or just name the category. Example: instead of "The rest of the wetsuit lineup including full suits and springsuits sits at men's wetsuits" write "The rest of the wetsuit range including full suits and springsuits sits at men's wetsuits." Hard ban — no exceptions.

- **Sentence fragments.** Every sentence needs a subject and a finite verb. Headline-style noun-phrase fragments — "Marked-down sweatshirts, hoodies, half-zips, and pullovers." or "Halter neckline, fitted body, sized for evenings out." or "Adjustable arch strap, rounded toe with flex sole, and partially recycled exterior fabric with SMART Foam." or "Pieces designed to wear across the closet." — read as catalog bullets, not editorial copy. Same with bare prepositional phrases ("Sized for long days in and out of the water.") and bare interrogatives used as section headers ("Browsing by gender?"). Fix by adding a subject and verb: "The sale grid covers sweatshirts, hoodies, half-zips, and pullovers." / "It pairs a halter neckline with a fitted body, sized for evenings out." / "They're sized for long days in and out of the water." / "If you're browsing by gender, jump to women's swim or men's boardshorts." When you finish a draft, scan every sentence for a verb — if it's just a noun phrase, rewrite.

- **Pairing logic that links a bottom-to-bottom or top-to-top as the "anchor."** When the copy describes a bottom (shorts, pants, jeans, skirt), don't follow up with "to anchor the look, pair with [other bottoms]." That makes no sense — bottoms anchor with tops. Same in reverse: when describing a top, don't suggest pairing with another top as the foundation. Suggested pairings should *complement*, not *duplicate*. Bad example:

  > The Wanderer Woven Shorts pair with most printed tops in the season. Perfect for everyday activities like running errands and short walks to the water.
  >
  > To anchor the look with bottoms, pair with [women's pants](...).

  The first paragraph correctly pairs shorts with tops. The second paragraph then breaks logic by linking shorts → pants. Fix: "To anchor the look, pair with a tee from [women's tops](...)." Always sanity-check the pairing direction before placing the link.

- **"X half" claiming a fractional split that isn't actually a half.** Don't call the swim portion of a look "the swim half" or any other category "the X half" unless the outfit literally has two equal parts. A bikini top + bottom + cover-up isn't half of anything. Use *the swim portion*, *the swim side*, *the swim pieces*, or just describe what's in the drop. Same for "the dress half," "the bottoms half," etc. when there's no defined whole.

- **"Kit" as a synonym for an apparel outfit.** Phrases like "build the kit" or "a coordinated kit" used to mean a clothing combination don't read naturally. People say *outfit*, *look*, *set*, or just describe the pieces. **Exception:** "kit" works for actual gear stacks where multiple equipment pieces combine for a function — e.g., a wetsuit kit (suit + boots + gloves + hood), a surf kit (boardshorts + rashguard + booties), a beach kit (towel + bag + sunscreen). For pairing tops with bottoms, drop "kit" and write "outfit" or "look" — or skip the wrapper word and just describe the pairing.

  Bad: "The matching Sunliner cuts pair across tops and bottoms in the same prints, so the swim half builds easily into a coordinated kit."
  Good: "The matching Sunliner tops and bottoms come in the same prints, so the swim pieces pair into a coordinated set."

- **Repeated sentence openers.** Don't begin consecutive sentences with the same word — especially "For" (the most common offender), but also "The," "Pair," "Browse," etc. Stacked "For X, see..." across two or three sentences in a row reads as a sitemap, not editorial copy. Vary the structure: lead one sentence with the product or use case, the next with the link target, the next with a closing thought. Bad example (three sentences in a row starting with "For"):

  > For all of our tops, see [women's tops](...). For longer silhouettes, browse [women's dresses](...).
  >
  > For pre-coordinated head-to-toe looks, see [matching sets](...).

  Fix by inverting one or two of them: "Browse [women's tops](...) for the rest of the range, or step into [women's dresses](...) for longer silhouettes. Pre-coordinated looks live at [matching sets](...)." When you finish a draft, scan paragraph openers and intra-paragraph sentence openers in sequence — if two sentences in a row start with the same word, rewrite at least one.

**What to avoid — anything that goes stale when inventory, pricing, or availability changes:**
- **Product/style counts** — never state how many styles, pieces, or results a page has (e.g., "93 styles", "686 pieces", "80 styles deep", "182 styles and counting"). Inventory changes constantly and these numbers go stale immediately. Also avoid writing counts as words ("Fifty-eight pieces across...").
- **Prices and price ranges** — no dollar amounts anywhere in the copy. No price ranges, no "starting at" pricing, no "sits in the $35.95 range" (e.g., "$25.95 to $49.95", "prices from $22.95", "with markdowns taking some styles down to $28.97"). Prices change with sales, markdowns, and seasonal shifts. **Exception:** sale/clearance pages may use general price language like "full-price", "marked down", "markdowns", and "spending full price" — but still no specific dollar amounts.
- **Size ranges and size availability** — never mention specific size ranges (e.g., "sizes XS to XL", "XXS through 2XL", "waist sizes 24 through 31", "available in sizes XS through M", "S/M, L/XL, and one-size across the range"). Size availability fluctuates by style and season, and stating it creates inaccuracy the moment stock changes.
- **Length measurements** — no inseam, outseam, or inch measurements (e.g., "18-inch outseam", "15 to 21 inches"). Also avoid relative length language like "mid-length cut", "shorter fits to longer options", or "short enough / long enough". Fit *styles* (straight, scallop, regular, arch) are fine — those describe the cut shape, not the measurement.
- Claims you can't verify from the crawl data (e.g., "all products have UPF 50" when only some do — use "many of our [product type]" instead)
- Hype words, exclamation marks, ALL CAPS, emojis
- Em dashes (— or —) used as sentence breaks or parenthetical asides. These create a rambling, stream-of-consciousness feel. Rewrite instead — split into two sentences or restructure so the thought flows naturally without the dash. Example: "There's something magical about slipping into your favorite hoodie — that instant feeling of warmth" should become "There's something magical about slipping into your favorite hoodie. That instant feeling of warmth is hard to beat."
- Generic filler sentences that don't add information
- The word "capsule" or "capsule collection" to describe collections or PLPs. Use "collection," "lineup," "drop," "range," or just the collection's name instead. This is a hard ban — no exceptions, even for editorial/print-led collections that the brand internally calls "capsules." Reads as agency-speak.
- Overuse of the word "filter." Once per page is fine when it's the natural verb (e.g., "filter by color"). Don't lean on it as a connector or repeat it across paragraphs. Avoid phrases like "filter to X" or "the X filter" as link wrappers. If you find yourself writing "filter" twice in one piece, rewrite at least one to use "browse," "see," "shop," "narrow down," or just name the category directly.

### Step 4: Voice Check

Read the copy back and verify it matches the brand voice guidelines. Common voice violations to catch:
- Hype language ("ultimate", "premium", "best ever", "cutting-edge")
- Industry slang or forced coolness that the brand wouldn't use
- Corporate marketing speak ("elevate your journey", "unparalleled experience")
- Sustainability buzzwords ("eco-friendly", "planet-positive") unless the brand specifically uses them
- Exclamation marks, ALL CAPS, emojis
- Em dashes used as mid-sentence breaks or parenthetical asides (— or —) — rewrite as two sentences or restructure
- Third-person distancing ("Brand X products are...") when the voice guidelines call for first/second person ("Our products..." / "You'll find...")

If the brand guidelines specify a particular personality (e.g., "confident but understated", "knowledgeable but not nerdy"), check that the copy hits that tone rather than defaulting to generic marketing voice.

### Step 5: Fact Check Against Crawl Data

Compare every claim in the copy against what you found on the page:
- Are the product names real? (Check against crawl data — verbatim, not shortened)
- Are the fabric types and features accurate?
- Does the page actually have the variety you're describing?
- If you say "available in short and long sleeve", does the page actually show both?

Flag anything you can't verify. It's better to be vague ("several styles") than confidently wrong ("twelve colorways in every fit").

### Step 5b: Programmatic Verifiability Audit

After writing all the copy, run a structured audit before delivery. This catches claims you wrote on autopilot that aren't backed by the crawl. Failure mode this prevents: extrapolating a feature from one PDP to a sister product whose PDP doesn't claim it.

For each piece, extract:

1. **Named products** (regex for capitalized product-name patterns). Check each against the source PLP product list and the per-product PDP names. If the name in copy isn't a verbatim or clean substring/superstring of a real product name, flag it. Common cause: editorial shortening ("4/3mm Thermal Sealed Chest-Zip Wetsuit" → "Thermal Wetsuit"). Use the full name.

2. **High-risk specific claims** — patterns to extract:
   - Numerical specs (`4/3mm`, `5mm`, `180g cotton`, `4-way stretch`, `20" boardshorts`)
   - Material names from the PDP vocabulary (`graphene-infused`, `SMART Foam`, `Pro Stretch`, `Superflex neoprene`, `Silicone Stretch`, `Smooth Skin`, `partially recycled polyester`)
   - Construction terms (`GBS seams`, `fully welded seams`, `flatlock seams`, `bonded waistband`, `hidden split toe`, `chest zip`, `back zip`)
   - Named features (`lower leg patch pocket`, `back patch pocket`, `hammer loop`, `adjustable arch strap`, `adjustable drawcord`, `fixed waist`)
   - Fit terms (`regular fit`, `OG fit`, `core fit`, `performance fit`, `slim straight`)
   - Fabric finishes (`garment-washed`, `peached cotton twill`, `wave-washed`, `salt-washed`)

3. **For each extracted claim**, check whether the (normalized) phrase appears in the PDP intro or features list of any product on the source page. If not, the claim is unverified — flag the source slug and the claim.

4. **Sub-category sweep claims** ("our hoodies are made of...") need at least one PDP in the source whose features back the claim. If no hoodie PDP supports it, flag.

5. **Empty inventory check.** If the source's PDP crawl returned 0 products with usable descriptions (e.g., the PLP shows cross-product picks instead of category-matched inventory), flag the page itself: "PLP HAS NO MATCHING INVENTORY — copy describes intended category but live page does not actually list products of this type." Don't silently write copy as if the inventory exists.

**Output a per-piece findings line** that goes either into a tracking column ("Verifiability Audit") or into a separate audit file. Format:

- Fully verified: `All N product names + M specific claims verified.`
- Issues: `UNVERIFIED PRODUCT NAMES: [list]. UNVERIFIED CLAIMS (N): [tag: claim, claim; tag: claim].`
- Inventory issue: `PLP HAS NO MATCHING INVENTORY: [explanation].`

Reference approach: build a verification corpus per source from PDP descriptions + features + PLP product names, normalize hyphens and punctuation, then walk each high-risk claim pattern against it. Make it re-runnable and output findings to `audit_findings.json`.

**Common audit findings to expect (and what they tell you):**

- `Cotton-rich`, `cotton-blend` flagged → you wrote a generic descriptor instead of pulling the specific composition from the PDP ("100% Cotton" or "98% Cotton, 2% Elastane"). Fix: use the verbatim composition.
- `Garment-washed` flagged on a piece → you extrapolated from a sister PDP. Fix: only mention if it's in this product's PDP.
- Shortened product names flagged → use the verbatim PDP h1.
- `[Names-only audit: no PDP crawl for this source]` → the source was deliberately not deep-dived (sale/gift/branded/hub), so claims about specific products on those pages can't be verified from local data. Acceptable when the page type warranted skipping the PDP crawl.

### Step 6: Format as HTML

Ensure the copy is valid HTML:
- `<h2>` tag at the top with the primary keyword
- `<p>` tags for each paragraph (max 3 sentences)
- `<a href="https://...">` tags for internal links with absolute URLs
- No stray line breaks inside tags

### Step 7: Write to CSV

Place the finished copy in the Reworked Copy column and update metadata columns:
- **Copy word count** — word count of the copy (excluding HTML tags)
- **Internal links** — number of `<a>` links in the copy
- **Flags/notes** — any issues: 404 pages, low inventory (<5 products), keyword/content mismatches

## Batch Processing

For efficiency, process URLs in batches:

1. **Crawl in parallel** — run up to 5 Playwright crawls simultaneously using bash background processes. Wait for all to complete before writing copy.
2. **Write copy sequentially** — each piece needs the full CSV context to pick the right internal links, so write one at a time.
3. **Save after each batch** — don't wait until all URLs are done. Save the CSV after every 5–7 URLs so progress isn't lost.
4. **Report progress** — after each batch, show the user a summary table: URL slug, word count, link count, any flags.

## Edge Cases

- **404 pages**: Flag in the notes column, skip copy. Write `"404 PAGE — URL returns a 404 error. No products. Skipped copy."` in the flags.
- **Low inventory** (<5 products): Write the copy but flag it. Use language that reflects the limited selection rather than implying breadth.
- **Keyword/page mismatch**: If the keyword says "wetsuits" but the page only shows wetsuit boots, flag it and write copy that's honest about what's actually there.
- **Sale/clearance pages**: If the URL or keyword mentions "sale", lean into the value angle while still describing the products. General price language is allowed here — "full-price", "marked down", "markdowns", "spending full price" — since the whole point of a sale page is the deal. Still no specific dollar amounts. Don't be aggressively promotional — just acknowledge that these are marked-down items.
- **Collaboration collections**: If the page is a brand collaboration, research the partner brand briefly and weave in what makes the collab meaningful.

## Internal Linking Strategy

For each page, select the 3–4 most semantically related URLs from the CSV:

1. **Adjacent categories** — if writing about boardshorts, link to elastic waist boardshorts, hybrid shorts, rashguards
2. **Parent/child** — link from a sub-category to its parent or vice versa
3. **Complementary products** — items typically bought or used together (boardshorts + rashguards, snow pants + snow jackets)
4. **Sale pages** — if there's a sale version of this category, consider linking to it

Weave links naturally into the copy. Don't dump them all in the last paragraph — though ending with 1–2 links to related pages is fine as a natural transition.

## Output

The final CSV should contain all original columns plus:
- `Reworked Copy` — the HTML copy
- `Copy word count` — word count excluding HTML tags
- `Internal links` — count of `<a>` tags in the copy
- `Flags/notes` — any issues or context

Save the output CSV to the user's workspace folder.
