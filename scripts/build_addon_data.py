#!/usr/bin/env python3
"""Build heisig_data.json from Ultimate_deck.csv for the Anki add-on and web demo."""

import csv
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
CSV_PATH = os.path.join(PROJECT_DIR, "Ultimate_deck.csv")
ADDON_OUT = os.path.join(PROJECT_DIR, "heisig_addon", "data", "heisig_data.json")
DOCS_OUT = os.path.join(PROJECT_DIR, "docs", "heisig_data.json")


def build():
    data = {}
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            char = row["character"].strip()
            if not char:
                continue
            entry = {
                "keyword": row.get("keyword", "").strip(),
                "reading": row.get("reading", "").strip(),
                "decomposition": row.get("decomposition", "").strip(),
                "spatial": row.get("spatial", "").strip(),
                "components_detail": row.get("components_detail", "").strip(),
                "RTH_number": row.get("RTH_number", "").strip(),
                "RSH_number": row.get("RSH_number", "").strip(),
                "RTK_number": row.get("RTK_number", "").strip(),
                "tags": row.get("tags", "").strip(),
            }
            data[char] = entry

    for out_path in [ADDON_OUT, DOCS_OUT]:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)

    print(f"Built heisig_data.json with {len(data)} entries")
    print(f"  -> {ADDON_OUT}")
    print(f"  -> {DOCS_OUT}")


if __name__ == "__main__":
    build()
