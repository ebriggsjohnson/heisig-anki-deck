"""GUI components: editor button and settings dialog."""

from aqt import mw, gui_hooks
from aqt.editor import Editor
from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QAction,
)
from aqt.utils import showInfo, tooltip

from .decompose import lookup, format_explanation
from .llm import generate_story


def get_config():
    return mw.addonManager.getConfig(__name__.split(".")[0])


def save_config(cfg):
    mw.addonManager.writeConfig(__name__.split(".")[0], cfg)


# --- Editor button ---

def _on_heisig_button(editor: Editor):
    """Generate Heisig explanation for the current note."""
    note = editor.note
    if note is None:
        tooltip("No note selected")
        return

    cfg = get_config()
    char_field = cfg.get("character_field", "Character")
    keyword_field = cfg.get("keyword_field", "Keyword")
    expl_field = cfg.get("explanation_field", "Heisig Explanation")

    if char_field not in note or expl_field not in note:
        tooltip(f"Note must have '{char_field}' and '{expl_field}' fields")
        return

    char = note[char_field].strip()
    if not char:
        tooltip("Character field is empty")
        return

    # Take first character only
    char = char[0]
    info = lookup(char)
    if info is None:
        tooltip(f"Character '{char}' not found in Heisig data")
        return

    html = format_explanation(char, info, col=mw.col,
                              char_field=char_field,
                              keyword_field=keyword_field)

    # Optionally generate LLM story
    api_key = cfg.get("api_key", "")
    if api_key:
        provider = cfg.get("llm_provider", "anthropic")
        model = cfg.get("model", "claude-sonnet-4-20250514")
        story = generate_story(char, info, provider, api_key, model)
        if story:
            html += f"<br><br><i>{story}</i>"

    note[expl_field] = html
    editor.loadNoteKeepingFocus()
    tooltip("Heisig explanation generated")


def add_editor_button(buttons: list, editor: Editor):
    btn = editor.addButton(
        icon=None,
        cmd="heisig",
        func=_on_heisig_button,
        tip="Generate Heisig explanation (漢)",
        label="漢",
    )
    buttons.append(btn)


# --- Focus lost hook ---

def on_focus_lost(changed: bool, note, field_idx: int) -> bool:
    cfg = get_config()
    if not cfg.get("auto_generate_story", False):
        return changed

    char_field = cfg.get("character_field", "Character")
    keyword_field = cfg.get("keyword_field", "Keyword")
    expl_field = cfg.get("explanation_field", "Heisig Explanation")

    fields = mw.col.models.field_names(note.note_type())
    if char_field not in fields or expl_field not in fields:
        return changed
    if fields[field_idx] != char_field:
        return changed

    char = note[char_field].strip()
    if not char:
        return changed

    char = char[0]
    info = lookup(char)
    if info is None:
        return changed

    html = format_explanation(char, info, col=mw.col,
                              char_field=char_field,
                              keyword_field=keyword_field)

    api_key = cfg.get("api_key", "")
    if api_key and cfg.get("auto_generate_story", False):
        provider = cfg.get("llm_provider", "anthropic")
        model = cfg.get("model", "claude-sonnet-4-20250514")
        story = generate_story(char, info, provider, api_key, model)
        if story:
            html += f"<br><br><i>{story}</i>"

    if note[expl_field] != html:
        note[expl_field] = html
        return True
    return changed


# --- Settings dialog ---

class HeisigSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Heisig Mnemonic Settings")
        self.setMinimumWidth(400)

        cfg = get_config()
        layout = QVBoxLayout(self)

        # Provider
        row = QHBoxLayout()
        row.addWidget(QLabel("LLM Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["anthropic", "openai", "gemini"])
        self.provider_combo.setCurrentText(cfg.get("llm_provider", "anthropic"))
        row.addWidget(self.provider_combo)
        layout.addLayout(row)

        # API Key
        row = QHBoxLayout()
        row.addWidget(QLabel("API Key:"))
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setText(cfg.get("api_key", ""))
        row.addWidget(self.api_key_edit)
        layout.addLayout(row)

        # Model
        row = QHBoxLayout()
        row.addWidget(QLabel("Model:"))
        self.model_edit = QLineEdit()
        self.model_edit.setText(cfg.get("model", "claude-sonnet-4-20250514"))
        row.addWidget(self.model_edit)
        layout.addLayout(row)

        # Auto generate
        self.auto_check = QCheckBox("Auto-generate story on field change")
        self.auto_check.setChecked(cfg.get("auto_generate_story", False))
        layout.addWidget(self.auto_check)

        # Character field
        row = QHBoxLayout()
        row.addWidget(QLabel("Character field:"))
        self.char_field_edit = QLineEdit()
        self.char_field_edit.setText(cfg.get("character_field", "Character"))
        row.addWidget(self.char_field_edit)
        layout.addLayout(row)

        # Keyword field
        row = QHBoxLayout()
        row.addWidget(QLabel("Keyword field:"))
        self.keyword_field_edit = QLineEdit()
        self.keyword_field_edit.setText(cfg.get("keyword_field", "Keyword"))
        row.addWidget(self.keyword_field_edit)
        layout.addLayout(row)

        # Explanation field
        row = QHBoxLayout()
        row.addWidget(QLabel("Explanation field:"))
        self.expl_field_edit = QLineEdit()
        self.expl_field_edit.setText(cfg.get("explanation_field", "Heisig Explanation"))
        row.addWidget(self.expl_field_edit)
        layout.addLayout(row)

        # Buttons
        row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        row.addWidget(save_btn)
        row.addWidget(cancel_btn)
        layout.addLayout(row)

    def on_save(self):
        cfg = {
            "llm_provider": self.provider_combo.currentText(),
            "api_key": self.api_key_edit.text(),
            "model": self.model_edit.text(),
            "auto_generate_story": self.auto_check.isChecked(),
            "character_field": self.char_field_edit.text(),
            "keyword_field": self.keyword_field_edit.text(),
            "explanation_field": self.expl_field_edit.text(),
        }
        save_config(cfg)
        tooltip("Settings saved")
        self.accept()


def open_settings():
    dlg = HeisigSettingsDialog(mw)
    dlg.exec()


def setup_menu():
    action = QAction("Heisig Settings", mw)
    action.triggered.connect(open_settings)
    mw.form.menuTools.addAction(action)
