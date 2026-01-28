# Heisig Anki Decks & Mnemonic Generator

Tools for learning Chinese and Japanese characters using James W. Heisig's method: an **Anki add-on** that breaks down characters and generates mnemonic stories with AI, plus **pre-built decks** if you just want the flashcards.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ebriggsjohnson/heisig_anki_plugin/blob/main/demo.ipynb)

---

## Anki Add-on

The add-on decomposes any character into its components and optionally generates a mnemonic story using an LLM. It works with any deck — you don't need to be studying Heisig specifically.

### Features

- **One-click decomposition**: click the 漢 button in the editor to break down the current character into components, layout, reading, and Heisig book numbers
- **AI mnemonic stories**: generate vivid, memorable stories that connect component meanings to the character's keyword, using Anthropic, OpenAI, or Gemini (free tier)
- **Respects your keywords**: if you've already defined a keyword for a component character in your deck, the plugin uses yours instead of the Heisig default — useful if you're not following Heisig or prefer different mnemonics
- **Auto-fill mode**: optionally triggers decomposition automatically when you tab out of the Character field
- **Configurable**: Tools → Heisig Settings to set your LLM provider, API key, model, and field names

### Install

```bash
# Option 1: Symlink for development
ln -s /path/to/heisig_addon ~/Library/Application\ Support/Anki2/addons21/heisig_addon

# Option 2: Package and install via Anki
cd heisig_addon && zip -r ../heisig_addon.ankiaddon *
# Then: Anki → Tools → Add-ons → Install from file → select heisig_addon.ankiaddon
```

Restart Anki after installing.

### Usage

1. Your note type needs a **Character** field and a **Heisig Explanation** field (field names are configurable in Tools → Heisig Settings)
2. Type a character in the Character field
3. Click the **漢** button in the editor toolbar
4. The Heisig Explanation field fills with the decomposition:
   - Keyword and book numbers
   - Reading (pinyin)
   - Components with their meanings
   - Spatial layout (IDS)
5. To add an AI-generated story, enter your API key in Tools → Heisig Settings

<!-- TODO: add screenshots -->

---

## Pre-built Decks

If you don't want to install an add-on, you can just download and import the pre-built `.apkg` decks. These include all the decomposition data baked into each card — you just won't have the LLM story generation feature.

| File | Contents | Cards |
|------|----------|-------|
| `RSH_deck.apkg` | Remembering Simplified Hanzi | ~3,300 |
| `RTH_deck.apkg` | Remembering Traditional Hanzi | ~3,300 |
| `RTK_deck.apkg` | Remembering the Kanji | ~3,300 |
| `Ultimate_deck.apkg` | All 3 merged (deduplicated) | ~5,200 |

Each card includes: character, keyword, separate RSH/RTH/RTK book numbers, pinyin readings (CC-CEDICT), recursive component decomposition, spatial layout (IDS), and tags by chapter.

To import: open Anki → File → Import → select the `.apkg` file.

### Non-Unicode Primitives

57 Heisig primitives have no standard Unicode representation (marked with `囧` in the source XML). These are rendered as approximate images using visually similar characters. See `data/primitive_images/manifest.json` for the full mapping.

---

## Try It Online

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ebriggsjohnson/heisig_anki_plugin/blob/main/demo.ipynb)

Click the badge to open an interactive demo in Google Colab — no install required. Type any character, see its decomposition, and generate mnemonic stories with a free [Gemini API key](https://aistudio.google.com/apikey).

---

## Building from Source

### Setup

```bash
git clone --recurse-submodules https://github.com/ebriggsjohnson/heisig_anki_plugin.git
pip install openpyxl genanki Pillow
```

The Excel workbook (`data/Heisig's Remembering the Kanji vs. Hanzi v27.xlsx`) is required for `build_decks.py` but not included in the repo. Place it in `data/` manually.

### Scripts

| Script | Purpose |
|--------|---------|
| `scripts/parse_rsh.py` | Parse `rsh.xml` → `rsh_parsed.json` |
| `scripts/build_mapping.py` | Build component-to-name mappings |
| `scripts/build_decks.py` | Generate CSV decks |
| `scripts/crop_primitives.py` | Generate primitive approximation images |
| `scripts/build_apkg.py` | Package CSVs + images into `.apkg` files |
| `scripts/build_addon_data.py` | Build `heisig_data.json` for the add-on and web demo |

### Rebuilding decks

```bash
python scripts/crop_primitives.py   # generate primitive images
python scripts/build_apkg.py        # build .apkg with embedded media
```

## Data Sources

- **Heisig XML database**: [rouseabout/heisig](https://github.com/rouseabout/heisig) by Peter Ross (MIT license) — included as a submodule in `data/heisig-repo/`
- **IDS decomposition data**: `data/IDS.TXT` from the [CHISE project](https://www.chise.org/)
- **CC-CEDICT readings**: via the Excel workbook (not included in repo due to size)

## License

Scripts in this repo are provided as-is. The Heisig XML data (`data/heisig-repo/`) is MIT-licensed by Peter Ross. _Remebering Traditional Hanzi_, _Remembering Simplified Hanzi_, and _Remembering the Kanji _ are the intellectual property of James W. Heisig.


