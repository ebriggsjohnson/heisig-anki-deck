"""Parse rsh.xml to extract characters, primitives, and decompositions."""
import xml.etree.ElementTree as ET
import json
import csv

tree = ET.parse("data/heisig-repo/rsh.xml")
root = tree.getroot()

characters = []  # frames with type="character"
primitives = []  # frames with type="primitive"

for frame in root.iter("frame"):
    frame_type = frame.get("{http://www.w3.org/2001/XMLSchema-instance}type")
    char = frame.get("character")
    keyword = frame.get("keyword")
    number = frame.get("number")  # only characters have numbers

    # Get primitive aliases (pself tags inside <primitive> block)
    prim_block = frame.find("primitive")
    aliases = []
    if prim_block is not None:
        aliases = [ps.text for ps in prim_block.iter("pself") if ps.text]

    # Get components (cite tags = what this frame is made of)
    components = []
    for p in frame.findall("p"):
        for cite in p.iter("cite"):
            if cite.text:
                components.append(cite.text)

    entry = {
        "character": char,
        "keyword": keyword,
        "type": frame_type,
        "number": int(number) if number else None,
        "primitive_aliases": aliases,
        "components": components,
    }

    if frame_type == "character":
        characters.append(entry)
    elif frame_type == "primitive":
        primitives.append(entry)

# Save to JSON
output = {
    "characters": characters,
    "primitives": primitives,
}
with open("data/rsh_parsed.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

# Print summary
print(f"Characters: {len(characters)}")
print(f"Primitives: {len(primitives)}")

# Characters that also have primitive meanings
chars_with_prim = [c for c in characters if c["primitive_aliases"]]
print(f"Characters with primitive aliases: {len(chars_with_prim)}")

# Components used across all frames
all_components = set()
for entry in characters + primitives:
    all_components.update(entry["components"])
print(f"Unique component names referenced: {len(all_components)}")

# All keywords defined (as character or primitive)
defined_keywords = set()
for entry in characters + primitives:
    defined_keywords.add(entry["keyword"])
    defined_keywords.update(entry["primitive_aliases"])

# Components that are referenced but never defined
undefined = all_components - defined_keywords
print(f"\nReferenced but never defined as keyword/alias ({len(undefined)}):")
for u in sorted(undefined):
    print(f"  {u}")

# Primitives sample
print(f"\nSample primitives:")
for p in primitives[:15]:
    aliases = f" (also: {', '.join(p['primitive_aliases'])})" if p["primitive_aliases"] else ""
    comps = f" <- [{', '.join(p['components'])}]" if p["components"] else ""
    print(f"  {p['character']} = {p['keyword']}{aliases}{comps}")

# Characters with primitive meanings sample
print(f"\nSample characters with primitive aliases:")
for c in chars_with_prim[:15]:
    print(f"  {c['character']} ({c['keyword']}) -> primitive: {', '.join(c['primitive_aliases'])}")
