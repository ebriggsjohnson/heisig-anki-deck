"""Character decomposition lookup from bundled heisig_data.json."""

import json
import os

_DATA = None
_DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "heisig_data.json")


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
                                keyword_field: str) -> str:
    """Re-resolve component keywords using the user's collection.

    components_detail looks like: "木 = tree, 木 = tree"
    For each component character, check the user's deck first.
    """
    if not components_detail:
        return components_detail

    parts = []
    for part in components_detail.split(", "):
        if " = " in part:
            comp_char, _old_kw = part.split(" = ", 1)
            comp_char = comp_char.strip()
            # Only resolve single actual characters, skip 囧-encoded primitives
            if len(comp_char) == 1 and "囧" not in comp_char:
                resolved = resolve_keyword(comp_char, col, char_field, keyword_field)
                parts.append(f"{comp_char} = {resolved}")
            else:
                parts.append(part)
        else:
            parts.append(part)
    return ", ".join(parts)


def format_explanation(char: str, info: dict, col=None,
                       char_field: str = "Character",
                       keyword_field: str = "Keyword") -> str:
    """Format decomposition info as HTML for the explanation field.

    If col is provided, component keywords are resolved from the user's
    collection first, falling back to bundled data.
    """
    keyword = resolve_keyword(char, col, char_field, keyword_field)
    lines = [f"<b>{keyword}</b> ({char})"]

    # Book numbers
    nums = []
    for key, label in [("RSH_number", "RSH"), ("RTH_number", "RTH"), ("RTK_number", "RTK")]:
        v = info.get(key, "")
        if v:
            nums.append(f"{label} #{v}")
    if nums:
        lines[0] += " " + ", ".join(nums)

    if info.get("reading"):
        lines.append(f"Reading: {info['reading']}")

    components = info.get("components_detail", "")
    if components:
        components = _resolve_components_detail(
            components, col, char_field, keyword_field
        )
        lines.append(f"Components: {components}")

    if info.get("spatial"):
        lines.append(f"Layout: {info['spatial']}")

    return "<br>".join(lines)
