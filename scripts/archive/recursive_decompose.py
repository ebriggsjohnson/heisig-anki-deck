"""Test recursive decomposition strategy:
1. Use Heisig decomposition if available
2. Otherwise decompose via IDS, recursively, until all leaves are Heisig-named
"""
import json
import re
import openpyxl

# Load data
with open("data/rsh_parsed.json", "r", encoding="utf-8") as f:
    rsh = json.load(f)

# Build Heisig lookups
heisig_by_char = {}  # char -> {keyword, aliases, components, type}
heisig_by_keyword = {}  # keyword -> char

for e in rsh["characters"] + rsh["primitives"]:
    heisig_by_char[e["character"]] = e
    heisig_by_keyword[e["keyword"]] = e["character"]
    for a in e["primitive_aliases"]:
        heisig_by_keyword[a] = e["character"]

# Add radical variant mappings
radical_map = {
    '訁': '言', '糹': '糸', '釒': '金', '𥫗': '竹', '刂': '刀',
    '彳': '行', '𤣩': '玉', '𧾷': '足', '罒': '网', '乚': '乙',
    '飠': '食', '爫': '爪', '虍': '虎', '𧘇': '衣', '龶': '生',
    '𦍌': '羊', '亍': '行', '牜': '牛', '覀': '西', '丬': '爿',
    '䒑': '丷', '亻': '人', '氵': '水', '扌': '手', '忄': '心',
    '犭': '犬', '礻': '示', '衤': '衣', '灬': '火', '⺌': '小',
    '⺊': '卜', '讠': '言', '钅': '金', '饣': '食', '纟': '糸',
    '贝': '貝', '车': '車', '见': '見', '门': '門', '鱼': '魚',
    '马': '馬', '鸟': '鳥', '页': '頁', '风': '風',
}
for variant, parent in radical_map.items():
    if variant not in heisig_by_char and parent in heisig_by_char:
        heisig_by_char[variant] = {
            "character": variant,
            "keyword": heisig_by_char[parent]["keyword"],
            "type": "radical_variant",
            "primitive_aliases": [],
            "components": [],
        }

# Load IDS
ids_map = {}
with open("data/IDS.TXT", "r", encoding="utf-8-sig") as f:
    for line in f:
        if line.startswith("#") or line.strip() == "":
            continue
        parts = line.strip().split("\t")
        if len(parts) >= 3:
            ids_map[parts[1]] = parts[2:]

IDS_OPERATORS = set("⿰⿱⿲⿳⿴⿵⿶⿷⿸⿹⿺⿻⿼⿽⿾⿿〾")

def parse_ids(ids_str):
    """Parse IDS string into tree. Returns (operator, [children]) or char string."""
    cleaned = re.sub(r'\$\([^)]*\)', '', ids_str)
    cleaned = cleaned.replace('^', '').strip()
    tokens = list(cleaned)
    pos = [0]  # mutable for closure

    def parse_next():
        if pos[0] >= len(tokens):
            return None
        ch = tokens[pos[0]]
        pos[0] += 1

        if ch in IDS_OPERATORS:
            n = 3 if ch in '⿲⿳' else (1 if ch == '〾' else 2)
            children = []
            for _ in range(n):
                child = parse_next()
                if child is not None:
                    children.append(child)
            return (ch, children)
        elif ch in '{}()0123456789 \t\r\n':
            return parse_next()
        else:
            return ch

    return parse_next()


def get_heisig_name(char):
    """Get Heisig name for a character, or None."""
    if char in heisig_by_char:
        e = heisig_by_char[char]
        # Prefer primitive alias if it exists, otherwise keyword
        if e["primitive_aliases"]:
            return e["primitive_aliases"][0]
        return e["keyword"]
    return None


def recursive_decompose(char, depth=0, max_depth=10, seen=None):
    """Decompose a character recursively.
    Returns a tree: either
        {"char": X, "name": "heisig name"} for a leaf
        {"char": X, "name": "...", "operator": "⿰", "children": [...]} for a decomposed node
        {"char": X, "name": None} for an unresolvable leaf
    """
    if seen is None:
        seen = set()
    if char in seen or depth > max_depth:
        return {"char": char, "name": get_heisig_name(char)}
    seen = seen | {char}

    name = get_heisig_name(char)

    # Strategy 1: If this char has a Heisig decomposition (from XML), use it
    if char in heisig_by_char and heisig_by_char[char].get("components"):
        e = heisig_by_char[char]
        children = []
        for comp_name in e["components"]:
            comp_char = heisig_by_keyword.get(comp_name)
            if comp_char:
                children.append({"char": comp_char, "name": comp_name})
            else:
                children.append({"char": "?", "name": comp_name})
        return {
            "char": char,
            "name": name,
            "source": "heisig",
            "children": children,
        }

    # Strategy 2: If we have a Heisig name but no decomposition, it's atomic
    if name and char in heisig_by_char and not heisig_by_char[char].get("components"):
        return {"char": char, "name": name, "source": "heisig_atomic"}

    # Strategy 3: If we have a Heisig name via radical mapping, stop here
    if name:
        return {"char": char, "name": name, "source": "radical_map"}

    # Strategy 4: Decompose via IDS, recurse on children
    if char in ids_map:
        tree = parse_ids(ids_map[char][0])
        if tree and isinstance(tree, tuple):
            op, children = tree
            decomposed_children = []
            for child in children:
                if isinstance(child, str):
                    decomposed_children.append(
                        recursive_decompose(child, depth + 1, max_depth, seen)
                    )
                elif isinstance(child, tuple):
                    # Nested IDS operator - flatten
                    decomposed_children.append(
                        {"char": "?", "name": None, "note": "nested_ids"}
                    )
            return {
                "char": char,
                "name": None,
                "source": "ids",
                "operator": op,
                "children": decomposed_children,
            }

    # Nothing works
    return {"char": char, "name": None, "source": "unknown"}


def format_tree(node, indent=0):
    """Pretty print a decomposition tree."""
    prefix = "  " * indent
    char = node["char"]
    name = node["name"] or "???"
    source = node.get("source", "")

    if "children" in node:
        op = node.get("operator", "→")
        print(f"{prefix}{char} [{name}] ({source}) {op}")
        for child in node["children"]:
            format_tree(child, indent + 1)
    else:
        print(f"{prefix}{char} [{name}] ({source})")


def count_leaves(node):
    """Count resolved vs unresolved leaves."""
    if "children" not in node:
        return (1, 0) if node["name"] else (0, 1)
    resolved = 0
    unresolved = 0
    for child in node["children"]:
        r, u = count_leaves(child)
        resolved += r
        unresolved += u
    return resolved, unresolved


# Load all Excel characters
wb = openpyxl.load_workbook("data/Heisig's Remembering the Kanji vs. Hanzi v27.xlsx")
ws = wb["RTH+RSH+RTK"]

all_excel = set()
for row in ws.iter_rows(min_row=2, values_only=True):
    for col in [3, 4, 5]:
        if row[col]:
            all_excel.add(row[col])

# Test on some interesting examples
test_chars = ['虎', '慮', '龍', '鬱', '飛', '愛', '學', '國', '聽', '體',
              '巳', '丿', '廾', '僉']
print("=== Sample Decompositions ===\n")
for ch in test_chars:
    if ch in all_excel or ch in ids_map:
        tree = recursive_decompose(ch)
        format_tree(tree)
        r, u = count_leaves(tree)
        status = "COMPLETE" if u == 0 else f"{u} unresolved"
        print(f"  -> {status}\n")

# Now run on ALL excel chars and get stats
fully_resolved = 0
partially_resolved = 0
unresolved_chars = []
all_unresolved_leaves = set()

for char in sorted(all_excel):
    tree = recursive_decompose(char)
    r, u = count_leaves(tree)
    if u == 0:
        fully_resolved += 1
    else:
        if r > 0:
            partially_resolved += 1
        else:
            unresolved_chars.append(char)
        # Collect unresolved leaf chars
        def collect_unresolved(node):
            if "children" not in node:
                if not node["name"]:
                    all_unresolved_leaves.add(node["char"])
            else:
                for child in node["children"]:
                    collect_unresolved(child)
        collect_unresolved(tree)

print(f"\n=== Coverage across all {len(all_excel)} Excel characters ===")
print(f"Fully resolved:     {fully_resolved}")
print(f"Partially resolved: {partially_resolved}")
print(f"Unresolved:         {len(unresolved_chars)}")
print(f"\nUnique unresolved leaf components: {len(all_unresolved_leaves)}")

# Show the unresolved leaves by frequency
from collections import Counter
leaf_freq = Counter()
for char in all_excel:
    tree = recursive_decompose(char)
    def count_unresolved(node):
        if "children" not in node:
            if not node["name"]:
                leaf_freq[node["char"]] += 1
        else:
            for child in node["children"]:
                count_unresolved(child)
    count_unresolved(tree)

print(f"\nTop 20 unresolved leaves:")
for leaf, count in leaf_freq.most_common(20):
    cp = ord(leaf) if len(leaf) == 1 else 0
    print(f"  {leaf} (U+{cp:04X}) appears in {count} characters")
