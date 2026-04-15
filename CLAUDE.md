# anki-heisig project

Anki decks and add-on for learning Chinese/Japanese characters using Heisig's method.

## Owner
GitHub: ebriggsjohnson
Always set git author to `ebriggsjohnson <ebriggsjohnson@users.noreply.github.com>` before committing.

## What this project is

- **Pre-built Anki decks** (RSH, RTH, RTK, Ultimate) covering exactly the Heisig corpus — no extended character sets yet
- **Anki add-on** (`heisig_addon/`) that decomposes any character into components for any deck
- Currently ~3,240 RSH / ~3,042 RTH / ~3,032 RTK / ~3,860 Ultimate cards

## Pipeline (run in order)

```
scripts/parse_rsh.py        → data/rsh_parsed.json
scripts/build_decks.py      → RSH/RTH/RTK/Ultimate_deck.csv
scripts/build_apkg.py       → RSH/RTH/RTK/Ultimate_deck.apkg
scripts/build_addon_data.py → heisig_addon/data/heisig_data.json
```

`build_mapping.py` and `crop_primitives.py` are less frequently run (mapping overrides and primitive images).

## Key data sources

- `data/heisig-repo/rsh.xml` — Heisig XML database (git submodule, Peter Ross, MIT)
- `data/rsh_parsed.json` — parsed output from `parse_rsh.py`; includes `book` + `lesson` fields on every entry
- `data/IDS.TXT` — CHISE ideographic description sequences (character decomposition)
- `data/Heisig's Remembering the Kanji vs. Hanzi v27.xlsx` — cross-reference Excel (not in repo, must be placed in `data/` manually)
- `data/unified_mapping.json` — component → name mappings
- `data/unmapped_human_reviewed.csv` — manual name overrides for unmapped components
- `data/primitive_images/` — PNG images for the 56 pseudo-char primitives (囧xxx); `manifest.json` maps keyword → file

## Primitives

Two kinds:
1. **Real Unicode characters** Heisig uses only as primitives (e.g. 皿, 幺, 豸) — have their own cards
2. **Pseudo-char primitives** with no Unicode (stored as `囧xxx－yyy` strings in XML, e.g. `囧只－口` = "animal legs") — 56 total, rendered as `<img>` tags in the deck using `data/primitive_images/`

All 196 standalone primitives (both types) are now tagged with their RSH lesson chapter (e.g. `RSH1::L05 primitive`) so users can unsuspend by chapter.

## Tagging system

Cards are tagged `RSH1::L03` / `RSH2::L14` etc. so users unsuspend them as they progress through the books. The workflow: all cards start suspended; user unsuspends by lesson tag as they study.

- Lesson tags come from the Excel for regular characters
- Lesson tags come from `rsh_parsed.json` (`book`/`lesson` fields) for primitives
- The 8 primitives that arrive via Excel with no lesson tag are patched in `build_decks.py` using `prim_lesson_by_char`

## Anki note types

Two models in `build_apkg.py`:
- `MODEL_ID = 1607392319` — "Heisig Primitives + Characters" (RSH/RTH/RTK decks), 11 fields
- `ULTIMATE_MODEL_ID = 1607392324` — "Heisig Ultimate (with variants)", 18 fields

**Important:** Deleting a deck in Anki does NOT delete the note type. If the note type schema changes, users must delete it via Tools → Manage Note Types before reimporting.

## What doesn't exist yet (future work)

- Extended character sets (HSK, 通用规范汉字表, Taiwan standard lists) — scaffolding exists in some scripts but not active
- AI-generated mnemonic stories
- Better Traditional/Japanese decomposition
