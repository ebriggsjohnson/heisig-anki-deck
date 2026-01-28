"""Heisig Mnemonic Generator — Anki add-on.

Auto-fills a "Heisig Explanation" field with character decomposition
and optional LLM-generated mnemonic stories.
"""

from aqt import gui_hooks
from .gui import add_editor_button, on_focus_lost, setup_menu

gui_hooks.editor_did_init_buttons.append(add_editor_button)
gui_hooks.editor_did_unfocus_field.append(on_focus_lost)
gui_hooks.main_window_did_init.append(lambda: setup_menu())
