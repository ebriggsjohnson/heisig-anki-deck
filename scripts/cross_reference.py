"""Cross-reference Excel characters with RSH parsed data and IDS decompositions."""
import json
import openpyxl
import re

# 1. Load RSH parsed data
with open("data/rsh_parsed.json", "r", encoding="utf-8") as f:
    rsh = json.load(f)

rsh_chars = {e["character"] for e in rsh["characters"]}
rsh_prims = {e["character"] for e in rsh["primitives"]}
rsh_all = rsh_chars | rsh_prims
print(f"RSH XML: {len(rsh_chars)} characters, {len(rsh_prims)} primitives")

# 2. Load Excel - get unique characters from all 3 books
wb = openpyxl.load_workbook("data/Heisig's Remembering the Kanji vs. Hanzi v27.xlsx")
ws = wb["RTH+RSH+RTK"]

excel_chars = {"TH": set(), "SH": set(), "K": set()}
for row in ws.iter_rows(min_row=2, values_only=True):
    th, sh, k = row[3], row[4], row[5]
    if th:
        excel_chars["TH"].add(th)
    if sh:
        excel_chars["SH"].add(sh)
    if k:
        excel_chars["K"].add(k)

all_excel = excel_chars["TH"] | excel_chars["SH"] | excel_chars["K"]
print(f"\nExcel totals:")
print(f"  RTH (Traditional Hanzi): {len(excel_chars['TH'])}")
print(f"  RSH (Simplified Hanzi):  {len(excel_chars['SH'])}")
print(f"  RTK (Kanji):             {len(excel_chars['K'])}")
print(f"  Unique across all 3:     {len(all_excel)}")

# 3. Coverage from RSH XML
in_rsh = all_excel & rsh_chars
not_in_rsh = all_excel - rsh_all
print(f"\nExcel chars found in RSH XML: {len(in_rsh)}")
print(f"Excel chars NOT in RSH XML:   {len(not_in_rsh)}")

# Break down what's missing by book
th_missing = excel_chars["TH"] - rsh_all
sh_missing = excel_chars["SH"] - rsh_all
k_missing = excel_chars["K"] - rsh_all
print(f"  Missing from TH only: {len(th_missing - sh_missing - k_missing)}")
print(f"  Missing from K only:  {len(k_missing - th_missing - sh_missing)}")
print(f"  Missing from SH:      {len(sh_missing)}")

# 4. Load IDS
ids_map = {}
with open("data/IDS.TXT", "r", encoding="utf-8-sig") as f:
    for line in f:
        if line.startswith("#") or line.strip() == "":
            continue
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            char = parts[1]
            # Could have multiple IDS sequences (region variants); take all
            ids_seqs = parts[2:]
            ids_map[char] = ids_seqs

print(f"\nIDS file: {len(ids_map)} characters")

# 5. IDS coverage of our excel characters
ids_covered = all_excel & set(ids_map.keys())
ids_missing = all_excel - set(ids_map.keys())
print(f"Excel chars found in IDS: {len(ids_covered)}")
print(f"Excel chars NOT in IDS:   {len(ids_missing)}")
if ids_missing:
    print(f"  Missing: {sorted(ids_missing)[:20]}...")

# 6. For chars not in RSH XML, can IDS help decompose them?
not_in_rsh_but_in_ids = not_in_rsh & set(ids_map.keys())
not_in_rsh_not_in_ids = not_in_rsh - set(ids_map.keys())
print(f"\nChars missing from RSH XML but decomposable via IDS: {len(not_in_rsh_but_in_ids)}")
print(f"Chars missing from BOTH RSH XML and IDS:             {len(not_in_rsh_not_in_ids)}")
if not_in_rsh_not_in_ids:
    print(f"  Truly missing: {sorted(not_in_rsh_not_in_ids)[:30]}")

# 7. Extract all unique IDS components for our characters
# IDS operators
ids_operators = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿〾")

def extract_ids_components(ids_str):
    """Pull out actual character components from an IDS string."""
    # Strip region tags like $(GHTJKPV) and markers like ^
    cleaned = re.sub(r'\$\([^)]*\)', '', ids_str)
    cleaned = cleaned.replace('^', '').replace('$', '')
    components = set()
    for ch in cleaned:
        if ch not in ids_operators and ch.strip() and ch not in '{}()0123456789':
            components.append(ch) if False else components.add(ch)
    return components

all_ids_components = set()
for char in all_excel:
    if char in ids_map:
        for seq in ids_map[char]:
            all_ids_components |= extract_ids_components(seq)

# How many of these components are themselves in our Heisig data?
components_in_heisig = all_ids_components & rsh_all
components_not_in_heisig = all_ids_components - rsh_all
# Further filter: which are actual CJK chars (not strokes/fragments)
cjk_components_not_in_heisig = set()
for c in components_not_in_heisig:
    cp = ord(c)
    if (0x4E00 <= cp <= 0x9FFF or  # CJK Unified
        0x3400 <= cp <= 0x4DBF or  # CJK Ext A
        0x2E80 <= cp <= 0x2FDF or  # Radicals
        0x2FF0 <= cp <= 0x2FFF or  # IDC
        0x31C0 <= cp <= 0x31EF or  # CJK Strokes
        0xF900 <= cp <= 0xFAFF or  # Compat
        0x20000 <= cp <= 0x2A6DF): # Ext B
        cjk_components_not_in_heisig.add(c)

print(f"\nIDS components used to build our Excel chars: {len(all_ids_components)}")
print(f"  Already in Heisig data: {len(components_in_heisig)}")
print(f"  NOT in Heisig data:     {len(components_not_in_heisig)}")
print(f"  Of which are CJK chars: {len(cjk_components_not_in_heisig)}")

# Sample some missing CJK components
print(f"\nSample CJK components not in Heisig ({min(30, len(cjk_components_not_in_heisig))}):")
for c in sorted(cjk_components_not_in_heisig)[:30]:
    ids_for = ids_map.get(c, ["?"])
    print(f"  {c} (U+{ord(c):04X}) IDS: {ids_for[0][:40]}")
