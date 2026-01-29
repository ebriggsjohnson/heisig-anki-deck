#!/usr/bin/env python3
"""Merge generated mainland/taiwan characters into the deck CSVs."""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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
    with open(ROOT / "data" / "generated_mainland.json", "r", encoding="utf-8") as f:
        mainland = json.load(f)
    with open(ROOT / "data" / "generated_taiwan.json", "r", encoding="utf-8") as f:
        taiwan = json.load(f)

    print(f"Loaded {len(mainland)} mainland, {len(taiwan)} taiwan entries")

    # Convert to CSV row format
    def to_row(e, deck):
        return {
            "character": e["char"],
            "keyword": e["keyword"],
            "RTH_number": "",
            "RSH_number": "",
            "RTK_number": "",
            "reading": e.get("reading", ""),
            "decomposition": "",
            "spatial": "",
            "ids": e.get("ids", ""),
            "components_detail": e.get("components_detail", ""),
            "deck": deck,
            "tags": e.get("tags", ""),
        }

    # Process RSH_deck.csv (simplified - add mainland chars)
    rsh_rows, rsh_chars, fieldnames = load_existing_csv(ROOT / "RSH_deck.csv")

    # Remove old generated entries (those with ML:: or TW:: tags)
    rsh_rows = [r for r in rsh_rows if not r.get("tags", "").startswith(("ML::", "TW::"))]
    rsh_chars = {r["character"]: i for i, r in enumerate(rsh_rows)}

    ml_added = 0
    for e in mainland:
        if e["char"] not in rsh_chars:
            rsh_rows.append(to_row(e, "ML"))
            ml_added += 1

    with open(ROOT / "RSH_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rsh_rows)
    print(f"RSH_deck.csv: {len(rsh_rows)} total ({ml_added} mainland added)")

    # Process RTH_deck.csv (traditional - add taiwan chars)
    rth_rows, rth_chars, fieldnames = load_existing_csv(ROOT / "RTH_deck.csv")

    # Remove old generated entries
    rth_rows = [r for r in rth_rows if not r.get("tags", "").startswith(("ML::", "TW::"))]
    rth_chars = {r["character"]: i for i, r in enumerate(rth_rows)}

    tw_added = 0
    for e in taiwan:
        if e["char"] not in rth_chars:
            rth_rows.append(to_row(e, "TW"))
            tw_added += 1

    with open(ROOT / "RTH_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rth_rows)
    print(f"RTH_deck.csv: {len(rth_rows)} total ({tw_added} taiwan added)")

    # Process Ultimate_deck.csv (all combined)
    ult_rows, ult_chars, fieldnames = load_existing_csv(ROOT / "Ultimate_deck.csv")

    # Remove old generated entries
    ult_rows = [r for r in ult_rows if not r.get("tags", "").startswith(("ML::", "TW::"))]
    ult_chars = {r["character"]: i for i, r in enumerate(ult_rows)}

    # Add mainland
    for e in mainland:
        if e["char"] not in ult_chars:
            ult_rows.append(to_row(e, "ML"))
            ult_chars[e["char"]] = len(ult_rows) - 1

    # Add taiwan (skip if already in from mainland)
    for e in taiwan:
        if e["char"] not in ult_chars:
            ult_rows.append(to_row(e, "TW"))

    with open(ROOT / "Ultimate_deck.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(ult_rows)
    print(f"Ultimate_deck.csv: {len(ult_rows)} total")


if __name__ == "__main__":
    main()
