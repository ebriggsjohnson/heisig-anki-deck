"""Build .apkg Anki decks with embedded primitive images.

Reuses the card-building pipeline from build_decks.py, then packages
everything into .apkg files using genanki. Non-unicode primitives (囧)
are rendered as <img> tags referencing the PNGs from data/primitive_images/.

Outputs:
  RTH_deck.apkg  — Traditional Hanzi + primitives
  RSH_deck.apkg  — Simplified Hanzi + primitives
  RTK_deck.apkg  — Kanji + primitives
  Ultimate_deck.apkg — All 3 merged
"""

import csv
import json
import os
import re
import sys
from pathlib import Path

import genanki

ROOT = Path(__file__).resolve().parent.parent
PRIM_IMAGES_DIR = ROOT / "data" / "primitive_images"
MANIFEST_PATH = PRIM_IMAGES_DIR / "manifest.json"

# ── Load primitive image manifest ──────────────────────────────────────
prim_manifest = {}
if MANIFEST_PATH.exists():
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        prim_manifest = json.load(f)

# Build keyword -> image filename lookup
# Also need: 囧 character string -> keyword mapping from rsh_parsed.json
RSH_JSON = ROOT / "data" / "rsh_parsed.json"
with open(RSH_JSON, "r", encoding="utf-8") as f:
    rsh = json.load(f)

jiong_char_to_keyword = {}  # e.g. "囧只－口" -> "animal legs"
jiong_keywords = set()
for p in rsh["primitives"]:
    if "囧" in p["character"]:
        jiong_char_to_keyword[p["character"]] = p["keyword"]
        jiong_keywords.add(p["keyword"])


def prim_img_tag(keyword):
    """Return an <img> tag for a primitive keyword, or None."""
    if keyword in prim_manifest:
        entry = prim_manifest[keyword]
        fname = entry["file"]
        approx = " ≈" if entry.get("approximate") else ""
        return f'<img src="{fname}">{approx}'
    return None


def char_display(char):
    """Return HTML to display a character, using <img> for 囧 primitives."""
    if "囧" in char:
        kw = jiong_char_to_keyword.get(char)
        if kw:
            tag = prim_img_tag(kw)
            if tag:
                return tag
    return char


def enrich_components_detail(detail_str):
    """Replace 囧 characters in components_detail with img tags."""
    if not detail_str:
        return detail_str
    parts = detail_str.split(", ")
    enriched = []
    for part in parts:
        if "=" in part:
            ch, name = part.split(" = ", 1)
            ch = ch.strip()
            if "囧" in ch:
                kw = jiong_char_to_keyword.get(ch)
                if kw:
                    tag = prim_img_tag(kw)
                    if tag:
                        enriched.append(f'{tag} = {name}')
                        continue
            enriched.append(part)
        else:
            enriched.append(part)
    return ", ".join(enriched)


# ── Anki model definition ─────────────────────────────────────────────
# Stable random IDs (generated once, kept constant for model/deck identity)
MODEL_ID = 1607392319
DECK_IDS = {
    "RTH": 1607392320,
    "RSH": 1607392321,
    "RTK": 1607392322,
    "Ultimate": 1607392323,
}

CARD_CSS = """\
.card {
  font-family: "Hiragino Sans", "PingFang SC", "Noto Sans CJK", "MS Gothic", sans-serif;
  font-size: 18px;
  text-align: center;
  color: #333;
  background-color: #fafafa;
  padding: 20px;
}
.character {
  font-size: 120px;
  line-height: 1.2;
  margin: 20px 0;
  color: #000;
}
.character img {
  height: 100px;
  vertical-align: middle;
}
.keyword {
  font-size: 32px;
  font-weight: bold;
  margin: 10px 0;
  color: #1a1a2e;
}
.reading {
  font-size: 20px;
  color: #555;
  margin: 8px 0;
}
.decomposition {
  font-size: 18px;
  color: #666;
  margin: 8px 0;
}
.components {
  font-size: 16px;
  color: #777;
  margin: 8px 0;
}
.components img {
  height: 24px;
  vertical-align: middle;
}
.spatial {
  font-size: 14px;
  color: #999;
  margin: 4px 0;
}
.tags {
  font-size: 12px;
  color: #aaa;
  margin-top: 16px;
}
.numbers {
  font-size: 13px;
  color: #888;
  margin: 4px 0;
}
.approx-note {
  font-size: 11px;
  color: #c0392b;
}
"""

FRONT_TEMPLATE = """\
<div class="character">{{Character}}</div>
{{#Tags}}<div class="tags">{{Tags}}</div>{{/Tags}}
"""

BACK_TEMPLATE = """\
{{FrontSide}}
<hr>
<div class="keyword">{{Keyword}}</div>
{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}
{{#Decomposition}}<div class="decomposition">{{Decomposition}}</div>{{/Decomposition}}
{{#ComponentsDetail}}<div class="components">{{ComponentsDetail}}</div>{{/ComponentsDetail}}
{{#Spatial}}<div class="spatial">{{Spatial}}</div>{{/Spatial}}
{{#Numbers}}<div class="numbers">{{Numbers}}</div>{{/Numbers}}
"""

heisig_model = genanki.Model(
    MODEL_ID,
    "Heisig Primitives + Characters",
    fields=[
        {"name": "Character"},
        {"name": "Keyword"},
        {"name": "Reading"},
        {"name": "Decomposition"},
        {"name": "ComponentsDetail"},
        {"name": "Spatial"},
        {"name": "Numbers"},
        {"name": "Tags"},
        {"name": "SortField"},
    ],
    templates=[
        {
            "name": "Recognition",
            "qfmt": FRONT_TEMPLATE,
            "afmt": BACK_TEMPLATE,
        },
    ],
    css=CARD_CSS,
    sort_field_index=8,  # SortField
)


def build_note(card):
    """Build a genanki Note from a card dict."""
    char = card.get("character", "")
    character_html = char_display(char)

    # Build numbers string
    nums = []
    for book in ["RTH", "RSH", "RTK"]:
        n = card.get(f"{book}_number", "")
        if n:
            nums.append(f"{book} #{n}")
    numbers_str = " · ".join(nums)

    # Enrich components_detail with img tags
    components = enrich_components_detail(card.get("components_detail", ""))

    # Sort field: prefer RSH number, then RTH, then RTK, then keyword
    sort_val = ""
    for book in ["RSH", "RTH", "RTK"]:
        n = card.get(f"{book}_number", "")
        if n:
            sort_val = f"{book}_{int(n):05d}"
            break
    if not sort_val:
        sort_val = f"ZZZ_{card.get('keyword', char)}"

    tags_str = card.get("tags", "")

    note = genanki.Note(
        model=heisig_model,
        fields=[
            character_html,
            card.get("keyword", ""),
            card.get("reading", ""),
            card.get("decomposition", ""),
            components,
            card.get("spatial", ""),
            numbers_str,
            tags_str,
            sort_val,
        ],
        tags=tags_str.split() if tags_str else [],
    )
    return note


def load_csv_cards(csv_path):
    """Load card dicts from a CSV deck file."""
    cards = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cards.append(dict(row))
    return cards


def collect_media_files():
    """Collect all primitive image files that need to be embedded."""
    media = []
    if PRIM_IMAGES_DIR.exists():
        for entry in prim_manifest.values():
            img_path = PRIM_IMAGES_DIR / entry["file"]
            if img_path.exists():
                media.append(str(img_path))
    return media


def build_deck(name, csv_path, output_path):
    """Build an .apkg file from a CSV deck."""
    deck_id = DECK_IDS.get(name, hash(name) % (2**31))
    deck = genanki.Deck(deck_id, f"Heisig::{name}")

    cards = load_csv_cards(csv_path)
    for card in cards:
        note = build_note(card)
        deck.add_note(note)

    media = collect_media_files()

    pkg = genanki.Package(deck)
    pkg.media_files = media
    pkg.write_to_file(str(output_path))

    return len(cards)


def main():
    os.chdir(ROOT)

    decks = [
        ("RTH", "RTH_deck.csv", "RTH_deck.apkg"),
        ("RSH", "RSH_deck.csv", "RSH_deck.apkg"),
        ("RTK", "RTK_deck.csv", "RTK_deck.apkg"),
        ("Ultimate", "Ultimate_deck.csv", "Ultimate_deck.apkg"),
    ]

    print("Building .apkg decks...")
    print(f"Primitive images: {len(prim_manifest)} entries in manifest")

    media = collect_media_files()
    print(f"Media files to embed: {len(media)}")

    for name, csv_file, apkg_file in decks:
        csv_path = ROOT / csv_file
        if not csv_path.exists():
            print(f"  SKIP {name}: {csv_file} not found (run build_decks.py first)")
            continue
        n = build_deck(name, csv_path, ROOT / apkg_file)
        print(f"  {apkg_file}: {n} cards")

    print("\nDone!")


if __name__ == "__main__":
    main()
