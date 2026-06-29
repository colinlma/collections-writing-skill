#!/usr/bin/env python3
"""
Deterministic claim verifier for PLP copy. Vertical-agnostic.

Builds a normalized verification corpus from the PDP crawls of a PLP, then checks
each piece of copy for high-risk factual claims that do NOT appear anywhere in
that PLP's corpus. Anything not found is flagged as UNVERIFIED — it is either a
hallucination or a feature extrapolated from a sibling product's PDP.

It does NOT rely on a per-vertical vocabulary list. Instead it extracts the kinds
of tokens that ARE specific, checkable claims in any product category, then
verifies each against the corpus:

  1. Numeric specs    — measurements/units (mm, cm, g, kg, oz, ml, l, w, v, mah,
                        hz, gb, tb, mph, psi, ...), percentages ("98% cotton",
                        "100% juice"), and number-hyphen compounds ("40-hour",
                        "12-pack", "4-way").
  2. Hyphenated descriptors — "water-resistant", "cold-pressed", "noise-cancelling",
                        "dishwasher-safe", "garment-washed" (minus generic
                        marketing fluff via a small stoplist).
  3. Acronyms         — "LED", "USB", "ANC", "GBS", "SPF", "OLED" (minus common
                        non-product acronyms via a stoplist).

This is the deterministic backbone of the validate -> fix loop. It errs toward
flagging candidates; a validator subagent prunes false positives and adds the
semantic checks a regex can't make (product-name accuracy, over-claims like
"short and long sleeve", sub-category sweeps, empty inventory).

For domain-specific multiword terms a regex won't catch on its own ("GBS seams",
"regular fit", "grain-fed", "single-origin"), add them with --patterns (see
patterns.example.txt). The acronym/hyphen/spec extractors already cover most of
what those lists used to.

Usage:
    python3 scripts/verify_claims.py <corpus.json> <copy.json> [--patterns patterns.txt] [--output findings.json]

corpus.json — built from the crawls, keyed by PLP slug:
    { "<plp-slug>": { "names": ["Full Verbatim Product Name", ...],
                       "text":  "all PDP descriptions + features concatenated" } }

copy.json   — the written copy, one object per PLP:
    [ {"slug": "<plp-slug>", "copy": "<h2>...</h2>..."}, ... ]

patterns.txt (OPTIONAL) — extra claim signals, one per line:
    lines beginning "re:" are regexes; everything else is a literal phrase.

Output: findings JSON (also printed as a summary). Exit code is always 0 — this
is a report, not a gate; the loop decides when to stop.
"""

import json
import re
import sys
import argparse


# --- Vertical-agnostic numeric-spec patterns ---------------------------------
UNIT = (r"(?:mm|cm|m|in|inch|inches|ft|gsm|g|kg|mg|lb|lbs|oz|ml|l|gal|"
        r"w|kw|v|mah|wh|hz|khz|mhz|ghz|db|kb|mb|gb|tb|mp|fps|psi|mph|rpm|cc|k)")
SPEC_REGEXES = [
    r"\d+\s?/\s?\d+\s?mm",                 # 4/3mm
    r"\d+(?:\.\d+)?\s?" + UNIT + r"\b",    # 180g, 5mm, 40w, 5.3ghz, 256gb
    r'\d+(?:\.\d+)?\s?"',                  # 20" diagonal
    r"\d+(?:\.\d+)?\s?%\s?[a-z]",          # 98% cotton, 100% juice
    r"\b\d+(?:\.\d+)?\s?-\s?[a-z]{2,}\b",  # 40-hour, 12-pack, 4-way, 3-piece
    r"\b\d+\s?x\s?\d+\b",                  # 1920x1080, 12x18
]

# Hyphenated marketing fluff that is NOT a checkable product claim.
COMPOUND_STOP = {
    "high-quality", "top-quality", "premium-quality", "best-selling", "easy-to-use",
    "must-have", "well-made", "brand-new", "ready-to-use", "hassle-free", "top-notch",
    "one-of-a-kind", "state-of-the-art", "time-tested", "hand-picked", "family-owned",
    "money-back", "in-stock", "out-of-stock", "add-on", "free-shipping", "long-term",
    "short-term", "day-to-day", "head-to-toe", "go-to", "so-called", "up-to-date",
    "full-price", "best-in-class", "all-new", "down-to-earth",
}

# Acronyms that are not product/material/feature claims.
ACRONYM_STOP = {
    "PLP", "PDP", "URL", "CSV", "HTML", "SEO", "AEO", "FAQ", "USA", "UK", "EU", "DIY",
    "AKA", "FYI", "ASAP", "OK", "ID", "AM", "PM", "VS", "OR", "AND", "THE", "NEW",
    "SALE", "SHOP", "PDF", "API", "CTA", "KW",
}

COMPOUND_RE = re.compile(r"\b[a-z]{3,}-[a-z]{3,}(?:-[a-z]{3,})?\b")
ACRONYM_RE = re.compile(r"\b[A-Z]{2,}\b")


def normalize(s: str) -> str:
    s = s.lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s


def loosen(s: str) -> str:
    """Hyphen-insensitive form so 'water-resistant' matches 'water resistant'."""
    return re.sub(r"\s+", " ", normalize(s).replace("-", " ")).strip()


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def load_extra_patterns(path):
    regexes, phrases = [], []
    if not path:
        return regexes, phrases
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("re:"):
                regexes.append(line[3:].strip())
            else:
                phrases.append(line)
    return regexes, phrases


def extract_claims(copy_html: str, extra_regexes, extra_phrases):
    """Return the set of distinct candidate claim strings present in the copy."""
    raw_text = strip_html(copy_html)
    norm = normalize(raw_text)
    found = set()

    # 1. Numeric specs (+ any user regexes), matched on normalized text.
    for rx in SPEC_REGEXES + extra_regexes:
        for m in re.finditer(rx, norm):
            found.add(m.group(0).strip())

    # 2. Hyphenated descriptors (lowercased), minus marketing fluff.
    for m in COMPOUND_RE.finditer(norm):
        token = m.group(0)
        if token not in COMPOUND_STOP:
            found.add(token)

    # 3. Acronyms, taken from the RAW (case-preserving) text, minus stoplist.
    for m in ACRONYM_RE.finditer(raw_text):
        token = m.group(0)
        if token not in ACRONYM_STOP:
            found.add(token.lower())

    # 4. User-supplied literal phrases (domain-specific multiword terms).
    for ph in extra_phrases:
        if normalize(ph) in norm:
            found.add(normalize(ph))

    return found


def main():
    ap = argparse.ArgumentParser(description="Verify PLP copy claims against the PDP corpus (vertical-agnostic).")
    ap.add_argument("corpus_json")
    ap.add_argument("copy_json")
    ap.add_argument("--patterns", default=None, help="Optional extra claim signals (regex/literal lines).")
    ap.add_argument("--output", default=None, help="Write findings JSON here.")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus_json, encoding="utf-8"))
    pieces = json.load(open(args.copy_json, encoding="utf-8"))
    extra_regexes, extra_phrases = load_extra_patterns(args.patterns)

    # Pre-normalize corpus (strict + loose).
    norm_corpus, loose_corpus = {}, {}
    for slug, c in corpus.items():
        blob = " ".join([c.get("text", "")] + c.get("names", []))
        norm_corpus[slug] = normalize(blob)
        loose_corpus[slug] = loosen(blob)

    findings = []
    for piece in pieces:
        slug = piece.get("slug", "")
        rec = {"slug": slug, "unverified_claims": [], "status": ""}

        if slug not in norm_corpus:
            rec["status"] = "NO_CORPUS"
            rec["note"] = "No PDP corpus for this slug — cannot verify. Crawl its PDPs or mark names-only."
            findings.append(rec)
            continue

        claims = extract_claims(piece.get("copy", ""), extra_regexes, extra_phrases)
        cn, cl = norm_corpus[slug], loose_corpus[slug]
        for claim in sorted(claims):
            if claim in cn or loosen(claim) in cl:
                continue
            rec["unverified_claims"].append(claim)

        rec["status"] = "CLEAN" if not rec["unverified_claims"] else "UNVERIFIED"
        findings.append(rec)

    if args.output:
        json.dump(findings, open(args.output, "w", encoding="utf-8"), indent=2)

    total_unverified = sum(len(f["unverified_claims"]) for f in findings)
    clean = sum(1 for f in findings if f["status"] == "CLEAN")
    no_corpus = sum(1 for f in findings if f["status"] == "NO_CORPUS")
    print("Verify Claims Report")
    print("=" * 56)
    print(f"Pieces: {len(pieces)} | clean: {clean} | "
          f"with unverified claims: {sum(1 for f in findings if f['status']=='UNVERIFIED')} | "
          f"no corpus: {no_corpus}")
    print(f"Total unverified claims (candidates for the validator to confirm): {total_unverified}")
    for f in findings:
        if f["status"] == "UNVERIFIED":
            print(f"  [{f['slug']}] UNVERIFIED: {', '.join(f['unverified_claims'])}")
        elif f["status"] == "NO_CORPUS":
            print(f"  [{f['slug']}] NO CORPUS")

    sys.exit(0)


if __name__ == "__main__":
    main()
