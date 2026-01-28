# Heisig Anki Decks

Anki flashcard decks for James W. Heisig's *Remembering the Hanzi* and *Remembering the Kanji* series.

## Decks

| File | Contents | Cards |
|------|----------|-------|
| `RSH_deck.csv` | Remembering Simplified Hanzi | ~3,300 |
| `RTH_deck.csv` | Remembering Traditional Hanzi | ~3,300 |
| `RTK_deck.csv` | Remembering the Kanji | ~3,300 |
| `Ultimate_deck.csv` | All 3 merged (deduplicated) | ~5,400 |

Each card includes: character, keyword, book numbers, pinyin readings (CC-CEDICT), recursive component decomposition, spatial layout via Ideographic Description Sequences (IDS), and tags by chapter.

## Non-Unicode Primitives

57 Heisig primitives have no standard Unicode representation (marked with `囧` in the source XML). These are rendered as approximate images using visually similar characters. See `data/primitive_images/manifest.json` for the full mapping.

To generate `.apkg` files with embedded primitive images:

```bash
pip install genanki Pillow
python scripts/crop_primitives.py   # generate primitive images
python scripts/build_apkg.py        # build .apkg with embedded media
```

## Scripts

- `scripts/parse_rsh.py` — Parse `rsh.xml` → `rsh_parsed.json`
- `scripts/build_mapping.py` — Build component-to-name mappings
- `scripts/build_decks.py` — Generate CSV decks
- `scripts/crop_primitives.py` — Generate primitive approximation images
- `scripts/build_apkg.py` — Package CSVs + images into `.apkg` files

## Data Sources

- **Heisig XML database**: [rouseabout/heisig](https://github.com/rouseabout/heisig) by Peter Ross (MIT license) — included as a submodule in `data/heisig-repo/`
- **IDS decomposition data**: `data/IDS.TXT` from the [CHISE project](https://www.chise.org/)
- **CC-CEDICT readings**: via the Excel workbook (not included in repo due to size)

## Setup

```bash
git clone --recurse-submodules https://github.com/ebriggsjohnson/heisig_anki_plugin.git
pip install openpyxl genanki Pillow
```

The Excel workbook (`data/Heisig's Remembering the Kanji vs. Hanzi v27.xlsx`) is required for `build_decks.py` but not included in the repo. Place it in `data/` manually.

## License

Scripts in this repo are provided as-is. The Heisig XML data (`data/heisig-repo/`) is MIT-licensed by Peter Ross. Heisig's keyword system is the intellectual property of James W. Heisig.

