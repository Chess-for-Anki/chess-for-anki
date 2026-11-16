"""
Import dialog for Chess for Anki.
Lets the user paste a PGN, set a title, tags, and choose their color.

Behaves like Anki's "Add Cards" window:
- stays open after creating a card
- clears the title and PGN for the next entry
- keeps the tags (and color/deck) so consecutive lines are quick to add
"""

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit,
    QTextEdit, QComboBox, QPushButton, Qt,
    QGroupBox, QRadioButton, QButtonGroup, QFrame, QLabel, QCheckBox,
    QScrollArea, QWidget, QTextCursor, QFileDialog, QSizePolicy, QTimer,
    QIcon, QSize, QFont, QTextCharFormat
)
from aqt import mw
from aqt.utils import showWarning, tooltip

from .pgn_parser import expand_variations, read_pgn_file
from .note_type import create_note
from .position_editor import PositionEditor

# Opened by the "Website" button on the tool page.
WEBSITE_URL = "https://buymeacoffee.com/fernandomec"
CHESS_OCR_URL = "https://helpman.komtera.lt/"  # Helpmate Analyzer image->FEN tool


def _is_valid_fen(text):
    """True if `text` begins with a well-formed FEN piece-placement field
    (8 ranks separated by '/', each describing exactly 8 squares). Used to tell
    a pasted/loaded FEN apart from PGN moves."""
    toks = (text or "").strip().split()
    if not toks:
        return False
    ranks = toks[0].split("/")
    if len(ranks) != 8:
        return False
    for rank in ranks:
        count = 0
        for ch in rank:
            if ch.isdigit():
                count += int(ch)
            elif ch in "pnbrqkPNBRQK":
                count += 1
            else:
                return False
        if count != 8:
            return False
    return True


TAG_COMPLETE_LIMIT = 100  # most tag suggestions shown in the popup at once


def _make_tag_edit(parent, col):
    """Anki's own TagEdit, with the autocomplete popup limited to
    TAG_COMPLETE_LIMIT prefix matches (like Woodpecker Mode and Anki's Add
    window), so a collection with tens of thousands of tags (AnkiHub/AnKing)
    doesn't flood the dropdown.

    IMPORTANT: the cap is applied the same safe way Woodpecker does it - we keep
    the full tag list ourselves and, on each keystroke, feed the completer's
    model only the matches for the current word, from a ``textEdited`` slot. We
    must NOT touch the model from inside the completer's ``splitPath``: doing so
    re-enters Qt while it is building completions and hard-crashes Anki. Multi-tag
    completion and selection stay handled by Anki's own completer.

    Fully guarded: if the cap can't be wired up the field just behaves like the
    normal (uncapped) TagEdit, and if TagEdit isn't available at all we fall back
    to a plain line edit. It can never end up worse than the stock field."""
    try:
        from aqt.tagedit import TagEdit
        edit = TagEdit(parent)
        if col is not None:
            edit.setCol(col)
    except Exception:
        return QLineEdit()

    try:
        comp = edit.completer()
        model = comp.model() if comp is not None else None
        tags = sorted(col.tags.all()) if col is not None else []
        pairs = [(t.lower(), t) for t in tags]
        if comp is not None and model is not None and pairs:
            # Start the completer's model empty so it never scans the whole tag
            # list; our slot fills in only the matches (<= limit) as the user
            # types. This keeps the completer fast AND caps how many show.
            model.setStringList([])

            def _cap(text, _comp=comp, _model=model, _pairs=pairs):
                try:
                    # Prefer the word Anki's completer is actually completing
                    # (set on it just before this slot runs); fall back to the
                    # last space-separated token.
                    word = ""
                    ctags = getattr(_comp, "tags", None)
                    ccur = getattr(_comp, "cursor", None)
                    if ctags and ccur is not None and 0 <= ccur < len(ctags):
                        word = ctags[ccur] or ""
                    if not word:
                        word = text.rsplit(" ", 1)[-1] if text else ""
                    pfx = word.strip().lower()
                    if not pfx:
                        _model.setStringList([])
                        return
                    out = []
                    for low, orig in _pairs:
                        if low.startswith(pfx):
                            out.append(orig)
                            if len(out) >= TAG_COMPLETE_LIMIT:
                                break
                    _model.setStringList(out)
                    _comp.complete()
                except Exception:
                    pass

            edit.textEdited.connect(_cap)
    except Exception:
        pass  # leave the stock (uncapped) completer in place

    return edit


class RichNotesEdit(QTextEdit):
    """Notes editor for Book/Personal Notes: Ctrl+B toggles bold, Ctrl+I
    toggles italics, Ctrl+U toggles underline (Cmd on macOS - Qt maps
    ControlModifier there), and Tab types an indent instead of moving focus.
    The formatting is preserved onto the card by _notes_field_html()."""

    def __init__(self, parent=None):
        QTextEdit.__init__(self, parent)
        try:
            self.setTabChangesFocus(False)
            self.setTabStopDistance(
                4 * self.fontMetrics().horizontalAdvance(" "))
        except Exception:
            pass
        self.setToolTip("Ctrl+B bold \u00b7 Ctrl+I italics \u00b7 Ctrl+U "
                        "underline \u00b7 Tab indents \u2014 formatting is "
                        "kept on the card")

    def _toggle_format(self, bold=False, italic=False, underline=False):
        try:
            fmt = QTextCharFormat()
            cur = self.currentCharFormat()
            if bold:
                heavy = cur.fontWeight() >= 600
                fmt.setFontWeight(QFont.Weight.Normal if heavy
                                  else QFont.Weight.Bold)
            if italic:
                fmt.setFontItalic(not cur.fontItalic())
            if underline:
                fmt.setFontUnderline(not cur.fontUnderline())
            self.mergeCurrentCharFormat(fmt)
        except Exception:
            pass

    def keyPressEvent(self, event):
        try:
            if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
                if event.key() == Qt.Key.Key_B:
                    self._toggle_format(bold=True)
                    return
                if event.key() == Qt.Key.Key_I:
                    self._toggle_format(italic=True)
                    return
                if event.key() == Qt.Key.Key_U:
                    self._toggle_format(underline=True)
                    return
        except Exception:
            pass
        QTextEdit.keyPressEvent(self, event)


def _notes_field_html(edit):
    """Serialize a notes editor into durable Anki-field HTML.

    Bold/italic become <b>/<i>; line breaks become <br>; tabs become four
    non-breaking spaces and runs of spaces become non-breaking spaces - so
    indentation survives HTML rendering EVERYWHERE (the card on desktop and
    mobile, and Anki's own Browse editor), instead of collapsing to single
    spaces. Text is HTML-escaped, so typing '<' in a note can't break the
    card. Falls back to plain text if anything about the document surprises
    us."""
    import html as _h
    import re as _re

    def enc(t, line_start):
        t = _h.escape(t, quote=False)
        t = t.replace("\t", "&nbsp;&nbsp;&nbsp;&nbsp;")
        t = _re.sub(r"  +", lambda m: "&nbsp;" * len(m.group(0)), t)
        # A single leading space only counts as indentation at a LINE start -
        # not at every bold/italic fragment boundary mid-sentence.
        t = _re.sub(r"(?<=\n) ", "&nbsp;", t)
        if line_start and t.startswith(" "):
            t = "&nbsp;" + t[1:]
        return t

    try:
        doc = edit.document()
        parts = []
        block = doc.begin()
        first = True
        while block.isValid():
            if not first:
                parts.append("<br>")
            it = block.begin()
            line_start = True
            while not it.atEnd():
                frag = it.fragment()
                if frag.isValid():
                    f = frag.charFormat()
                    raw = frag.text().replace("\u2028", "\n")
                    t = enc(raw, line_start)
                    t = t.replace("\n", "<br>")
                    if f.fontUnderline():
                        t = "<u>" + t + "</u>"
                    if f.fontItalic():
                        t = "<i>" + t + "</i>"
                    if f.fontWeight() >= 600:
                        t = "<b>" + t + "</b>"
                    parts.append(t)
                    line_start = raw.endswith("\n")
                it += 1
            first = False
            block = block.next()
        out = "".join(parts)
        # Trim outer blank lines/whitespace, but KEEP &nbsp; - a first line's
        # indentation is deliberate content, not padding.
        out = _re.sub(r"^(?:<br>|\s)+", "", out)
        out = _re.sub(r"(?:<br>|\s)+$", "", out)
        if _re.fullmatch(r"(?:&nbsp;|<br>|\s)*", out):
            return ""
        return out
    except Exception:
        return (edit.toPlainText() or "").strip()


# Sticky-field pins ─────────────────────────────────────────────────────────
# Each Add-dialog section can be "pinned" so its value carries to the next card
# instead of clearing after Add. A small checkbox lives in the section's group
# box; its state is stored in config under one of these keys.
STICKY_KEYS = {
    "deck": "sticky_deck",
    "title": "sticky_title",
    "color": "sticky_color",
    "startpos": "sticky_startpos",
    "book": "sticky_book",
    "personal": "sticky_personal",
    "tags": "sticky_tags",
}


class LockedPrefixTextEdit(QTextEdit):
    """A QTextEdit that can hold a non-editable, non-deletable prefix at the
    very start (used to show a grayed-out '1... ' for Custom + Black). The
    user can only edit text after the prefix; backspace/delete/typing/paste
    can never touch the prefix."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._prefix = ""

    def prefix(self):
        return self._prefix

    def set_prefix(self, prefix: str):
        """Set (or clear) the locked prefix, preserving the user's typed text."""
        from aqt.qt import QColor, QTextCharFormat, QBrush, Qt as _Qt
        body = self.user_text()
        self._prefix = prefix or ""
        self.blockSignals(True)
        self.setPlainText(self._prefix + body)
        if self._prefix:
            self._colorize_prefix()
        else:
            # No prefix: clear any leftover gray foreground so all text (and
            # future typing) reverts to the editor's default text color.
            cursor = self.textCursor()
            cursor.select(cursor.SelectionType.Document)
            clear_fmt = QTextCharFormat()
            clear_fmt.setForeground(QBrush(_Qt.BrushStyle.NoBrush))
            cursor.mergeCharFormat(clear_fmt)
            cursor.clearSelection()
            self.setTextCursor(cursor)
            self.setCurrentCharFormat(QTextCharFormat())
        self.blockSignals(False)
        self._move_cursor_to_safe()

    def user_text(self) -> str:
        """The text the user actually typed (everything after the prefix)."""
        full = self.toPlainText()
        if self._prefix and full.startswith(self._prefix):
            return full[len(self._prefix):]
        # Prefix was somehow disturbed; best effort
        if self._prefix and full.startswith(self._prefix.rstrip()):
            return full[len(self._prefix.rstrip()):]
        return full

    def _prefix_len(self):
        return len(self._prefix)

    def _colorize_prefix(self):
        """Gray out the prefix characters; ensure typed text stays white."""
        from aqt.qt import QColor
        if not self._prefix:
            # No prefix: don't override the theme's default text color.
            return
        # Gray the prefix span.
        cursor = self.textCursor()
        cursor.setPosition(0)
        cursor.setPosition(self._prefix_len(), QTextCursor.MoveMode.KeepAnchor)
        gray = cursor.charFormat()
        gray.setForeground(QColor("#888888"))
        cursor.setCharFormat(gray)
        # Any text typed after the prefix should be white (so it contrasts
        # with the gray prefix instead of inheriting its color).
        end = self.textCursor()
        end.movePosition(end.MoveOperation.End)
        white = end.charFormat()
        white.setForeground(QColor("#ffffff"))
        end.setCharFormat(white)
        self.setTextCursor(end)
        self.setCurrentCharFormat(white)

    def _ensure_white_input(self):
        """Force the current typing color to white (for text after the prefix)."""
        from aqt.qt import QColor
        fmt = self.currentCharFormat()
        fmt.setForeground(QColor("#ffffff"))
        self.setCurrentCharFormat(fmt)

    def _move_cursor_to_safe(self):
        cursor = self.textCursor()
        if cursor.position() < self._prefix_len():
            cursor.setPosition(self._prefix_len())
            self.setTextCursor(cursor)

    def keyPressEvent(self, event):
        if not self._prefix:
            super().keyPressEvent(event)
            return

        cursor = self.textCursor()
        pos = cursor.selectionStart()
        plen = self._prefix_len()

        # Block backspace that would eat into the prefix
        if event.key() == Qt.Key.Key_Backspace:
            if cursor.position() <= plen and not cursor.hasSelection():
                return
            if cursor.hasSelection() and cursor.selectionStart() < plen:
                return
        # Block delete that starts inside the prefix
        if event.key() == Qt.Key.Key_Delete:
            if cursor.position() < plen:
                return
            if cursor.hasSelection() and cursor.selectionStart() < plen:
                return

        # If cursor is inside the prefix for any typing, push it to safe zone
        if cursor.position() < plen:
            self._move_cursor_to_safe()

        # Text typed after the prefix must be white, not the gray prefix color.
        self._ensure_white_input()
        super().keyPressEvent(event)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._move_cursor_to_safe()

    def insertFromMimeData(self, source):
        # Ensure pastes land after the prefix
        self._move_cursor_to_safe()
        super().insertFromMimeData(source)


class ElidingComboBox(QComboBox):
    """A combo box whose drop-down popup is constrained to the width of the
    combo itself, so very long (e.g. deeply-nested AnKing) deck names don't
    make the popup span far wider than the dialog. Long names are elided with
    '…' both in the closed combo and in the open list."""

    def showPopup(self):
        super().showPopup()
        try:
            view = self.view()
            view.setTextElideMode(Qt.TextElideMode.ElideRight)
            w = self.width()
            container = view.parentWidget()   # the popup frame
            if container is not None:
                container.setMaximumWidth(w)
                container.resize(w, container.height())
            view.setFixedWidth(w)
        except Exception:
            pass


class ImportDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Chess for Anki - Tool")
        self.setMinimumWidth(600)
        self.setMinimumHeight(300)
        self.resize(660, 640)
        self.custom_fen = ""   # set when a custom position is confirmed
        # Sticky-field pins: load persisted state and prepare the registry.
        self._pins = {}
        self._suppress_color_clear = False
        try:
            from . import config as _cfg
            self._sticky_cfg = _cfg.get_config()
        except Exception:
            self._sticky_cfg = {}
        self.pos_manual_mode = False  # True while a Manual Edit position locks the box
        self.loaded_pgn_text = ""  # set when a .pgn file is imported
        self.manual_pgn_text = ""  # set when moves are entered via Manual Entry
        self._build_ui()
        # Restore last-committed pinned values into their widgets (once, after
        # the UI exists). Cheap: one config dict already in memory.
        self._restore_sticky_values()
        # Sync the PGN prefix to the initial state (White + Opening = no prefix)
        self._update_pgn_prefix()

    def _build_ui(self):
        # Outer layout holds a scroll area (content), a pinned Tags row,
        # and the fixed action buttons.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        # Never scroll horizontally: content should always fit the window width
        # and resize with it, rather than overflowing past the right edge.
        scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # ── Add to Deck (first / top) ──────────────────────────
        deck_group = QGroupBox("")
        deck_layout = QVBoxLayout(deck_group)
        self.deck_combo = ElidingComboBox()
        self.deck_combo.setEditable(True)
        self.deck_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.deck_combo.lineEdit().setPlaceholderText("Choose a deck or type a new deck name")
        # Don't let very long (e.g. deeply-nested AnKing) deck names size the
        # combo to the longest item, which would push the whole dialog wider
        # than the window. Keep a modest preferred width; the dropdown popup
        # still shows full names, and the closed combo elides with "…".
        self.deck_combo.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.deck_combo.setMinimumContentsLength(12)
        self.deck_combo.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._populate_decks()
        deck_layout.addWidget(self.deck_combo)
        self._boxed_header_pin(deck_group, "deck", "Add to Deck")
        layout.addWidget(deck_group)

        # ── Title ──────────────────────────────────────────────
        title_group = QGroupBox("")
        title_layout = QVBoxLayout(title_group)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("e.g. Ruy Lopez - Marshall Attack")
        title_layout.addWidget(self.title_edit)
        self._boxed_header_pin(title_group, "title", "Title")
        layout.addWidget(title_group)

        # ── Color ──────────────────────────────────────────────
        color_group = QGroupBox("")
        color_outer = QVBoxLayout(color_group)
        # Header row: bold "I am playing as…" + the pin, on one line.
        _color_pin = self._make_pin("color")
        _color_hdr = QLabel("I am playing as…")
        _cf = _color_hdr.font(); _cf.setBold(True); _color_hdr.setFont(_cf)
        color_outer.addLayout(self._pin_row(_color_pin, _color_hdr))
        # Radios row underneath.
        color_row = QWidget()
        color_layout = QHBoxLayout(color_row)
        color_layout.setContentsMargins(0, 0, 0, 0)
        self.color_group = QButtonGroup(self)
        self.white_rb = QRadioButton("White")
        self.black_rb = QRadioButton("Black")
        self._apply_color_chips()
        self.white_rb.setChecked(True)
        self.color_group.addButton(self.white_rb)
        self.color_group.addButton(self.black_rb)
        self.white_rb.toggled.connect(self._on_color_changed)
        color_layout.addWidget(self.white_rb)
        color_layout.addWidget(self.black_rb)
        color_layout.addStretch()
        color_outer.addWidget(color_row)
        self._tighten_box_top(color_group)
        layout.addWidget(color_group)

        # ── Starting Position (radios + revealed PGN in ONE box) ──
        # Colors track the user's board color (read when the dialog opens): the
        # derived LIGHT-square color borders this Starting Position box, and the
        # chosen DARK-square color borders the Moveset PGN box below, so the two
        # PGN areas are easy to tell apart at a glance.
        from . import config as _cfg
        _c = _cfg.get_config()
        self._light_sq, self._dark_sq = _cfg.board_colors(_c)

        pos_group = QGroupBox("Starting Position")
        pos_group.setStyleSheet(self._group_border_style(self._light_sq))
        pos_v = QVBoxLayout(pos_group)
        pos_v.setSpacing(6)

        # Opening / Custom radios
        radios_row = QHBoxLayout()
        self.pos_bg = QButtonGroup(self)
        self.opening_rb = QRadioButton("Opening")
        self.custom_rb = QRadioButton("Custom")
        self.opening_rb.setChecked(True)
        self.pos_bg.addButton(self.opening_rb)
        self.pos_bg.addButton(self.custom_rb)
        radios_row.addWidget(self.opening_rb)
        radios_row.addWidget(self.custom_rb)
        radios_row.addStretch()
        radios_row.addWidget(self._make_pin("startpos"))
        pos_v.addLayout(radios_row)

        # Revealed only for a Custom position: an inner "Starting Position PGN"
        # area that sits INSIDE the same box (no gap), with the textarea and the
        # Manual Edit / Import buttons pinned bottom-right. Define the custom
        # start by typing/pasting a PGN (its mainline's end position becomes the
        # start), or via the buttons.
        self.start_pos_reveal = QWidget()
        reveal_v = QVBoxLayout(self.start_pos_reveal)
        reveal_v.setContentsMargins(0, 2, 0, 0)

        start_pgn_label = QLabel("Starting Position PGN/FEN")
        start_pgn_label.setStyleSheet("font-weight: 600;")
        reveal_v.addWidget(start_pgn_label)

        self.start_pgn_edit = QTextEdit()
        self.start_pgn_edit.setPlaceholderText(
            "e.g. 1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4\n"
            "or\n"
            "e.g. rnbqkb1r/ppp2ppp/3p4/8/4n3/5N2/PPPP1PPP/RNBQKB1R")
        self.start_pgn_edit.setMinimumHeight(130)
        self.start_pgn_edit.textChanged.connect(self._on_start_pgn_changed)
        reveal_v.addWidget(self.start_pgn_edit)

        # Manual-edit chip (hidden until a position is set via Manual Edit):
        # a status label + Reset, mirroring the moveset box's manual chip.
        self.pos_manual_chip = QWidget()
        pchip_layout = QHBoxLayout(self.pos_manual_chip)
        pchip_layout.setContentsMargins(10, 8, 10, 8)
        self.pos_manual_chip.setStyleSheet(
            "QWidget { background: #2c3b1e; border: 1px solid #4a6327;"
            " border-radius: 6px; }"
        )
        pos_manual_label = QLabel("✏️  Position entered with Manual Edit")
        pos_manual_label.setStyleSheet(
            "color: #a3d160; font-size: 13px; border: none; background: transparent;")
        pchip_layout.addWidget(pos_manual_label, 1)
        self.reset_pos_btn = QPushButton("Reset")
        self.reset_pos_btn.setToolTip("Clear the Manual Edit position and type instead")
        self.reset_pos_btn.setStyleSheet(
            "QPushButton { background: #3d3a37; color: #e0b4a8; border: none;"
            " border-radius: 4px; padding: 4px 12px; font-size: 12px; }"
            "QPushButton:hover { background: #5a3030; color: #fff; }")
        self.reset_pos_btn.clicked.connect(self._exit_pos_manual_mode)
        pchip_layout.addWidget(self.reset_pos_btn)
        self.pos_manual_chip.setVisible(False)
        reveal_v.addWidget(self.pos_manual_chip)

        # Bottom row: status (left) + Manual Edit / Import (bottom-right).
        start_btn_row = QHBoxLayout()
        self.pos_status = QLabel("")
        self.pos_status.setStyleSheet("color: #5a9a3a; font-size: 11px;")
        start_btn_row.addWidget(self.pos_status)
        start_btn_row.addStretch()
        self.ocr_pos_btn = QPushButton("OCR")
        self.ocr_pos_btn.setToolTip(
            "Turn a chessboard image into a FEN with Helpmate Analyzer "
            "(opens in your browser), then paste the FEN above")
        self.ocr_pos_btn.clicked.connect(self._on_ocr)
        start_btn_row.addWidget(self.ocr_pos_btn)
        self.edit_pos_btn = QPushButton("Manual Edit")
        self.edit_pos_btn.setToolTip("Set the custom position by placing pieces")
        self.edit_pos_btn.clicked.connect(self._on_edit_position)
        start_btn_row.addWidget(self.edit_pos_btn)
        self.import_pos_btn = QPushButton("Import")
        self.import_pos_btn.setToolTip("Set the custom position from a .pgn or .fen file")
        self.import_pos_btn.clicked.connect(self._on_import_position)
        start_btn_row.addWidget(self.import_pos_btn)
        reveal_v.addLayout(start_btn_row)

        self.start_pos_reveal.setVisible(False)   # only shown for Custom
        pos_v.addWidget(self.start_pos_reveal)

        self.opening_rb.toggled.connect(self._on_position_mode_changed)
        layout.addWidget(pos_group)

        # Where the current custom position came from: "", "pgn", "manual",
        # "import". Lets typing clear only a typed position, never a board/file
        # one.
        self._start_pos_source = ""

        # ── PGN input ──────────────────────────────────────────
        pgn_group = QGroupBox("Moveset PGN")
        pgn_group.setStyleSheet(self._group_border_style(self._dark_sq))
        pgn_layout = QVBoxLayout(pgn_group)

        self.pgn_edit = LockedPrefixTextEdit()
        self.pgn_edit.setPlaceholderText("e.g. 1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4")
        self.pgn_edit.setMinimumHeight(130)
        pgn_layout.addWidget(self.pgn_edit)

        # File chip (hidden until a .pgn file is imported): shows filename + ✕
        self.file_chip = QWidget()
        chip_layout = QHBoxLayout(self.file_chip)
        chip_layout.setContentsMargins(10, 8, 10, 8)
        self.file_chip.setStyleSheet(
            "QWidget { background: #2c3b1e; border: 1px solid #4a6327;"
            " border-radius: 6px; }"
        )
        self.file_name_label = QLabel("")
        self.file_name_label.setStyleSheet(
            "color: #a3d160; font-size: 13px; border: none; background: transparent;")
        # Let the label take the space between the left edge and the Remove
        # button, and allow it to shrink below its text width so a long filename
        # can be elided ("…") instead of widening the chip past the window.
        self.file_name_label.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.file_name_label.setMinimumWidth(0)
        chip_layout.addWidget(self.file_name_label, 1)
        self.remove_file_btn = QPushButton("Remove")
        self.remove_file_btn.setToolTip("Remove the imported file")
        self.remove_file_btn.setStyleSheet(
            "QPushButton { background: #3d3a37; color: #e0b4a8; border: none;"
            " border-radius: 4px; padding: 4px 12px; font-size: 12px; }"
            "QPushButton:hover { background: #5a3030; color: #fff; }")
        self.remove_file_btn.clicked.connect(self._on_remove_file)
        chip_layout.addWidget(self.remove_file_btn)
        self.file_chip.setVisible(False)
        pgn_layout.addWidget(self.file_chip)

        # Manual-entry chip (hidden until moves are set via Manual Entry):
        # shows a status label + Reset, mirroring the file chip.
        self.manual_chip = QWidget()
        mchip_layout = QHBoxLayout(self.manual_chip)
        mchip_layout.setContentsMargins(10, 8, 10, 8)
        self.manual_chip.setStyleSheet(
            "QWidget { background: #2c3b1e; border: 1px solid #4a6327;"
            " border-radius: 6px; }"
        )
        manual_label = QLabel("✏️  Moves entered with Manual Input")
        manual_label.setStyleSheet(
            "color: #a3d160; font-size: 13px; border: none; background: transparent;")
        mchip_layout.addWidget(manual_label, 1)
        self.reset_manual_btn = QPushButton("Reset")
        self.reset_manual_btn.setToolTip("Clear the manual-entry moves and type instead")
        self.reset_manual_btn.setStyleSheet(
            "QPushButton { background: #3d3a37; color: #e0b4a8; border: none;"
            " border-radius: 4px; padding: 4px 12px; font-size: 12px; }"
            "QPushButton:hover { background: #5a3030; color: #fff; }")
        self.reset_manual_btn.clicked.connect(self._exit_manual_mode)
        mchip_layout.addWidget(self.reset_manual_btn)
        self.manual_chip.setVisible(False)
        pgn_layout.addWidget(self.manual_chip)

        # Button row (bottom-right of the PGN section): Manual Entry + Import
        # Bottom row: status (bottom-left, mirrors the Starting Position box)
        # + Manual Input / Import (bottom-right).
        import_row = QHBoxLayout()
        self.moveset_status = QLabel("(not set)")
        self.moveset_status.setStyleSheet("color: #5a9a3a; font-size: 11px;")
        import_row.addWidget(self.moveset_status)
        import_row.addStretch()
        self.manual_entry_btn = QPushButton("Manual Input")
        self.manual_entry_btn.setToolTip(
            "Enter moves by playing them on an interactive board")
        self.manual_entry_btn.clicked.connect(self._on_manual_entry)
        import_row.addWidget(self.manual_entry_btn)
        self.import_file_btn = QPushButton("Import")
        self.import_file_btn.setToolTip("Import a .pgn file instead of typing/pasting")
        self.import_file_btn.clicked.connect(self._on_import_file)
        import_row.addWidget(self.import_file_btn)
        pgn_layout.addLayout(import_row)

        # Keep the moveset status current as the user types in the box.
        self.pgn_edit.textChanged.connect(self._update_moveset_status)

        layout.addWidget(pgn_group)

        # Holds the moves text loaded from a file (when in file mode)
        self.loaded_pgn_text = ""
        self.manual_pgn_text = ""

        # ── Notes (free-form, shown at bottom of the card) ───
        extra_group = QGroupBox("Notes")
        extra_layout = QVBoxLayout(extra_group)
        extra_layout.setSpacing(6)   # match Starting Position's title->content gap
        extra_layout.addLayout(self._pin_row(self._make_pin("book"),
                                             QLabel("Book Notes")))
        self.book_notes_edit = RichNotesEdit()
        self.book_notes_edit.setMinimumHeight(70)
        extra_layout.addWidget(self.book_notes_edit)
        extra_layout.addLayout(self._pin_row(self._make_pin("personal"),
                                             QLabel("Personal Notes")))
        self.personal_notes_edit = RichNotesEdit()
        self.personal_notes_edit.setMinimumHeight(70)
        extra_layout.addWidget(self.personal_notes_edit)
        layout.addWidget(extra_group)

        # ── Status line (shows confirmation without a popup) ────
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #5a9a3a; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Finish the scroll area
        scroll.setWidget(content)
        outer.addWidget(scroll, 1)
        self._scroll = scroll               # kept for dynamic margin syncing

        # The scroll area reserves space on the right for its vertical
        # scrollbar, so its inner group boxes sit that much in from the window
        # edge. The Tags/button bars are pinned OUTSIDE the scroll area, so we
        # mirror that exact gutter on their right margin (synced at runtime in
        # _sync_pinned_margins so it's always pixel-accurate, scrollbar or not).

        # ── Tags (pinned at the bottom, like Anki's Add window) ─
        tags_bar = QWidget()
        tags_bar_layout = QVBoxLayout(tags_bar)
        tags_bar_layout.setContentsMargins(16, 6, 16, 0)
        self._tags_bar_layout = tags_bar_layout
        tags_group = QGroupBox("")
        tags_inner = QVBoxLayout(tags_group)
        # Use Anki's own tag widget so typing a tag autocompletes against the
        # collection's existing tags, exactly like the native Add window - but
        # with the popup capped (see _make_tag_edit) so huge tag sets don't lag.
        # Falls back to a plain line edit if TagEdit isn't available.
        self.tags_edit = _make_tag_edit(self, getattr(mw, "col", None))
        # A long single tag must never be able to widen the whole dialog. Let
        # the field ignore its content width and shrink to 0 as needed (it still
        # fills the available space), mirroring the filename label's guard. The
        # text scrolls inside the field instead of stretching the window.
        self.tags_edit.setSizePolicy(
            QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        self.tags_edit.setMinimumWidth(0)
        self.tags_edit.setPlaceholderText("e.g. #Drill #Variation5")
        tags_inner.addWidget(self.tags_edit)
        self._boxed_header_pin(tags_group, "tags", "Tags")
        tags_bar_layout.addWidget(tags_group)
        outer.addWidget(tags_bar)

        # ── Fixed action buttons (FAQ on left, Add on right) ─
        btn_bar = QWidget()
        btn_layout = QHBoxLayout(btn_bar)
        btn_layout.setContentsMargins(16, 8, 16, 12)
        self._btn_layout = btn_layout
        faq_btn = QPushButton("Help / Guide")
        faq_btn.clicked.connect(self._on_faq)
        btn_layout.addWidget(faq_btn)
        # Website button - same style as the others, with the Chess for Anki logo
        # (kept at its native colors) to the left of the text.
        import os
        self.website_btn = QPushButton("Buy me a coffee")
        self.website_btn.clicked.connect(self._on_website)
        btn_layout.addWidget(self.website_btn)
        btn_layout.addStretch()
        self.import_btn = QPushButton("Add")
        self.import_btn.setDefault(True)
        self.import_btn.clicked.connect(self._on_import)
        btn_layout.addWidget(self.import_btn)
        outer.addWidget(btn_bar)

        # Align the pinned bars once the widgets exist.
        self._sync_pinned_margins()

    def _sync_pinned_margins(self):
        """Match the pinned Tags/button bars' right margin to the exact gutter
        the scroll area reserves for its vertical scrollbar, so their right
        edges line up perfectly with the scrolling group boxes at any size."""
        try:
            gutter = self._scroll.width() - self._scroll.viewport().width()
            if gutter < 0:
                gutter = 0
            tm = self._tags_bar_layout.contentsMargins()
            self._tags_bar_layout.setContentsMargins(
                tm.left(), tm.top(), 16 + gutter, tm.bottom())
            bm = self._btn_layout.contentsMargins()
            self._btn_layout.setContentsMargins(
                bm.left(), bm.top(), 16 + gutter, bm.bottom())
        except Exception:
            pass

    def _update_filename_elision(self):
        """Elide the imported filename with '…' so it always fits the chip,
        re-fitting as the dialog is resized wider or narrower."""
        full = getattr(self, "_loaded_filename", "")
        if not full or not self.file_chip.isVisible():
            return
        try:
            fm = self.file_name_label.fontMetrics()
            avail = self.file_name_label.width() - 2
            if avail <= 0:
                return
            self.file_name_label.setText(
                fm.elidedText(full, Qt.TextElideMode.ElideRight, avail))
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_pinned_margins()
        self._update_filename_elision()

    def showEvent(self, event):
        super().showEvent(event)
        self._sync_pinned_margins()
        self._update_filename_elision()
        # Refresh the colour chips in case the board theme / piece style changed
        # in Settings while this dialog was open.
        self._apply_color_chips()

    def _apply_color_chips(self):
        """Set the white/black 'I am playing as' icons to kings on tiles in the
        user's current board theme and piece style. Falls back to glyphs."""
        try:
            from .position_editor import _king_chip_icon
            from aqt.qt import QSize as _QSize
            self.white_rb.setIcon(_king_chip_icon("w", 24))
            self.black_rb.setIcon(_king_chip_icon("b", 24))
            self.white_rb.setIconSize(_QSize(24, 24))
            self.black_rb.setIconSize(_QSize(24, 24))
        except Exception:
            self.white_rb.setText("♔  White")
            self.black_rb.setText("♚  Black")

    def _on_faq(self):
        from .faq_dialog import FaqDialog
        FaqDialog(self).exec()

    def _on_website(self):
        import webbrowser
        webbrowser.open(WEBSITE_URL)

    def _on_ocr(self):
        import webbrowser
        webbrowser.open(CHESS_OCR_URL)

    def _on_manual_entry(self):
        """Open the interactive board (non-modal-loop). On Set, the generated
        PGN is stored and the box shows a maroon 'manual entry' status."""
        if getattr(self, "loaded_pgn_text", ""):
            showWarning("Remove the imported file first to use Manual Input.")
            return
        use_custom = self.custom_rb.isChecked()
        if use_custom and not self.custom_fen:
            showWarning(
                "You chose a Custom starting position but haven't set one.\n"
                "Type a Starting Position PGN/FEN, use 'Manual Edit' / 'Import', "
                "or switch to Opening."
            )
            return
        start_fen = self.custom_fen if use_custom else ""
        player_color = "white" if self.white_rb.isChecked() else "black"

        from .manual_entry import ManualEntryDialog
        dlg = ManualEntryDialog(self, start_fen=start_fen, player_color=player_color,
                                initial_pgn=getattr(self, "manual_pgn_text", "") or "")
        # Keep a reference so the dialog isn't garbage-collected while shown.
        self._manual_dlg = dlg

        def _on_finished(code):
            try:
                if code == QDialog.DialogCode.Accepted and dlg.result_pgn:
                    self._enter_manual_mode(dlg.result_pgn)
            finally:
                self._manual_dlg = None

        dlg.finished.connect(_on_finished)
        # open() shows the dialog window-modal WITHOUT a nested event loop,
        # which avoids the QtWebEngine teardown freeze that exec() causes.
        dlg.open()

    def _enter_manual_mode(self, pgn):
        """Store manual-entry moves and show a maroon status in the PGN box."""
        self.manual_pgn_text = pgn
        self.manual_chip.setVisible(True)
        self.pgn_edit.set_prefix("")
        self.pgn_edit.setReadOnly(True)
        self.pgn_edit.setStyleSheet("QTextEdit { color: #9c4a4a; }")
        self.pgn_edit.blockSignals(True)
        self.pgn_edit.setPlainText("Using manual entry (reset to type)")
        self.pgn_edit.blockSignals(False)
        # Manual entry and file import are mutually exclusive input methods.
        self.import_file_btn.setEnabled(False)
        self._update_moveset_status()

    def _exit_manual_mode(self):
        """Clear manual-entry moves and return to typing mode."""
        self.manual_pgn_text = ""
        self.manual_chip.setVisible(False)
        self.pgn_edit.setReadOnly(False)
        self.pgn_edit.setStyleSheet("")
        self.pgn_edit.blockSignals(True)
        self.pgn_edit.clear()
        self.pgn_edit.blockSignals(False)
        self.pgn_edit.setPlaceholderText(
            "e.g. 1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4")
        self._sync_import_file_enabled()
        # Restore the locked '1... ' prefix if we're in Custom + Black.
        self._update_pgn_prefix()
        self._update_moveset_status()

    def _on_import_file(self):
        """Let the user pick a .pgn file; load it into 'file mode'."""
        # Only one file at a time. The Import button is already disabled while
        # a file is loaded, but guard here too in case this is reached anyway.
        if getattr(self, "loaded_pgn_text", ""):
            showWarning(
                "A file is already imported. Remove it first to import a different one.")
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Import PGN file", "",
            "PGN files (*.pgn);;Text files (*.txt);;All files (*)"
        )
        if not path:
            return
        try:
            text = read_pgn_file(path)
        except Exception as e:
            showWarning(f"Could not read the file:\n{e}")
            return
        if not text.strip():
            showWarning("That file appears to be empty.")
            return

        import os
        self.loaded_pgn_text = text
        base = os.path.basename(path)
        self._loaded_filename = "📄  " + base
        self.file_name_label.setToolTip(base)
        self.file_name_label.setText(self._loaded_filename)
        self.file_chip.setVisible(True)
        # Elide once the layout has positioned the now-visible chip.
        QTimer.singleShot(0, self._update_filename_elision)

        # Lock the text box (file provides the moves) and disable Import.
        # Slightly gray the box (like a disabled control) and use maroon text
        # to draw attention to the locked state.
        self.pgn_edit.set_prefix("")          # no manual prefix in file mode
        self.pgn_edit.setReadOnly(True)
        # Keep the box's normal background; just color the text maroon so it's
        # clear the box is showing the imported-file state.
        self.pgn_edit.setStyleSheet("QTextEdit { color: #9c4a4a; }")
        # Show the message as real text (placeholders render faded).
        self.pgn_edit.blockSignals(True)
        self.pgn_edit.setPlainText("Using imported file (remove attachment to type)")
        self.pgn_edit.blockSignals(False)
        self.import_file_btn.setEnabled(False)
        self.manual_entry_btn.setEnabled(False)
        self._update_moveset_status()

    def _on_remove_file(self):
        """Remove the imported file and return to typing mode."""
        self.loaded_pgn_text = ""
        self._loaded_filename = ""
        self.file_chip.setVisible(False)
        self.file_name_label.setText("")
        self.file_name_label.setToolTip("")
        self.pgn_edit.setReadOnly(False)
        self.pgn_edit.setStyleSheet("")   # restore normal editable appearance
        # Clear the "Using imported file…" message so the box is empty again.
        self.pgn_edit.blockSignals(True)
        self.pgn_edit.clear()
        self.pgn_edit.blockSignals(False)
        self.pgn_edit.setPlaceholderText(
            "e.g. 1. e4 e5 2. Nf3 Nf6 3. Nxe5 d6 4. Nf3 Nxe4")
        self._sync_import_file_enabled()
        self.manual_entry_btn.setEnabled(True)
        # Restore the locked '1... ' prefix if we're in Custom + Black.
        self._update_pgn_prefix()
        self._update_moveset_status()

    def _populate_decks(self):
        self.deck_combo.clear()
        deck_names = sorted(mw.col.decks.all_names())
        for name in deck_names:
            self.deck_combo.addItem(name)

    @staticmethod
    def _group_border_style(hex_color):
        """Stylesheet giving a QGroupBox a colored border (and a correctly
        placed title) while leaving its background to the theme."""
        return (
            f"QGroupBox {{ border: 2px solid {hex_color}; border-radius: 6px;"
            f" margin-top: 8px; padding-top: 4px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin;"
            f" subcontrol-position: top left; left: 10px; padding: 0 4px; }}"
        )

    def _on_position_mode_changed(self):
        custom = self.custom_rb.isChecked()
        # Reveal the Starting Position PGN area only for a Custom position.
        self.start_pos_reveal.setVisible(custom)
        if not custom:
            # Switching back to Opening discards any custom position and clears
            # the typed Starting Position PGN (dissolving a Manual Edit lock).
            if self.pos_manual_mode:
                self._exit_pos_manual_mode()
            self.custom_fen = ""
            self._start_pos_source = ""
            self._clear_start_pgn_box()
            self.pos_status.setText("")
        else:
            # PGN-file import isn't available for custom positions; if a file was
            # loaded under Opening, clear it so no stale attachment lingers.
            if getattr(self, "loaded_pgn_text", ""):
                self._on_remove_file()
            if self.custom_fen:
                self.pos_status.setText("✓ position set")
            else:
                self.pos_status.setText("(not set)")
        # A move sequence entered for one starting position is invalid for a
        # different one (the moves won't be legal from the new start), so clear
        # any entered moves when the Opening/Custom mode changes - same safety
        # as the color switch. Suppressed during restore/reset so programmatic
        # radio changes don't wipe intended moves.
        if not getattr(self, "_suppress_color_clear", False):
            self._clear_moveset_on_color_change()
        self._sync_import_file_enabled()
        self._update_pgn_prefix()

    def _sync_import_file_enabled(self):
        """Enable the PGN-file Import button only on a standard Opening with
        typing active. Custom positions can't use file import - a file's move
        numbering can't be reconciled with a custom side-to-move (e.g. a Black-
        to-move start), so the user enters those moves by typing or Manual Input
        instead. Also stays disabled while a file or manual line is loaded."""
        custom = self.custom_rb.isChecked()
        busy = bool(getattr(self, "manual_pgn_text", "")) or \
               bool(getattr(self, "loaded_pgn_text", ""))
        self.import_file_btn.setEnabled(not custom and not busy)

    def _on_color_changed(self):
        # Keep the custom position's pieces exactly where they are; only the
        # side-to-move changes to match the new color (the board orientation
        # is applied when the card is studied). Like flipping a real board:
        # a pawn on e4 stays on e4.
        if self.custom_fen:
            new_stm = "b" if self.black_rb.isChecked() else "w"
            self.custom_fen = self._set_fen_side_to_move(self.custom_fen, new_stm)
        # A move sequence entered for one color is invalid for the other (the
        # very first ply would belong to the wrong side), so clear any saved
        # moves when the color flips - preventing impossible cards. Guarded by
        # a flag so restoring/prefilling color doesn't wipe intended moves.
        if not getattr(self, "_suppress_color_clear", False):
            self._clear_moveset_on_color_change()
        self._update_pgn_prefix()

    def _clear_moveset_on_color_change(self):
        """Drop any typed / imported / manual-entry moves (used when the player
        color changes). No-op when nothing is entered."""
        had = (bool(getattr(self, "loaded_pgn_text", "")) or
               bool(getattr(self, "manual_pgn_text", "")) or
               bool(self.pgn_edit.user_text().strip()))
        if not had:
            return
        if getattr(self, "loaded_pgn_text", ""):
            self._on_remove_file()
        if getattr(self, "manual_pgn_text", ""):
            self._exit_manual_mode()
        self.pgn_edit.clear()
        self._update_moveset_status()

    @staticmethod
    def _set_fen_side_to_move(fen: str, stm: str) -> str:
        """Return `fen` with its side-to-move field set to `stm` ('w'/'b')."""
        parts = fen.strip().split()
        if len(parts) >= 2:
            parts[1] = stm
            return " ".join(parts)
        # Malformed; rebuild minimal fields
        placement = parts[0] if parts else fen.strip()
        return f"{placement} {stm}"

    def _update_pgn_prefix(self):
        """Show a locked, grayed-out '1... ' prefix in the PGN box only when
        the user is building a Custom position AND playing as Black - since
        in that case the first move written is Black's reply."""
        # Guard: during construction the widgets may not all exist yet.
        if not hasattr(self, "pgn_edit"):
            return
        if not hasattr(self, "custom_rb") or not hasattr(self, "black_rb"):
            return
        # In file mode or manual-entry mode the PGN box is read-only and shows
        # its own status message, not a prefix.
        if getattr(self, "loaded_pgn_text", "") or getattr(self, "manual_pgn_text", ""):
            return
        custom = self.custom_rb.isChecked()
        is_black = self.black_rb.isChecked()
        if custom and is_black:
            self.pgn_edit.set_prefix("1... ")
        else:
            self.pgn_edit.set_prefix("")

    def _on_edit_position(self):
        player_color = "white" if self.white_rb.isChecked() else "black"
        editor = PositionEditor(self, initial_fen=self.custom_fen,
                                player_color=player_color)
        if editor.exec():
            self.custom_fen = getattr(editor, "result_fen", "")
            if self.custom_fen:
                # A board-placed position overrides any typed Starting Position
                # PGN, so there's a single source of truth. Lock the box until
                # Reset so typing can't silently overwrite the placed position.
                self._start_pos_source = "manual"
                self._enter_pos_manual_mode()
            elif self.pos_manual_mode:
                # Editor returned no position: don't leave a stale lock up.
                self._exit_pos_manual_mode()
        # If cancelled, keep whatever we had (or nothing)

    def _enter_pos_manual_mode(self):
        """Lock the Starting Position box while a Manual Edit position is the
        source of truth: maroon status text, read-only, green chip with Reset.
        Mirrors the moveset box's manual-entry mode."""
        self.pos_manual_mode = True
        self.pos_manual_chip.setVisible(True)
        self.start_pgn_edit.setReadOnly(True)
        self.start_pgn_edit.setStyleSheet("QTextEdit { color: #9c4a4a; }")
        self.start_pgn_edit.blockSignals(True)
        self.start_pgn_edit.setPlainText("Using manual edit (reset to type)")
        self.start_pgn_edit.blockSignals(False)
        # Manual Edit and file import are mutually exclusive input methods.
        self.import_pos_btn.setEnabled(False)
        self.pos_status.setText("✓ position set")

    def _exit_pos_manual_mode(self):
        """Clear the Manual Edit position and return the box to typing mode."""
        self.pos_manual_mode = False
        self.custom_fen = ""
        self._start_pos_source = ""
        self.pos_manual_chip.setVisible(False)
        self.start_pgn_edit.setReadOnly(False)
        self.start_pgn_edit.setStyleSheet("")
        self._clear_start_pgn_box()
        self.import_pos_btn.setEnabled(True)
        self.pos_status.setText("(not set)")

    def _on_import_position(self):
        """Set the custom starting position from a .pgn or .fen file. A bare
        FEN is used directly; a PGN uses its [FEN \"...\"] tag if present,
        otherwise the position after the mainline's moves. Overwrites any
        position set via 'Manual Edit'."""
        from aqt.qt import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Import position from PGN or FEN", "",
            "PGN or FEN files (*.pgn *.fen);;All files (*)")
        if not path:
            return
        try:
            text = read_pgn_file(path)
        except Exception as e:
            showWarning(f"Couldn't read the file:\n{e}")
            return
        fen = self._fen_from_text(text)
        if not fen:
            showWarning(
                "Couldn't determine a position from that file.\n\n"
                "Make sure it's a valid FEN, or a PGN with a [FEN \"…\"] tag "
                "or a valid sequence of moves.")
            return
        # The custom position's side-to-move is the color you're studying as.
        stm = "b" if self.black_rb.isChecked() else "w"
        if self.pos_manual_mode:
            # Importing replaces a Manual Edit position; dissolve the lock first.
            self._exit_pos_manual_mode()
        self.custom_fen = self._set_fen_side_to_move(fen, stm)
        # An imported file overrides any typed Starting Position PGN.
        self._clear_start_pgn_box()
        self._start_pos_source = "import"
        self.pos_status.setText("✓ position set (imported)")
        self._update_pgn_prefix()

    def _set_status(self, text):
        """Set the green status line, hard-capped so no message can ever
        widen the dialog. A character cap (not QLabel word wrap, which
        inflates the surrounding layout's height negotiation) keeps the
        label a fixed-height single line."""
        if len(text) > 90:
            text = text[:89] + "\u2026"
        self.status_label.setText(text)

    def _update_moveset_status(self):
        """Reflect whether the moveset has content: a green '✓ moves set' when a
        file is imported, manual-entry moves exist, or text is typed; otherwise
        '(not set)'. Mirrors the Starting Position box's status."""
        if not hasattr(self, "moveset_status"):
            return
        if getattr(self, "loaded_pgn_text", ""):
            self.moveset_status.setText("✓ moves set (imported)")
        elif getattr(self, "manual_pgn_text", ""):
            self.moveset_status.setText("✓ moves set")
        elif self.pgn_edit.user_text().strip():
            self.moveset_status.setText("✓ moves set")
        else:
            self.moveset_status.setText("(not set)")

    def _clear_start_pgn_box(self):
        """Empty the Starting Position PGN box without re-triggering its
        textChanged handler."""
        if not hasattr(self, "start_pgn_edit"):
            return
        self.start_pgn_edit.blockSignals(True)
        self.start_pgn_edit.clear()
        self.start_pgn_edit.blockSignals(False)

    def _on_start_pgn_changed(self):
        """Derive the custom starting position from the typed/pasted Starting
        Position PGN: the position after its mainline becomes the start, with
        the side-to-move set to the color being studied (same as Import)."""
        text = self.start_pgn_edit.toPlainText().strip()
        if not text:
            # Only clear a position that itself came from typing - never wipe one
            # set via Manual Edit or Import.
            if self._start_pos_source == "pgn":
                self.custom_fen = ""
                self._start_pos_source = ""
                self.pos_status.setText("(not set)")
            return
        try:
            fen = self._fen_from_text(text)
        except Exception:
            fen = ""
        if not fen:
            self.custom_fen = ""
            self._start_pos_source = "pgn"
            self.pos_status.setText("(not set)")
            return
        stm = "b" if self.black_rb.isChecked() else "w"
        self.custom_fen = self._set_fen_side_to_move(fen, stm)
        self._start_pos_source = "pgn"
        self.pos_status.setText("✓ position set")

    @staticmethod
    def _board_to_fen(board, turn):
        rows = []
        for r in range(7, -1, -1):           # rank 8 down to rank 1
            row, empty = "", 0
            for f in range(8):
                p = board[r][f]
                if p is None:
                    empty += 1
                    continue
                if empty:
                    row += str(empty)
                    empty = 0
                row += p[1].upper() if p[0] == "w" else p[1].lower()
            if empty:
                row += str(empty)
            rows.append(row)
        return "/".join(rows) + f" {turn}"

    def _fen_from_pgn(self, text):
        import re
        m = re.search(r'\[FEN\s+"([^"]+)"\]', text)
        if m:
            return m.group(1).strip()
        # No FEN tag - play the mainline and use the resulting position.
        try:
            from .pgn_parser import expand_variations, read_pgn_file
            from .chess_logic import _start_board, apply_san
        except Exception:
            return ""
        lines = expand_variations(text)
        if not lines or not lines[0]:
            return ""
        board, turn = _start_board()
        ep = None
        for san in lines[0]:
            try:
                ep = apply_san(board, turn, san, ep)
                turn = "b" if turn == "w" else "w"
            except Exception:
                break          # stop at the first move we can't apply
        return self._board_to_fen(board, turn)

    def _fen_from_text(self, text):
        """Return a FEN from text that may be a bare FEN, a PGN with a
        [FEN \"...\"] tag, or PGN moves. A valid bare FEN is used directly;
        otherwise the text is treated as PGN."""
        t = (text or "").strip()
        if not t:
            return ""
        if _is_valid_fen(t):
            return t
        return self._fen_from_pgn(t)

    def _make_pin(self, which):
        """A small check to keep this field's value for the next card. The
        checkbox's state and the field's value are NOT persisted on toggle -
        they commit to config only when the user presses Add (see
        _persist_sticky), so nothing is remembered until a card is actually
        created. The box just reflects the last-committed state on open."""
        cb = QCheckBox("Pin")
        cb.setToolTip("Pin this field's value so it carries to the next card "
                      "instead of clearing it. Saved when you press Add.")
        key = STICKY_KEYS[which]
        try:
            cb.setChecked(bool(self._sticky_cfg.get(key, False)))
        except Exception:
            pass
        try:
            cb.setStyleSheet("QCheckBox { font-size: 11px; color: #9a9a9a; }")
        except Exception:
            pass
        self._pins[which] = cb
        return cb

    def _pinned(self, which):
        try:
            return bool(self._pins[which].isChecked())
        except Exception:
            return False

    def _persist_sticky(self):
        """Commit pin states AND the current values of pinned fields to config.
        Called only on a successful Add, so nothing is remembered until the
        user actually creates a card. One small config write per Add - no
        polling, no per-review cost."""
        try:
            from . import config as _cfg
            c = _cfg.get_config()
        except Exception:
            return
        for which, key in STICKY_KEYS.items():
            c[key] = self._pinned(which)
        # Save each pinned field's current value (unpinned ones are left as-is
        # so re-pinning later still finds a sensible last value).
        try:
            if self._pinned("deck"):
                c["sticky_val_deck"] = self.deck_combo.currentText()
            if self._pinned("title"):
                c["sticky_val_title"] = self.title_edit.text()
            if self._pinned("color"):
                c["sticky_val_color"] = ("black" if self.black_rb.isChecked()
                                         else "white")
            if self._pinned("startpos"):
                c["sticky_val_startpos_fen"] = (
                    self.custom_fen if self.custom_rb.isChecked() else "")
            if self._pinned("book"):
                c["sticky_val_book"] = self.book_notes_edit.toHtml()
            if self._pinned("personal"):
                c["sticky_val_personal"] = self.personal_notes_edit.toHtml()
            if self._pinned("tags"):
                c["sticky_val_tags"] = self.tags_edit.text()
        except Exception:
            pass
        try:
            _cfg.save_config(c)
            self._sticky_cfg = c
        except Exception:
            pass

    def _restore_sticky_values(self):
        """On dialog open, load the last-committed values of pinned fields into
        their widgets. Runs once at construction - no ongoing cost."""
        c = self._sticky_cfg or {}
        try:
            if c.get("sticky_title") and c.get("sticky_val_title"):
                self.title_edit.setText(c["sticky_val_title"])
            if c.get("sticky_color"):
                self._suppress_color_clear = True
                try:
                    if c.get("sticky_val_color") == "black":
                        self.black_rb.setChecked(True)
                    else:
                        self.white_rb.setChecked(True)
                finally:
                    self._suppress_color_clear = False
            if c.get("sticky_book") and c.get("sticky_val_book"):
                self.book_notes_edit.setHtml(c["sticky_val_book"])
            if c.get("sticky_personal") and c.get("sticky_val_personal"):
                self.personal_notes_edit.setHtml(c["sticky_val_personal"])
            if c.get("sticky_tags") and c.get("sticky_val_tags"):
                self.tags_edit.setText(c["sticky_val_tags"])
            if c.get("sticky_deck") and c.get("sticky_val_deck"):
                idx = self.deck_combo.findText(c["sticky_val_deck"])
                if idx >= 0:
                    self.deck_combo.setCurrentIndex(idx)
            if c.get("sticky_startpos") and c.get("sticky_val_startpos_fen"):
                self._restore_custom_position(c["sticky_val_startpos_fen"])
        except Exception:
            pass

    def _restore_custom_position(self, fen):
        """Re-apply a saved custom starting position to the UI."""
        try:
            self.custom_fen = fen
            self._start_pos_source = "restored"
            self._suppress_color_clear = True
            try:
                self.custom_rb.setChecked(True)
                self._on_position_mode_changed()   # reveals the custom area
            finally:
                self._suppress_color_clear = False
            self.pos_status.setText("✓ position set (kept)")
            self._update_pgn_prefix()
        except Exception:
            pass

    # The Starting Position box's radios sit 4px below its top border (its
    # frame title lives ON the border, so padding-top is just 4). Boxes whose
    # title is INSIDE the box have no border title but Qt still reserves the
    # title band, doubling the top gap. This stylesheet reclaims that band so
    # the in-box header row starts at the same 4px, matching the reference.
    _TIGHT_TOP_QSS = ("QGroupBox { margin-top: 0px; padding-top: 4px; }"
                      "QGroupBox::title { max-height: 0px; }")

    def _tighten_box_top(self, group):
        try:
            group.setStyleSheet(self._TIGHT_TOP_QSS)
        except Exception:
            pass

    def _boxed_header_pin(self, group, which, title, bold=True):
        """Put a bold section header and its pin on ONE row at the top of the
        box (the box's own frame title is dropped to avoid duplication). This
        is the clean Notes-style arrangement: title left, pin right, on the
        same line - used for Deck, Title, Player Color, and Tags so all match.
        """
        pin = self._make_pin(which)
        lbl = QLabel(title)
        if bold:
            f = lbl.font()
            f.setBold(True)
            lbl.setFont(f)
        row = self._pin_row(pin, lbl)
        lay = group.layout()
        try:
            lay.insertLayout(0, row)
        except Exception:
            lay.addLayout(row)
        self._tighten_box_top(group)
        return pin

    def _pin_row(self, pin, label=None):
        """A thin right-aligned row holding the pin (optionally with a left-side
        label). Shared by group-box pins and the inline Notes pins so all seven
        are visually identical."""
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(4)
        if label is not None:
            row.addWidget(label)
        row.addStretch()
        row.addWidget(pin)
        return row

    def _format_bad_move(self, bad_idx, bad_move, start_fen):
        """Produce a label like '6. Nc5' (white) or '6... Rd1' (black) for
        the move at position bad_idx (0-based) in a line.

        The first mover is White unless a custom FEN says Black is to move."""
        first_is_white = True
        if start_fen:
            parts = start_fen.strip().split()
            if len(parts) > 1 and parts[1] == "b":
                first_is_white = False

        # Side to move alternates each ply starting from first_is_white.
        is_white_move = (bad_idx % 2 == 0) == first_is_white

        # Full move number: increments after each Black move. Determine how
        # many full moves precede this ply.
        if first_is_white:
            move_no = bad_idx // 2 + 1
        else:
            # first ply is Black's move number 1
            move_no = (bad_idx + 1) // 2 + 1

        if is_white_move:
            return f"{move_no}. {bad_move}"
        else:
            return f"{move_no}... {bad_move}"

    def _on_import(self):
        title = self.title_edit.text().strip()
        tags_text = self.tags_edit.text().strip()
        # If a file was imported, use its contents; if moves were entered via
        # Manual Entry, use those; otherwise read the typed moves (excluding any
        # locked '1... ' prefix). Side-to-move comes from the position/color.
        if self.loaded_pgn_text:
            pgn_text = self.loaded_pgn_text.strip()
        elif self.manual_pgn_text:
            pgn_text = self.manual_pgn_text.strip()
        else:
            pgn_text = self.pgn_edit.user_text().strip()
        player_color = "white" if self.white_rb.isChecked() else "black"
        book_notes_text = _notes_field_html(self.book_notes_edit)
        personal_notes_text = _notes_field_html(self.personal_notes_edit)
        deck_name = self.deck_combo.currentText()

        # Validation
        if not title:
            showWarning("Please enter a title for this opening.")
            self.title_edit.setFocus()
            return
        if not pgn_text:
            showWarning("Please paste a PGN.")
            self.pgn_edit.setFocus()
            return

        # Custom-position validation
        use_custom = self.custom_rb.isChecked()
        if use_custom and not self.custom_fen:
            showWarning(
                "You chose a Custom starting position but haven't set one.\n"
                "Type a Starting Position PGN/FEN, use 'Manual Edit' / 'Import', "
                "or switch to Opening."
            )
            return

        start_fen = self.custom_fen if use_custom else ""

        # Expand any variations into separate complete lines
        try:
            lines = expand_variations(pgn_text)
        except ValueError as e:
            showWarning(str(e))
            return

        if not lines:
            showWarning("No moves found in PGN. Please check the format.")
            return

        # ── Validate every move in every line BEFORE creating cards ──
        # If any move is illegal from the starting position, abort the
        # whole import without creating anything or clearing the form.
        from . import chess_logic
        fen_for_check = start_fen if use_custom else None
        for line_idx, moves in enumerate(lines, start=1):
            ok, bad_idx, bad_move = chess_logic.validate_line(moves, fen_for_check)
            if not ok:
                # Reconstruct a human-friendly move label, e.g. "6. Nc5" or
                # "6... Rd1", based on position in the line and side to move.
                label = self._format_bad_move(bad_idx, bad_move, fen_for_check)
                line_note = (f"  (in line {line_idx})" if len(lines) > 1 else "")
                showWarning(
                    f"Notation error. Move {label} is not valid{line_note}.\n\n"
                    f"No cards were created. Please fix the PGN and try again."
                )
                return

        # Add note(s) to collection
        col = mw.col
        deck_id = col.decks.id(deck_name)
        col.decks.select(deck_id)

        tag_list = col.tags.split(tags_text) if tags_text else []
        multi = len(lines) > 1

        for idx, moves in enumerate(lines, start=1):
            # When there are branches, suffix the title so cards are
            # distinguishable (e.g. "Ruy Lopez (line 2)"). Single lines
            # keep the plain title.
            card_title = f"{title} (line {idx})" if multi else title

            note = create_note(
                col,
                title=card_title,
                player_color=player_color,
                moves=moves,
                start_fen=start_fen,
                book_notes=book_notes_text,
                personal_notes=personal_notes_text,
            )
            if tag_list:
                note.tags = list(tag_list)
            col.add_note(note, deck_id)

        mw.reset()

        # Commit pin states and pinned field values now that a card was
        # actually created (nothing sticky is saved until Add).
        self._persist_sticky()

        # ── Reset for next entry (honoring sticky-field pins) ────
        # Each field clears UNLESS its pin is checked. Deck and Tags are
        # pinned by default (their historical behavior); everything else
        # clears by default. Moves/PGN always clear - keeping them would
        # recreate the same card.
        if not self._pinned("title"):
            self.title_edit.clear()
        if not self._pinned("book"):
            self.book_notes_edit.clear()
        if not self._pinned("personal"):
            self.personal_notes_edit.clear()
        if not self._pinned("color"):
            self._suppress_color_clear = True
            try:
                self.white_rb.setChecked(True)     # color back to White
            finally:
                self._suppress_color_clear = False
        if not self._pinned("startpos"):
            self._suppress_color_clear = True
            try:
                self.opening_rb.setChecked(True)   # position back to Opening
            finally:
                self._suppress_color_clear = False
            self.custom_fen = ""
            self._start_pos_source = ""
            self._clear_start_pgn_box()
            self.start_pos_reveal.setVisible(False)
            self.pos_status.setText("")
        if not self._pinned("tags"):
            self.tags_edit.setText("")
        # Deck: pinned by default; when unpinned, fall back to the first deck.
        if not self._pinned("deck"):
            try:
                if self.deck_combo.count() > 0:
                    self.deck_combo.setCurrentIndex(0)
            except Exception:
                pass
        # Moves/PGN ALWAYS clear - a persisted move list would duplicate cards.
        # Clear any imported file and return the PGN box to typing mode.
        if self.loaded_pgn_text:
            self._on_remove_file()
        # Clear any manual-entry moves too.
        if self.manual_pgn_text:
            self._exit_manual_mode()
        self.pgn_edit.set_prefix("")       # remove any '1... ' prefix
        self.pgn_edit.clear()
        self._update_moveset_status()
        self.title_edit.setFocus()

        # Count-only confirmations: titles and tag lists are unbounded user
        # text and were stretching the dialog border. The card's name lives in
        # the deck browser; here the count is the confirmation that matters.
        if multi:
            n = len(lines)
            self._set_status(f"✓ Added {n} line{'s' if n != 1 else ''}")
            tooltip(f"Added {n} card{'s' if n != 1 else ''}", period=1500)
        else:
            move_count = len(lines[0])
            self._set_status(
                f"✓ Added 1 line  ({move_count} moves, {player_color})")
            tooltip("Added 1 card", period=1200)
