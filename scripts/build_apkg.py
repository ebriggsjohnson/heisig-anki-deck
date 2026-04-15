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
    """Replace 囧 characters in components_detail with img tags.

    Handles both old format (char = name, char = name) and
    new HTML format (<span>char</span> <span>name</span><br>...).
    """
    if not detail_str:
        return detail_str

    # Check if it's the new HTML format
    if "<span" in detail_str:
        # For HTML format, look for 囧 and replace with img tags
        for jiong_char, kw in jiong_char_to_keyword.items():
            if jiong_char in detail_str:
                tag = prim_img_tag(kw)
                if tag:
                    # Replace the character in the span
                    detail_str = detail_str.replace(
                        f'>{jiong_char}</span>',
                        f'>{tag}</span>'
                    )
        return detail_str

    # Old format: "char = name, char = name"
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
.primitive-meanings {
  font-size: 15px;
  color: #999;
  margin: 2px 0 8px 0;
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
.numbers {
  font-size: 13px;
  color: #888;
  margin: 4px 0;
}
.explanation {
  font-size: 15px;
  color: #444;
  margin-top: 12px;
  text-align: left;
  line-height: 1.5;
}
.approx-note {
  font-size: 11px;
  color: #c0392b;
}
.card-type {
  font-size: 14px;
  color: #888;
  margin-bottom: 10px;
}
.reading-answer {
  font-size: 36px;
  font-weight: bold;
  margin: 15px 0;
  color: #1a5276;
}
.variants {
  font-size: 14px;
  color: #666;
  margin: 8px 0;
  padding: 4px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  display: inline-block;
}
"""

# ── Writing card templates (keyword + pinyin → character) ──────────────
# Always generates — primitives with no reading still get a keyword→character card
WRITING_FRONT_TEMPLATE = """\
<div class="card-type">Writing</div>
<div class="keyword">{{Keyword}}</div>
{{#PrimitiveMeanings}}<div class="primitive-meanings">as primitive: {{PrimitiveMeanings}}</div>{{/PrimitiveMeanings}}
{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}
"""

WRITING_BACK_TEMPLATE = """\
<div class="card-type">Writing</div>
<div class="keyword">{{Keyword}}</div>
{{#PrimitiveMeanings}}<div class="primitive-meanings">as primitive: {{PrimitiveMeanings}}</div>{{/PrimitiveMeanings}}
{{#Reading}}<div class="reading">{{Reading}}</div>{{/Reading}}
<hr>
<div class="character">{{Character}}</div>
{{#Decomposition}}<div class="decomposition">{{Decomposition}}</div>{{/Decomposition}}
{{#ComponentsDetail}}<div class="components">{{ComponentsDetail}}</div>{{/ComponentsDetail}}
{{#Spatial}}<div class="spatial">{{Spatial}}</div>{{/Spatial}}
{{#RTH_Number}}<div class="numbers">RTH #{{RTH_Number}}</div>{{/RTH_Number}}
{{#RSH_Number}}<div class="numbers">RSH #{{RSH_Number}}</div>{{/RSH_Number}}
{{#RTK_Number}}<div class="numbers">RTK #{{RTK_Number}}</div>{{/RTK_Number}}
{{#Heisig Explanation}}<div class="explanation">{{Heisig Explanation}}</div>{{/Heisig Explanation}}
"""

# ── Reading card templates (character → pinyin) ────────────────────────
# Only generates when Reading field is non-empty (RTH/RSH cards)
READING_FRONT_TEMPLATE = """\
{{#Reading}}
<div class="card-type">Reading</div>
<div class="character">{{Character}}</div>
{{/Reading}}
"""

READING_BACK_TEMPLATE = """\
{{#Reading}}
<div class="card-type">Reading</div>
<div class="character">{{Character}}</div>
<hr>
<div class="reading-answer">{{Reading}}</div>
<div class="keyword">{{Keyword}}</div>
{{/Reading}}
"""

heisig_model = genanki.Model(
    MODEL_ID,
    "Heisig Primitives + Characters",
    fields=[
        {"name": "Character"},
        {"name": "Keyword"},
        {"name": "PrimitiveMeanings"},
        {"name": "Reading"},
        {"name": "Variants"},
        {"name": "Decomposition"},
        {"name": "ComponentsDetail"},
        {"name": "Spatial"},
        {"name": "RTH_Number"},
        {"name": "RSH_Number"},
        {"name": "RTK_Number"},
        {"name": "Heisig Explanation"},
    ],
    templates=[
        {
            "name": "Writing",
            "qfmt": WRITING_FRONT_TEMPLATE,
            "afmt": WRITING_BACK_TEMPLATE,
        },
        {
            "name": "Reading",
            "qfmt": READING_FRONT_TEMPLATE,
            "afmt": READING_BACK_TEMPLATE,
        },
    ],
    css=CARD_CSS,
    sort_field_index=1,  # Sort by Keyword
)

# ── Ultimate deck model (with variant quiz cards) ──────────────────────
ULTIMATE_MODEL_ID = 1607392324

# Variant quiz templates
SIMPLIFIED_FRONT = """\
{{#Simplified}}
<div class="card-type">Simplified form?</div>
<div class="character">{{Character}}</div>
<div class="keyword">{{Keyword}}</div>
{{/Simplified}}
"""

SIMPLIFIED_BACK = """\
{{#Simplified}}
<div class="card-type">Simplified form</div>
<div class="character">{{Character}} → {{Simplified}}</div>
<hr>
<div class="reading-answer">{{SimplifiedReading}}</div>
{{#SimplifiedDecomposition}}<div class="decomposition">{{SimplifiedDecomposition}}</div>{{/SimplifiedDecomposition}}
{{#SimplifiedComponents}}<div class="components">{{SimplifiedComponents}}</div>{{/SimplifiedComponents}}
{{/Simplified}}
"""

JAPANESE_FRONT = """\
{{#Japanese}}
<div class="card-type">Japanese form?</div>
<div class="character">{{Character}}</div>
<div class="keyword">{{Keyword}}</div>
{{/Japanese}}
"""

JAPANESE_BACK = """\
{{#Japanese}}
<div class="card-type">Japanese form</div>
<div class="character">{{Character}} → {{Japanese}}</div>
<hr>
{{#JapaneseDecomposition}}<div class="decomposition">{{JapaneseDecomposition}}</div>{{/JapaneseDecomposition}}
{{#JapaneseComponents}}<div class="components">{{JapaneseComponents}}</div>{{/JapaneseComponents}}
{{/Japanese}}
"""

ultimate_model = genanki.Model(
    ULTIMATE_MODEL_ID,
    "Heisig Ultimate (with variants)",
    fields=[
        {"name": "Character"},          # Canonical (Traditional)
        {"name": "Keyword"},
        {"name": "PrimitiveMeanings"},
        {"name": "Reading"},            # Canonical reading
        {"name": "Decomposition"},      # Canonical decomposition
        {"name": "ComponentsDetail"},   # Canonical components
        {"name": "Spatial"},
        {"name": "RTH_Number"},
        {"name": "RSH_Number"},
        {"name": "RTK_Number"},
        {"name": "Simplified"},         # Only if different from canonical
        {"name": "SimplifiedReading"},
        {"name": "SimplifiedDecomposition"},
        {"name": "SimplifiedComponents"},
        {"name": "Japanese"},           # Only if different from canonical
        {"name": "JapaneseDecomposition"},
        {"name": "JapaneseComponents"},
        {"name": "Heisig Explanation"},
        {"name": "ReviewNotes"},        # For user audit/corrections
    ],
    templates=[
        {
            "name": "Writing",
            "qfmt": WRITING_FRONT_TEMPLATE,
            "afmt": WRITING_BACK_TEMPLATE,
        },
        {
            "name": "Reading",
            "qfmt": READING_FRONT_TEMPLATE,
            "afmt": READING_BACK_TEMPLATE,
        },
        {
            "name": "Simplified",
            "qfmt": SIMPLIFIED_FRONT,
            "afmt": SIMPLIFIED_BACK,
        },
        {
            "name": "Japanese",
            "qfmt": JAPANESE_FRONT,
            "afmt": JAPANESE_BACK,
        },
    ],
    css=CARD_CSS,
    sort_field_index=1,  # Sort by Keyword
)


def build_note(card):
    """Build a genanki Note from a card dict (single-book decks)."""
    char = card.get("character", "")
    character_html = char_display(char)

    # Enrich components_detail with img tags
    components = enrich_components_detail(card.get("components_detail", ""))

    tags_str = card.get("tags", "")

    note = genanki.Note(
        model=heisig_model,
        fields=[
            character_html,
            card.get("keyword", ""),
            card.get("primitive_meanings", ""),
            card.get("reading", ""),
            card.get("variants", ""),
            card.get("decomposition", ""),
            components,
            card.get("spatial", ""),
            card.get("RTH_number", ""),
            card.get("RSH_number", ""),
            card.get("RTK_number", ""),
            "",  # Heisig Explanation — filled by the add-on
        ],
        tags=tags_str.split() if tags_str else [],
    )
    return note


def build_ultimate_note(card):
    """Build a genanki Note for Ultimate deck (with variant fields)."""
    char = card.get("character", "")
    character_html = char_display(char)

    # Enrich components for canonical and variants
    components = enrich_components_detail(card.get("components_detail", ""))
    simp_components = enrich_components_detail(card.get("simplified_components", ""))
    jp_components = enrich_components_detail(card.get("japanese_components", ""))

    # Handle simplified/japanese character display
    simp_char = card.get("simplified", "")
    simp_html = char_display(simp_char) if simp_char else ""
    jp_char = card.get("japanese", "")
    jp_html = char_display(jp_char) if jp_char else ""

    tags_str = card.get("tags", "")

    note = genanki.Note(
        model=ultimate_model,
        fields=[
            character_html,
            card.get("keyword", ""),
            card.get("primitive_meanings", ""),
            card.get("reading", ""),
            card.get("decomposition", ""),
            components,
            card.get("spatial", ""),
            card.get("RTH_number", ""),
            card.get("RSH_number", ""),
            card.get("RTK_number", ""),
            simp_html,
            card.get("simplified_reading", ""),
            card.get("simplified_decomposition", ""),
            simp_components,
            jp_html,
            card.get("japanese_decomposition", ""),
            jp_components,
            "",  # Heisig Explanation — filled by the add-on
            "",  # ReviewNotes — for user corrections
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


def build_deck(name, csv_path, output_path, use_ultimate_model=False):
    """Build an .apkg file from a CSV deck."""
    deck_id = DECK_IDS.get(name, hash(name) % (2**31))
    deck = genanki.Deck(deck_id, f"Heisig::{name}")

    cards = load_csv_cards(csv_path)
    # Drop entries with no keyword
    cards = [c for c in cards if c.get("keyword", "").strip()]

    note_builder = build_ultimate_note if use_ultimate_model else build_note
    for card in cards:
        note = note_builder(card)
        deck.add_note(note)

    media = collect_media_files()

    pkg = genanki.Package(deck)
    pkg.media_files = media
    pkg.write_to_file(str(output_path))

    return len(cards)


def main():
    os.chdir(ROOT)

    # (name, csv_file, apkg_file, use_ultimate_model)
    decks = [
        ("RTH", "RTH_deck.csv", "RTH_deck.apkg", False),
        ("RSH", "RSH_deck.csv", "RSH_deck.apkg", False),
        ("RTK", "RTK_deck.csv", "RTK_deck.apkg", False),
        ("Ultimate", "Ultimate_deck.csv", "Ultimate_deck.apkg", True),
    ]

    print("Building .apkg decks...")
    print(f"Primitive images: {len(prim_manifest)} entries in manifest")

    media = collect_media_files()
    print(f"Media files to embed: {len(media)}")

    for name, csv_file, apkg_file, use_ultimate in decks:
        csv_path = ROOT / csv_file
        if not csv_path.exists():
            print(f"  SKIP {name}: {csv_file} not found (run build_decks.py first)")
            continue
        n = build_deck(name, csv_path, ROOT / apkg_file, use_ultimate_model=use_ultimate)
        print(f"  {apkg_file}: {n} cards")

    print("\nDone!")


if __name__ == "__main__":
    main()
