#!/usr/bin/env python3
"""Merge generated traditional characters into the deck CSVs.

Simplified characters are saved separately to data/simplified_additions.csv.
Only TC::A and TC::B are added to the main decks.
"""

import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# IDS operator labels
IDS_LABELS = {
    "⿰": "left-right",
    "⿱": "top-bottom",
    "⿲": "left-mid-right",
    "⿳": "top-mid-bottom",
    "⿴": "surround",
    "⿵": "surround-open-bottom",
    "⿶": "surround-open-top",
    "⿷": "surround-open-right",
    "⿸": "top-left-wrap",
    "⿹": "top-right-wrap",
    "⿺": "bottom-left-wrap",
    "⿻": "overlaid",
}


def parse_spatial(ids_raw):
    """Extract spatial description from IDS string."""
    # Strip source annotations like ^...$(GHTJKP)
    ids = re.sub(r'^\^', '', ids_raw)
    ids = re.sub(r'\$\([A-Z]+\)$', '', ids)

    if not ids:
        return ""

    # Find first IDS operator
    for char in ids:
        if char in IDS_LABELS:
            return f"{char} ({IDS_LABELS[char]})"
    return ""


def parse_decomposition(components_detail):
    """Extract decomposition from components_detail."""
    if not components_detail:
        return ""

    # Parse "亠 = top hat, 凶 = cruel" -> "top hat + cruel"
    keywords = []
    for part in components_detail.split(", "):
        if " = " in part:
            keyword = part.split(" = ", 1)[1]
            keywords.append(keyword)

    return " + ".join(keywords)


def load_existing_csv(path):
    """Load CSV as list of dicts, keyed by character."""
    chars = {}
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            char = row["character"]
            chars[char] = len(rows)
            rows.append(dict(row))
    return rows, chars, fieldnames


def main():
    # Load generated data
    with open(ROOT / "data" / "generated_simplified.json", "r", encoding="utf-8") as f:
        simplified = json.load(f)
    with open(ROOT / "data" / "generated_traditional.json", "r", encoding="utf-8") as f:
        traditional = json.load(f)

    print(f"Loaded {len(simplified)} simplified, {len(traditional)} traditional entries")

    # Convert to CSV row format with decomposition and spatial filled in
    def to_row(e, deck):
        ids_raw = e.get("ids", "")
        components = e.get("components_detail", "")
        # Clean IDS for storage
        ids_clean = re.sub(r'^\^', '', ids_raw)
        ids_clean = re.sub(r'\$\([A-Z]+\)$', '', ids_clean)
        return {
            "character": e["char"],
            "keyword": e["keyword"],
            "RTH_number": "",
            "RSH_number": "",
            "RTK_number": "",
            "reading": e.get("reading", ""),
            "decomposition": parse_decomposition(components),
            "spatial": parse_spatial(ids_raw),
            "ids": ids_clean,
            "components_detail": components,
            "deck": deck,
            "tags": e.get("tags", ""),
        }

    # Save simplified to separate file (not added to main decks)
    ml_fieldnames = ["character", "keyword", "reading", "decomposition", "spatial",
                     "ids", "components_detail", "tags"]
    ml_rows = [to_row(e, "SC") for e in simplified]
    with open(ROOT / "data" / "simplified_additions.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ml_fieldnames)
        writer.writeheader()
        for row in ml_rows:
            writer.writerow({k: row[k] for k in ml_fieldnames})
    print(f"data/simplified_additions.csv: {len(ml_rows)} simplified chars saved separately")

    # Process RSH_deck.csv (simplified - Heisig + SC::L1 + SC::L2)
    rsh_rows, rsh_chars, fieldnames = load_existing_csv(ROOT / "RSH_deck.csv")

    # Remove old generated entries (those with SC:: or TC:: tags)
    rsh_rows = [r for r in rsh_rows if not r.get("tags", "").startswith(("SC::", "TC::", "ML::", "TW::"))]
    rsh_chars = {r["character"]: i for i, r in enumerate(rsh_rows)}

    # Add SC::L1 and SC::L2 (practical simplified chars)
    sc_added = 0
    for e in simplified:
        tags = e.get("tags", "")
        if tags in ("SC::L1", "SC::L2") and e["char"] not in rsh_chars:
            rsh_rows.append(to_row(e, "SC"))
            rsh_chars[e["char"]] = len(rsh_rows) - 1
            sc_added += 1

    with open(ROOT / "RSH_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rsh_rows)
    print(f"RSH_deck.csv: {len(rsh_rows)} total (Heisig + {sc_added} SC::L1/L2)")

    # Process RTH_deck.csv (traditional - add traditional A/B chars)
    rth_rows, rth_chars, fieldnames = load_existing_csv(ROOT / "RTH_deck.csv")

    # Remove old generated entries
    rth_rows = [r for r in rth_rows if not r.get("tags", "").startswith(("SC::", "TC::", "ML::", "TW::"))]
    rth_chars = {r["character"]: i for i, r in enumerate(rth_rows)}

    tw_added = 0
    for e in traditional:
        if e["char"] not in rth_chars:
            rth_rows.append(to_row(e, "TC"))
            tw_added += 1

    with open(ROOT / "RTH_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rth_rows)
    print(f"RTH_deck.csv: {len(rth_rows)} total ({tw_added} traditional A/B added)")

    # Process Ultimate_deck.csv (Heisig + SC::L1/L2 + TC::A/B)
    ult_rows, ult_chars, fieldnames = load_existing_csv(ROOT / "Ultimate_deck.csv")

    # Remove old generated entries
    ult_rows = [r for r in ult_rows if not r.get("tags", "").startswith(("SC::", "TC::", "ML::", "TW::"))]
    ult_chars = {r["character"]: i for i, r in enumerate(ult_rows)}

    # Add SC::L1 and SC::L2
    for e in simplified:
        tags = e.get("tags", "")
        if tags in ("SC::L1", "SC::L2") and e["char"] not in ult_chars:
            ult_rows.append(to_row(e, "SC"))
            ult_chars[e["char"]] = len(ult_rows) - 1

    # Add traditional A/B
    for e in traditional:
        if e["char"] not in ult_chars:
            ult_rows.append(to_row(e, "TC"))

    with open(ROOT / "Ultimate_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ult_rows)
    print(f"Ultimate_deck.csv: {len(ult_rows)} total (Heisig + SC::L1/L2 + TC::A/B)")


if __name__ == "__main__":
    main()
