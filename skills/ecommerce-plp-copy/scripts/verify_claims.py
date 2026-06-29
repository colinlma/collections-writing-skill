#!/usr/bin/env python3
"""
Deterministic claim verifier for PLP copy.

Builds a normalized verification corpus from the PDP crawls of a PLP, then checks
each piece of copy for high-risk factual claims (numeric specs, material names,
construction terms, finishes) that do NOT appear anywhere in that PLP's corpus.
Anything not found is flagged as UNVERIFIED — it is either a hallucination or a
feature extrapolated from a sibling product's PDP.

This is the deterministic backbone of the validate -> fix loop. A validator
subagent layers semantic checks (product-name accuracy, over-claims like
"short and long sleeve", sub-category sweeps, empty inventory) on top of it.

Usage:
    python3 scripts/verify_claims.py <corpus.json> <copy.json> [--patterns patterns.txt] [--output findings.json]

corpus.json  — built from the crawls, keyed by PLP slug:
    {
      "<plp-slug>": {
        "names": ["Full Verbatim Product Name", ...],   # PLP titles + PDP H1s
        "text":  "all PDP descriptions + features concatenated"
      },
      ...
    }

copy.json    — the written copy, one object per PLP:
    [ {"slug": "<plp-slug>", "copy": "<h2>...</h2>..."}, ... ]

patterns.txt — OPTIONAL override of the high-risk claim patterns (one per line):
    lines beginning "re:" are treated as regexes, everything else as a literal
    phrase. If omitted, an apparel-oriented default set is used — REPLACE IT for
    non-apparel verticals (electronics, home goods, etc.).

Output: findings JSON (also printed as a summary). Exit code is always 0 — this
is a report, not a gate; the loop decides when to stop.
"""

import json
import re
import sys
import argparse


# Numeric-spec regexes are vertical-agnostic (a measurement is a measurement).
DEFAULT_SPEC_REGEXES = [
    r"\d+\s?/\s?\d+\s?mm",          # 4/3mm
    r"\d+(\.\d+)?\s?mm\b",          # 5mm
    r"\d+\s?g\b",                   # 180g
    r"\d+\s?gsm\b",                 # 220gsm
    r"\d+\s?-?\s?way stretch",      # 4-way stretch
    r'\d+(\.\d+)?\s?"',             # 20" outseam
    r"\d+\s?-?\s?inch",             # 18-inch
    r"\d+%\s?[a-z]",                # 98% cotton
    r"upf\s?\d+",                   # UPF 50
]

# Apparel-oriented vocabulary default. Replace via --patterns for other verticals.
DEFAULT_PHRASES = [
    "garment-washed", "garment washed", "peached", "wave-washed", "salt-washed",
    "gbs seams", "fully welded", "flatlock", "bonded waistband", "hidden split toe",
    "chest zip", "back zip", "blind stitch", "taped seams",
    "4-way stretch", "2-way stretch", "smart foam", "graphene", "superflex",
    "silicone stretch", "smooth skin", "pro stretch", "recycled polyester",
    "merino", "organic cotton", "ripstop", "gore-tex", "primaloft", "cordura",
    "regular fit", "slim straight", "og fit", "core fit", "performance fit", "relaxed fit",
    "cotton-rich", "cotton-blend",
]


def normalize(s: str) -> str:
    s = s.lower()
    s = s.replace("’", "'").replace("‘", "'")
    s = s.replace("–", "-").replace("—", "-")
    s = re.sub(r"\s+", " ", s)
    return s


def strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def load_patterns(path):
    if not path:
        return DEFAULT_SPEC_REGEXES, DEFAULT_PHRASES
    regexes, phrases = [], []
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


def find_claims(copy_text_norm, spec_regexes, phrases):
    """Return the set of distinct claim strings present in the copy."""
    found = set()
    for rx in spec_regexes:
        for m in re.finditer(rx, copy_text_norm):
            found.add(m.group(0).strip())
    for ph in phrases:
        if normalize(ph) in copy_text_norm:
            found.add(normalize(ph))
    return found


def main():
    ap = argparse.ArgumentParser(description="Verify PLP copy claims against the PDP corpus.")
    ap.add_argument("corpus_json")
    ap.add_argument("copy_json")
    ap.add_argument("--patterns", default=None, help="Optional patterns override file.")
    ap.add_argument("--output", default=None, help="Write findings JSON here.")
    args = ap.parse_args()

    corpus = json.load(open(args.corpus_json, encoding="utf-8"))
    pieces = json.load(open(args.copy_json, encoding="utf-8"))
    spec_regexes, phrases = load_patterns(args.patterns)

    # Pre-normalize corpus
    norm_corpus = {}
    for slug, c in corpus.items():
        blob = " ".join([c.get("text", "")] + c.get("names", []))
        norm_corpus[slug] = normalize(blob)

    findings = []
    for piece in pieces:
        slug = piece.get("slug", "")
        copy_norm = normalize(strip_html(piece.get("copy", "")))
        corpus_norm = norm_corpus.get(slug)

        rec = {"slug": slug, "unverified_claims": [], "status": ""}
        if corpus_norm is None:
            rec["status"] = "NO_CORPUS"
            rec["note"] = "No PDP corpus for this slug — cannot verify. Crawl its PDPs or mark as names-only."
            findings.append(rec)
            continue

        for claim in sorted(find_claims(copy_norm, spec_regexes, phrases)):
            if claim not in corpus_norm:
                rec["unverified_claims"].append(claim)

        rec["status"] = "CLEAN" if not rec["unverified_claims"] else "UNVERIFIED"
        findings.append(rec)

    if args.output:
        json.dump(findings, open(args.output, "w", encoding="utf-8"), indent=2)

    total_unverified = sum(len(f["unverified_claims"]) for f in findings)
    no_corpus = sum(1 for f in findings if f["status"] == "NO_CORPUS")
    clean = sum(1 for f in findings if f["status"] == "CLEAN")
    print(f"Verify Claims Report")
    print(f"{'='*56}")
    print(f"Pieces: {len(pieces)} | clean: {clean} | with unverified claims: "
          f"{sum(1 for f in findings if f['status']=='UNVERIFIED')} | no corpus: {no_corpus}")
    print(f"Total unverified claims: {total_unverified}")
    for f in findings:
        if f["status"] == "UNVERIFIED":
            print(f"  [{f['slug']}] UNVERIFIED: {', '.join(f['unverified_claims'])}")
        elif f["status"] == "NO_CORPUS":
            print(f"  [{f['slug']}] NO CORPUS")

    # Always exit 0 — this is a report; the loop decides when to stop.
    sys.exit(0)


if __name__ == "__main__":
    main()
