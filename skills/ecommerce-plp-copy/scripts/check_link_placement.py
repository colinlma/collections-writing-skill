#!/usr/bin/env python3
"""
Deterministic link-placement checker for PLP footer copy (Step 5c QA loop).

Parses each piece's HTML and flags the OBJECTIVE placement problems a regex can
catch, so a fixer subagent can concentrate on the judgment calls. It intentionally
does NOT decide whether an anchor sits on a naturally-occurring word — that needs a
reader (the QA subagent). Think of this as the backbone pre-pass, mirroring
verify_claims.py in the verifiability loop.

Usage:
    python3 scripts/check_link_placement.py copy.json [--output link_findings.json]
                                                      [--min-links 2] [--max-links 4]

Input (copy.json): a JSON array of {"slug": "...", "copy": "<h2>...</h2><p>...</p>"}.

Output: JSON array of findings, one object per piece that has at least one issue:
    {
      "slug": "...",
      "total_links": 3,
      "links_in_last_p": 3,
      "paragraphs": 3,
      "findings": ["closing_dump", "generic_anchor:shop now"],
      "anchors": ["boardshorts", "shop now", "rashguards"]
    }
Pieces with no issues are omitted from the array (a clean run returns []).
Exit code is 0 whether or not findings exist — findings are data, not errors.
"""

import json
import re
import sys
import argparse

# Anchor text that carries no category meaning — a link on these wastes the anchor.
GENERIC_ANCHORS = {
    "shop now", "shop", "click here", "here", "learn more", "read more",
    "see more", "view", "view more", "browse", "browse now", "this page",
    "shop the collection", "explore", "explore now", "check it out",
    "check out", "see all", "shop all", "find out more", "more",
}


def paragraphs(html):
    """Return a list of the inner HTML of each <p>...</p> block, in order."""
    return re.findall(r"<p\b[^>]*>(.*?)</p>", html, re.S | re.I)


def anchors(fragment):
    """Return [(href, anchor_text)] for every <a> in an HTML fragment."""
    out = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]*)"[^>]*>(.*?)</a>', fragment, re.S | re.I):
        text = re.sub(r"<[^>]+>", "", m.group(2))
        out.append((m.group(1), re.sub(r"\s+", " ", text).strip()))
    return out


def visible(fragment):
    """Plain visible text of a fragment (tags stripped)."""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", fragment)).strip()


def sentences_in_paragraph(inner):
    """Split one paragraph's inner HTML into sentence spans (tags preserved), on
    . ? ! followed by whitespace. Paragraph boundaries are handled by the caller —
    a `</p><p>` join has no space after the period, so splitting per-paragraph is
    what keeps two separate closing sentences from being counted as one."""
    parts = re.split(r"(?<=[.?!])\s+", inner)
    return [p for p in parts if p.strip()]


def max_links_per_sentence(html):
    """Largest number of <a> tags found in any single sentence, counted per
    paragraph so sentences never bleed across `<p>` boundaries. Two links in one
    sentence is common natural prose ("it runs across swim, dresses, and tops");
    the loud signal is 3+ in a sentence, i.e. an explicit "A, B, and C" list."""
    best = 0
    for inner in paragraphs(html):
        for s in sentences_in_paragraph(inner):
            best = max(best, len(anchors(s)))
    return best


def check_piece(slug, html, min_links, max_links):
    ps = paragraphs(html)
    all_links = anchors(html)
    last_p_links = anchors(ps[-1]) if ps else []
    findings = []

    n = len(all_links)
    if n < min_links:
        findings.append(f"too_few_links:{n}")
    if n > max_links:
        findings.append(f"too_many_links:{n}")

    # Closing dump: the final paragraph carries a PILE of links (3+). A closing
    # paragraph with two links spread across separate prose sentences is fine —
    # short category pages often have few other natural anchor spots — so the
    # trigger is 3+, not 2+. Links jammed into ONE sentence are caught below.
    if ps and len(last_p_links) >= 3:
        findings.append("closing_dump")

    # Stacked links: 3+ links crammed into a single sentence anywhere in the piece.
    # This is the explicit "Browse A, B, and C" list. Two links in one sentence is
    # left for the QA subagent to judge — it's usually fine natural prose, so the
    # deterministic layer only fires on the unambiguous 3+ case to stay high-precision.
    stack = max_links_per_sentence(html)
    if stack >= 3:
        findings.append(f"stacked_in_one_sentence:{stack}")

    # Clustered: every link in the piece lives in one paragraph (and there are 2+).
    if n >= 2 and len(ps) >= 2:
        per_p = [len(anchors(p)) for p in ps]
        if max(per_p) == n:
            findings.append("clustered_single_paragraph")

    # Generic (non-descriptive) anchor text.
    for _href, text in all_links:
        if text.lower() in GENERIC_ANCHORS:
            findings.append(f"generic_anchor:{text}")

    # Orphaned closing: the last paragraph is essentially only links (little/no prose).
    if ps and last_p_links:
        vis = visible(ps[-1])
        anchor_chars = sum(len(t) for _h, t in last_p_links)
        # if the paragraph's visible text is almost entirely anchor text, it's a link list
        if len(vis) > 0 and anchor_chars / max(len(vis), 1) > 0.7 and len(last_p_links) >= 2:
            findings.append("orphaned_closing_link_list")

    if not findings:
        return None
    return {
        "slug": slug,
        "total_links": n,
        "links_in_last_p": len(last_p_links),
        "paragraphs": len(ps),
        "findings": sorted(set(findings)),
        "anchors": [t for _h, t in all_links],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("copy_json", help="JSON array of {slug, copy}")
    ap.add_argument("--output", help="write findings JSON here (also prints a summary)")
    ap.add_argument("--min-links", type=int, default=2)
    ap.add_argument("--max-links", type=int, default=4)
    args = ap.parse_args()

    pieces = json.load(open(args.copy_json, encoding="utf-8"))
    findings = []
    for p in pieces:
        f = check_piece(p["slug"], p.get("copy", ""), args.min_links, args.max_links)
        if f:
            findings.append(f)

    if args.output:
        json.dump(findings, open(args.output, "w"), indent=1)

    clean = len(pieces) - len(findings)
    print(f"Checked {len(pieces)} pieces: {clean} clean, {len(findings)} with placement findings")
    for f in findings:
        print(f"  [{f['slug']}] {', '.join(f['findings'])} "
              f"(links={f['total_links']}, last_p={f['links_in_last_p']})")


if __name__ == "__main__":
    main()
