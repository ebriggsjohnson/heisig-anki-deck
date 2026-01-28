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

## Anki Add-on

An Anki plugin that auto-generates character breakdowns and optional LLM-powered mnemonic stories.

### Features

- **Editor button** (漢): decompose the current character into components, layout, and reading
- **Auto-fill**: optionally triggers when you tab out of the Character field
- **LLM stories**: generate mnemonic stories using Anthropic, OpenAI, or Gemini (free tier)
- **User keywords**: if you've defined your own keyword for a component in your deck, the plugin uses yours instead of the Heisig default
- **Settings dialog**: Tools → Heisig Settings to configure provider, API key, model, and field names

### Install

```bash
# Symlink into Anki's addons directory
ln -s /path/to/heisig_addon ~/Library/Application\ Support/Anki2/addons21/heisig_addon

# Or package as .ankiaddon
cd heisig_addon && zip -r ../heisig_addon.ankiaddon *
```

Your note type needs at least a `Character` field and a `Heisig Explanation` field. Field names are configurable in settings.

## Demo

- **Notebook**: [`demo.ipynb`](demo.ipynb) — renders styled cards with LLM-generated stories, viewable directly on GitHub
- **Web demo**: [`docs/index.html`](docs/index.html) — standalone HTML page, works on GitHub Pages

## Scripts

- `scripts/parse_rsh.py` — Parse `rsh.xml` → `rsh_parsed.json`
- `scripts/build_mapping.py` — Build component-to-name mappings
- `scripts/build_decks.py` — Generate CSV decks
- `scripts/crop_primitives.py` — Generate primitive approximation images
- `scripts/build_apkg.py` — Package CSVs + images into `.apkg` files
- `scripts/build_addon_data.py` — Build `heisig_data.json` from CSV for the add-on and web demo

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

Scripts in this repo are provided as-is. The Heisig XML data (`data/heisig-repo/`) is MIT-licensed by Peter Ross. _Remebering Traditional Hanzi_, _Remembering Simplified Hanzi_, and _Remembering the Kanji _ are the intellectual property of James W. Heisig.


