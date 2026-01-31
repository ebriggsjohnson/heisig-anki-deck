"""Character decomposition lookup from bundled heisig_data.json."""

import json
import os

_DATA = None
_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "heisig_data.json")

# IDS operator descriptions
IDS_DESCRIPTIONS = {
    "⿰": "left → right",
    "⿱": "top → bottom",
    "⿲": "left → middle → right",
    "⿳": "top → middle → bottom",
    "⿴": "surrounded",
    "⿵": "open at bottom",
    "⿶": "open at top",
    "⿷": "open at right",
    "⿸": "upper-left wraps",
    "⿹": "upper-right wraps",
    "⿺": "lower-left wraps",
    "⿻": "overlapping",
}


def _load():
    global _DATA
    if _DATA is None:
        with open(_DATA_PATH, encoding="utf-8") as f:
            _DATA = json.load(f)
    return _DATA


def lookup(char: str) -> dict | None:
    """Return decomposition dict for a character, or None if not found."""
    data = _load()
    return data.get(char.strip())


def resolve_keyword(char: str, col, char_field: str, keyword_field: str) -> str:
    """Resolve a keyword for a character.

    Checks the user's collection first (searching for a note whose
    char_field matches the character and whose keyword_field is non-empty).
    Falls back to heisig_data.json, then to the character itself.
    """
    if col is not None:
        try:
            note_ids = col.find_notes(f'"{char_field}:{char}"')
            for nid in note_ids:
                note = col.get_note(nid)
                if keyword_field in note and note[keyword_field].strip():
                    return note[keyword_field].strip()
        except Exception:
            pass

    info = lookup(char)
    if info and info.get("keyword"):
        return info["keyword"]

    return char


def _resolve_components_detail(components_detail: str, col, char_field: str,
                                keyword_field: str) -> list:
    """Re-resolve component keywords using the user's collection.

    components_detail looks like: "木 = tree, 木 = tree"
    For each component character, check the user's deck first.
    Deduplicates entries with the same character and resolved keyword.
    Returns a list of (char, keyword) tuples.
    """
    if not components_detail:
        return []

    seen = set()
    parts = []
    for part in components_detail.split(", "):
        if " = " in part:
            comp_char, old_kw = part.split(" = ", 1)
            comp_char = comp_char.strip()
            # Only resolve single actual characters, skip 囧-encoded primitives
            if len(comp_char) == 1 and "囧" not in comp_char:
                resolved = resolve_keyword(comp_char, col, char_field, keyword_field)
            else:
                resolved = old_kw.strip()
            key = (comp_char, resolved)
            if key not in seen:
                seen.add(key)
                parts.append(key)
    return parts


def _parse_ids_layout(ids: str) -> str:
    """Extract a human-readable layout description from IDS string.

    Returns the first IDS operator found translated to readable text,
    or empty string if none found.
    """
    if not ids:
        return ""

    for char in ids:
        if char in IDS_DESCRIPTIONS:
            return IDS_DESCRIPTIONS[char]
    return ""


def format_explanation(char: str, info: dict, col=None,
                       char_field: str = "Character",
                       keyword_field: str = "Keyword") -> str:
    """Format decomposition info as HTML for the explanation field.

    Output: keyword, components on separate lines, and spatial layout.
    If col is provided, component keywords are resolved from the user's
    collection first, falling back to bundled data.
    """
    keyword = resolve_keyword(char, col, char_field, keyword_field)
    lines = [f"<b>{keyword}</b>"]

    components = info.get("components_detail", "")
    if components:
        parts = _resolve_components_detail(
            components, col, char_field, keyword_field
        )
        for comp_char, comp_kw in parts:
            lines.append(f'<span style="color:#1a5276">{comp_char}</span> '
                         f'<span style="color:#666">{comp_kw}</span>')

        # Add spatial layout from IDS
        ids = info.get("ids", "")
        layout = _parse_ids_layout(ids)
        if layout:
            lines.append(f"<i>({layout})</i>")
    else:
        lines.append("<i>(no breakdown)</i>")

    return "<br>".join(lines)
