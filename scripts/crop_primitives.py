"""Generate primitive images for non-unicode Heisig primitives.

For the 56 primitives marked with 囧 in the XML (no Unicode representation),
this script generates PNG images using Unicode approximation characters.

Tier 1: The primitive IS a real character (e.g., 囧高 = "Eiffel Tower") — render
        the character directly.
Tier 2: A close single-character approximation exists (e.g., 囧只－口 ≈ 八).
Tier 3: No good approximation — placeholder; user provides PNGs manually.

Output: data/primitive_images/<keyword_safe>.png
Also writes data/primitive_images/manifest.json mapping keyword -> filename + metadata.
"""

import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "data" / "primitive_images"
RSH_XML = ROOT / "data" / "heisig-repo" / "rsh.xml"

# ── Approximation mapping ─────────────────────────────────────────────
# (keyword, approx_char, tier, note)
# Tier 1: char is exact (just used with different primitive name)
# Tier 2: close approximation
# Tier 3: no good single-char approx — needs user screenshot
APPROXIMATIONS = {
    # Tier 1 — whole character used as primitive
    "belt":           ("冂", 1, None),
    "cast":           ("勹", 1, None),
    "city walls":     ("阝", 1, None),
    "Eiffel Tower":   ("高", 1, None),
    "Disneyland":     ("若", 1, None),
    "Magellan":       ("旁", 1, None),
    "flophouse":      ("家", 1, None),
    "dog kennel":     ("因", 1, None),
    "miser":          ("我", 1, None),
    "cadet":          ("曹", 1, None),
    "stepladder":     ("登", 1, None),
    "Hercules":       ("甚", 1, None),

    # Tier 2 — reasonable approximation
    "animal legs":    ("八", 2, "only－口 from 只"),
    "tool":           ("具", 2, "without 目"),
    "lidded crock":   ("吉", 2, "inner part of 周"),
    "Thanksgiving":   ("栽", 2, "≈载 without 车"),
    "mending":        ("走", 2, "without 十"),
    "apron":          ("冠", 2, "≈冖+巾"),
    "wool":           ("差", 2, "without 工"),
    "tucked under the arm": ("又", 2, "史 without 口"),
    "birdhouse":      ("受", 2, "without 又"),
    "wall":           ("云", 2, "会 without 亼"),
    "outhouse":       ("尚", 2, "赏 without 贝"),
    "plow":           ("乚", 2, "以 without 丶人"),
    "greenhouse":     ("宝", 2, "≈荣 without 木"),
    "banner":         ("㫃", 2, "施 without 也"),
    "salad":          ("龷", 2, "昔 without 日"),
    "quarter":        ("拳", 2, "眷 without 目"),
    "fencing foil":   ("刂", 2, "坚 without 圣"),
    "slingshot":      ("与", 2, "without bottom 一"),
    "pointed tail":   ("与", 2, "without 丨一"),
    "letter opener":  ("卯", 2, "贸 without 贝"),
    "chop":           ("卩", 2, "节 without 艹"),
    "staples":        ("𠂇", 2, "印 without 卩"),
    "hamster cage":   ("塞", 2, "赛 without 贝"),
    "grow up":        ("龶", 2, "毒 without 母"),
    "cornstalk":      ("丰", 2, "奉 without 大"),
    "silage":         ("垂", 2, "without top/bottom 一"),
    "key":            ("⺈", 2, "侯 without 亻矢"),
    "belch":          ("㕣", 2, "船 without 舟"),
    "barrette":       ("衣", 2, "丧 without 十丷"),
    "owl":            ("应", 2, "without 广"),
    "decapitation":   ("梁", 2, "粱 without 米"),
    "dunce":          ("侵", 2, "浸 without 氵"),
    "chapel":         ("宀", 2, "索 without 糸"),
    "zipper":         ("與", 2, "舆 without 车"),
    "chocolate turtle": ("将", 2, "酱 without 酉"),
    "bullfighter":    ("监", 2, "鉴 without 金"),
    "Frankenbowser":  ("尢", 2, "尴 without 监"),
    "scarecrow":      ("择", 2, "泽 without 氵"),
    "razor wire":     ("那", 2, "without 阝"),

    # Tier 3 — needs user-provided screenshot
    "crutches":       (None, 3, "介 without 𠆢 — two falling strokes"),
    "schoolhouse":    ("学", 2, "top part only — ⺍冖 without 子"),
    "infant":         (None, 3, "充 without 儿 — top 亠厶 part"),
    "caverns":        (None, 3, "席 without 巾 — 广+廿 top"),
    "sparkler":       (None, 3, "率 without 玄十 — 亠幺幺"),
    "Biang":          (None, 3, "novelty character — skip"),
}


def safe_filename(keyword):
    return re.sub(r'[^a-zA-Z0-9_]', '_', keyword.lower()).strip('_')


def get_non_unicode_primitives():
    """Get all 囧 primitives from XML: keyword -> character field."""
    tree = ET.parse(RSH_XML)
    root = tree.getroot()
    prims = {}
    for book in root.findall(".//book"):
        for page in book.findall(".//page"):
            for frame in page.findall("frame"):
                char = frame.get("character", "")
                if "囧" in char:
                    kw = frame.get("keyword", "")
                    prims[kw] = char
    return prims


def render_character(char, size=200, font_size=160):
    """Render a single CJK character as a PNG image."""
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Try several CJK fonts on macOS
    font = None
    for font_path in [
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    ]:
        try:
            font = ImageFont.truetype(font_path, font_size)
            break
        except (IOError, OSError):
            continue

    if font is None:
        font = ImageFont.load_default()

    # Center the character
    bbox = draw.textbbox((0, 0), char, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (size - tw) // 2 - bbox[0]
    y = (size - th) // 2 - bbox[1]
    draw.text((x, y), char, fill=(0, 0, 0, 255), font=font)

    return img


def render_placeholder(keyword, note):
    """Render a placeholder image for Tier 3 primitives."""
    size = 200
    img = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    except (IOError, OSError):
        font = ImageFont.load_default()

    draw.text((10, 80), f"[{keyword}]", fill=(180, 0, 0, 255), font=font)
    draw.text((10, 110), "needs image", fill=(128, 128, 128, 255), font=font)

    return img


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    non_unicode = get_non_unicode_primitives()
    print(f"Total 囧 primitives in XML: {len(non_unicode)}")

    manifest = {}
    saved = 0
    tier3_list = []

    for keyword, orig_char in sorted(non_unicode.items()):
        if keyword not in APPROXIMATIONS:
            print(f"  WARNING: no approximation defined for '{keyword}'")
            continue

        approx_char, tier, note = APPROXIMATIONS[keyword]
        fname = safe_filename(keyword) + ".png"
        out_path = OUTPUT_DIR / fname

        if tier == 3:
            if keyword == "Biang":
                continue  # skip novelty character

            # Check if user has provided a manual image
            manual = OUTPUT_DIR / "manual" / fname
            if manual.exists():
                # Copy manual image
                img = Image.open(manual)
                img.save(out_path)
                manifest[keyword] = {
                    "file": fname, "tier": 3, "source": "manual",
                    "note": note, "approximate": False,
                }
                saved += 1
                print(f"  {keyword}: using manual image")
            else:
                # Render placeholder
                img = render_placeholder(keyword, note)
                img.save(out_path)
                manifest[keyword] = {
                    "file": fname, "tier": 3, "source": "placeholder",
                    "note": note, "approximate": False,
                }
                tier3_list.append((keyword, note))
                saved += 1
                print(f"  {keyword}: PLACEHOLDER (needs manual image)")
        else:
            # Tier 1 or 2: render the approximation character
            img = render_character(approx_char)
            img.save(out_path)
            manifest[keyword] = {
                "file": fname, "tier": tier,
                "source": "exact" if tier == 1 else "approximate",
                "approx_char": approx_char,
                "note": note,
                "approximate": tier == 2,
            }
            saved += 1
            label = "exact" if tier == 1 else f"≈ {approx_char}"
            print(f"  {keyword}: {label}")

    # Write manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"Saved: {saved} images")
    print(f"  Tier 1 (exact): {sum(1 for v in manifest.values() if v['tier'] == 1)}")
    print(f"  Tier 2 (approx): {sum(1 for v in manifest.values() if v['tier'] == 2)}")
    print(f"  Tier 3 (manual/placeholder): {sum(1 for v in manifest.values() if v['tier'] == 3)}")

    if tier3_list:
        print(f"\nPrimitives still needing manual images ({len(tier3_list)}):")
        print(f"  Place PNGs in: {OUTPUT_DIR / 'manual'}/")
        for kw, note in tier3_list:
            print(f"    {safe_filename(kw)}.png  — {kw} ({note})")

    print(f"\nManifest: {manifest_path}")


if __name__ == "__main__":
    main()
