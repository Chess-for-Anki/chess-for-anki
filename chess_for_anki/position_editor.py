"""
Custom position editor for Chess for Anki.

Presents a blank 8x8 board. Click a square to open a piece picker
(white/black toggle + the 6 piece types shown as Lichess SVG icons).
Click an occupied square to remove its piece. Only one king per color
is allowed; the king icon is disabled when that color's king exists.

The board is oriented to the player's color, and that color is the side
to move. OK validates the position (legality checks) and, if valid,
builds a FEN and returns it; Cancel returns None.
"""

import os
import re

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QPushButton,
    QLabel, QRadioButton, QButtonGroup, QFrame, Qt, QSize,
    QByteArray, QIcon, QMenu, QWidgetAction, QWidget, QPixmap, QPainter,
    QScrollArea
)
from aqt.utils import showInfo

# QSvgRenderer lives in QtSvg; aqt.qt usually re-exports it, but fall back
# to the PyQt6 module directly if not.
try:
    from aqt.qt import QSvgRenderer
except ImportError:
    try:
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:
        from PyQt5.QtSvg import QSvgRenderer


# ── Load piece SVGs from pieces.js ──────────────────────────────
def _load_piece_svgs():
    path = os.path.join(os.path.dirname(__file__), "web", "pieces.js")
    with open(path, "r", encoding="utf-8") as f:
        js = f.read()
    pieces = {}
    for m in re.finditer(r"(\w{2}):\s*'(.*?)',?\n", js, re.DOTALL):
        key, val = m.group(1), m.group(2)
        if len(key) == 2 and key[0] in "wb":
            pieces[key] = val
    return pieces


_PIECE_SVGS = _load_piece_svgs()
_CURRENT_PIECE_SET = "cburnett"   # set from config when the editor opens


def _piece_svg_markup(code: str, piece_set: str = None) -> str:
    ps = piece_set or _CURRENT_PIECE_SET
    if ps in ("blank", "blindfold") and piece_set is None:
        # The position editor exists to PLACE pieces: invisible pieces
        # (blindfold) or six identical discs per colour in the palette (blank)
        # would make it unusable, so the editor's implicit path falls back to
        # Classic. Callers that pass an explicit set (the Config preview)
        # still get the honest rendering below.
        ps = "cburnett"
    if ps == "blindfold":
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" '
                'width="45" height="45"></svg>')
    if ps == "blank":
        try:
            from . import config as cfg
            return cfg.blank_svg(code)
        except Exception:
            pass
    if ps == "letters":
        try:
            from . import config as cfg
            return cfg.letters_svg(code)
        except Exception:
            pass
    inner = _PIECE_SVGS.get(code, "")
    if ps == "wooden":
        try:
            from . import config as cfg
            inner = cfg.wooden_recolor(inner, code[0] == "w")
        except Exception:
            pass
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 45 45" '
            'width="45" height="45">' + inner + "</svg>")


def _piece_icon(code: str, size: int = 44, piece_set: str = None) -> QIcon:
    svg = _piece_svg_markup(code, piece_set).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg))
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return QIcon(pix)


def _king_chip_icon(color: str, size: int = 26, light: str = None,
                    dark: str = None, piece_set: str = None) -> QIcon:
    """Render a king on a tile coloured to match the user's board theme. The
    tile uses the chosen light square colour (dark square tone as the border),
    and the king uses the user's current piece style. color: 'w' or 'b'."""
    from aqt.qt import QColor, QRectF, QBrush, QPen
    # Pull theme + piece style from config so the chip always reflects current
    # settings (fixes a stale-icon bug when switching styles).
    if light is None or dark is None or piece_set is None:
        try:
            from . import config as cfg
            c = cfg.get_config()
            cl, cd = cfg.board_colors(c)
            if light is None:
                light = cl
            if dark is None:
                dark = cd
            if piece_set is None:
                piece_set = c.get("piece_set", "cburnett")
                if piece_set == "blindfold":
                    piece_set = "cburnett"  # chips must show the king
        except Exception:
            light = light or "#f0d9b5"
            dark = dark or "#b58863"
            piece_set = piece_set or "cburnett"
    code = ("wK" if color == "w" else "bK")

    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
    # rounded tile background in the theme's light-square colour
    painter.setBrush(QBrush(QColor(light)))
    painter.setPen(QPen(QColor(dark), 1.5))
    r = QRectF(1, 1, size - 2, size - 2)
    painter.drawRoundedRect(r, 5, 5)
    # king SVG centered, with a little padding
    pad = 3
    svg = _piece_svg_markup(code, piece_set).encode("utf-8")
    renderer = QSvgRenderer(QByteArray(svg))
    renderer.render(painter, QRectF(pad, pad, size - 2 * pad, size - 2 * pad))
    painter.end()
    return QIcon(pix)


PIECE_TYPES = ["k", "q", "r", "b", "n", "p"]
PIECE_NAMES = {"k": "King", "q": "Queen", "r": "Rook",
               "b": "Bishop", "n": "Knight", "p": "Pawn"}

LIGHT = "#f0d9b5"
DARK = "#b58863"


class PositionEditor(QDialog):
    def __init__(self, parent=None, initial_fen: str = "", player_color: str = "white"):
        super().__init__(parent)
        self.setWindowTitle("Chess for Anki - Manual Edit")
        self.setModal(True)
        self.resize(560, 620)

        # board[rank][file] = piece code like 'wK' or None. rank 0 = rank1.
        self.board = [[None] * 8 for _ in range(8)]
        # The side to move is the color the user is playing as (their first
        # PGN move comes from this position), so it's derived, not chosen here.
        self.player_color = "black" if player_color == "black" else "white"
        self.side_to_move = "b" if self.player_color == "black" else "w"
        self.flip = (self.player_color == "black")
        self.cell_buttons = {}  # (file, rank) -> QPushButton

        # Board colors from the user's settings (light/dark derived from one
        # base color). Falls back to the classic tan board.
        self._texture = "solid"
        try:
            from . import config as cfg
            c = cfg.get_config()
            self._light, self._dark = cfg.board_colors(c)
            self._texture = c.get("board_texture", "solid")
            global _CURRENT_PIECE_SET
            _CURRENT_PIECE_SET = c.get("piece_set", "cburnett")
        except Exception:
            self._light, self._dark = LIGHT, DARK

        if initial_fen:
            self._load_fen(initial_fen)

        self._build_ui()
        self._refresh_all()

    # ── FEN helpers ─────────────────────────────────────────────
    def _load_fen(self, fen):
        try:
            parts = fen.strip().split()
            rows = parts[0].split("/")
            for r in range(8):
                rank_idx = 7 - r
                file_idx = 0
                for ch in rows[r]:
                    if ch.isdigit():
                        file_idx += int(ch)
                    else:
                        color = "w" if ch.isupper() else "b"
                        self.board[rank_idx][file_idx] = color + ch.upper()
                        file_idx += 1
            # NOTE: side to move is derived from the player's color, not the
            # FEN, so we intentionally don't read parts[1] here.
        except Exception:
            pass

    def _count_king(self, color):
        target = color + "K"
        return sum(
            1 for r in range(8) for f in range(8) if self.board[r][f] == target
        )

    def to_fen(self):
        rows = []
        for r in range(7, -1, -1):  # rank 8 down to rank 1
            row = ""
            empty = 0
            for f in range(8):
                p = self.board[r][f]
                if p is None:
                    empty += 1
                else:
                    if empty:
                        row += str(empty)
                        empty = 0
                    letter = p[1]
                    row += letter.upper() if p[0] == "w" else letter.lower()
            if empty:
                row += str(empty)
            rows.append(row)
        placement = "/".join(rows)
        # StartFEN keeps placement + side to move only: castling rights are
        # assumed from placement everywhere, so the old " - - 0 1" tail was
        # both inaccurate and noise.
        return f"{placement} {self.side_to_move}"

    def _validate(self):
        """Run all legality checks. Returns a list of error message strings
        (empty if the position is valid)."""
        from . import chess_logic

        b = self.board
        errors = []

        # 1. Exactly one king of each color
        wk = self._count_king("w")
        bk = self._count_king("b")
        if wk == 0:
            errors.append("There is no White king on the board. Add exactly one White king.")
        elif wk > 1:
            errors.append("There is more than one White king. Only one is allowed.")
        if bk == 0:
            errors.append("There is no Black king on the board. Add exactly one Black king.")
        elif bk > 1:
            errors.append("There is more than one Black king. Only one is allowed.")

        # 2. No pawns on rank 1 or rank 8
        pawn_on_first = any(b[0][f] is not None and b[0][f][1] == "P" for f in range(8))
        pawn_on_last = any(b[7][f] is not None and b[7][f][1] == "P" for f in range(8))
        if pawn_on_first:
            errors.append("A pawn is on the 1st rank, which is impossible "
                          "(it would have promoted). Remove or move it.")
        if pawn_on_last:
            errors.append("A pawn is on the 8th rank, which is impossible "
                          "(it would have promoted). Remove or move it.")

        # 4. No more than 8 pawns per color
        wp = sum(1 for r in range(8) for f in range(8) if b[r][f] == "wP")
        bp = sum(1 for r in range(8) for f in range(8) if b[r][f] == "bP")
        if wp > 8:
            errors.append(f"There are {wp} White pawns. A side can have at most 8 pawns.")
        if bp > 8:
            errors.append(f"There are {bp} Black pawns. A side can have at most 8 pawns.")

        # 5. No more than 16 pieces per color
        wtotal = sum(1 for r in range(8) for f in range(8)
                     if b[r][f] is not None and b[r][f][0] == "w")
        btotal = sum(1 for r in range(8) for f in range(8)
                     if b[r][f] is not None and b[r][f][0] == "b")
        if wtotal > 16:
            errors.append(f"There are {wtotal} White pieces. A side can have at most 16.")
        if btotal > 16:
            errors.append(f"There are {btotal} Black pieces. A side can have at most 16.")

        # The remaining checks rely on both kings being present exactly once.
        kings_ok = (wk == 1 and bk == 1)

        # 3. Kings not adjacent (needs both kings)
        if kings_ok:
            wpos = chess_logic.find_king(b, "w")
            bpos = chess_logic.find_king(b, "b")
            if max(abs(wpos[0] - bpos[0]), abs(wpos[1] - bpos[1])) <= 1:
                errors.append("The two kings are touching, which is not a legal "
                              "position. Separate them by at least one square.")

        mover = self.side_to_move          # 'w' or 'b'
        waiting = "b" if mover == "w" else "w"

        # 6. The side NOT to move must not be in check (needs both kings)
        if kings_ok and chess_logic.in_check(b, waiting):
            waiting_name = "Black" if waiting == "b" else "White"
            mover_name = "White" if mover == "w" else "Black"
            errors.append(f"The {waiting_name} king is in check, but it's "
                          f"{mover_name}'s turn to move. The side not to move "
                          f"cannot be in check. (The side to move matches the "
                          f"color you're playing as.)")

        # 7. The side to move must have at least one legal move (needs kings).
        #    Skip if the side-not-to-move is already in check, since that
        #    position is illegal anyway and the mate/stalemate label would
        #    be misleading.
        if kings_ok and not chess_logic.in_check(b, waiting):
            if not chess_logic.has_legal_move(b, mover):
                mover_name = "White" if mover == "w" else "Black"
                if chess_logic.in_check(b, mover):
                    errors.append(f"This position is already checkmate ({mover_name} "
                                  f"has no legal moves). There would be nothing to practice.")
                else:
                    errors.append(f"This position is a stalemate ({mover_name} has no "
                                  f"legal moves). There would be nothing to practice.")

        return errors

    # ── UI ──────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Color the side word with the user's own board palette: "White" uses the
        # light-square color, "Black" the dark-square color. It self-themes with
        # whatever board colors they've chosen (and is theirs to adjust).
        if self.flip:
            perspective = ("Board shown from "
                           f"<b style='color:{self._dark}'>Black's</b> perspective.")
        else:
            perspective = ("Board shown from "
                           f"<b style='color:{self._light}'>White's</b> perspective.")
        info = QLabel(
            "Click a square to place a piece. Click a piece to remove it.  "
            + perspective
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        info.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(info)

        # Board grid (with a-h / 1-8 coordinate labels around it)
        board_wrap = QHBoxLayout()
        board_wrap.addStretch()
        grid = QGridLayout()
        grid.setSpacing(0)

        FILES = ["a", "b", "c", "d", "e", "f", "g", "h"]
        coord_css = "color:#888; font-size:11px; font-weight:600;"

        # Determine display order. White at bottom (default): top row = rank8.
        # Black perspective flips both ranks and files.
        display_ranks = [1, 2, 3, 4, 5, 6, 7, 8] if self.flip \
            else [8, 7, 6, 5, 4, 3, 2, 1]
        display_files = [7, 6, 5, 4, 3, 2, 1, 0] if self.flip \
            else [0, 1, 2, 3, 4, 5, 6, 7]

        # Grid columns: col 0 = rank labels, cols 1..8 = board, then file row.
        for drow, rank_label in enumerate(display_ranks):
            rank = rank_label - 1  # 0-based internal rank
            # Rank number label on the left
            rlab = QLabel(str(rank_label))
            rlab.setStyleSheet(coord_css)
            rlab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rlab.setFixedWidth(18)
            grid.addWidget(rlab, drow, 0)

            for dcol, file in enumerate(display_files):
                btn = QPushButton()
                btn.setFixedSize(QSize(54, 54))
                btn.setIconSize(QSize(46, 46))
                light = (rank + file) % 2 == 1
                color = self._light if light else self._dark
                try:
                    from . import config as cfg
                    bg = cfg.qt_square_bg(color, self._texture)
                except Exception:
                    bg = color
                btn.setStyleSheet(
                    f"QPushButton {{ background:{bg}; border:none; }}"
                    f"QPushButton:hover {{ background:{bg}; "
                    f"border: 2px solid #629924; }}"
                )
                btn.clicked.connect(
                    lambda _checked, f=file, r=rank: self._on_square_clicked(f, r)
                )
                self.cell_buttons[(file, rank)] = btn
                grid.addWidget(btn, drow, dcol + 1)

        # File letter labels along the bottom
        for dcol, file in enumerate(display_files):
            flab = QLabel(FILES[file])
            flab.setStyleSheet(coord_css)
            flab.setAlignment(Qt.AlignmentFlag.AlignCenter)
            grid.addWidget(flab, 8, dcol + 1)

        board_wrap.addLayout(grid)
        board_wrap.addStretch()
        layout.addLayout(board_wrap)

        # Clear board button (Side-to-move removed; orientation is automatic)
        tools_row = QHBoxLayout()
        tools_row.addStretch()
        clear_btn = QPushButton("Clear Board")
        clear_btn.clicked.connect(self._on_clear)
        tools_row.addWidget(clear_btn)
        layout.addLayout(tools_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        layout.addStretch()

        scroll.setWidget(content)
        outer.addWidget(scroll, 1)

        # Fixed action buttons (outside scroll area)
        btn_bar = QWidget()
        btn_row = QHBoxLayout(btn_bar)
        btn_row.setContentsMargins(16, 8, 16, 12)
        btn_row.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        self.ok_btn = QPushButton("Set")
        self.ok_btn.setDefault(True)
        self.ok_btn.clicked.connect(self._on_ok)
        btn_row.addWidget(cancel)
        btn_row.addWidget(self.ok_btn)
        outer.addWidget(btn_bar)

    def _on_clear(self):
        self.board = [[None] * 8 for _ in range(8)]
        self._refresh_all()

    # ── Square interaction ──────────────────────────────────────
    def _on_square_clicked(self, file, rank):
        # Occupied -> remove the piece
        if self.board[rank][file] is not None:
            self.board[rank][file] = None
            self._refresh_square(file, rank)
            return
        # Empty -> show piece picker
        self._show_piece_picker(file, rank)

    def _show_piece_picker(self, file, rank):
        menu = QMenu(self)
        wking_exists = self._count_king("w") >= 1
        bking_exists = self._count_king("b") >= 1

        def choose(code):
            self.board[rank][file] = code
            self._refresh_square(file, rank)
            menu.close()

        def make_row(color, king_taken):
            w = QWidget()
            row = QHBoxLayout(w)
            row.setContentsMargins(8, 6, 8, 6)
            row.setSpacing(4)
            for t in PIECE_TYPES:
                code = color + t.upper()
                b = QPushButton()
                b.setIconSize(QSize(40, 40))
                b.setFixedSize(QSize(48, 48))
                b.setIcon(_piece_icon(code, 40))
                b.setToolTip(("White " if color == "w" else "Black ") + PIECE_NAMES[t])
                if t == "k" and king_taken:
                    b.setEnabled(False)
                # Piece swatches keep the light-square background regardless of
                # the board's dark-square color.
                b.setStyleSheet(
                    f"QPushButton {{ background:{self._light}; border:1px solid #999; "
                    "border-radius:4px; } "
                    "QPushButton:hover:enabled { border:2px solid #629924; } "
                    "QPushButton:disabled { background:#ccc; }"
                )
                b.clicked.connect(lambda _c, cc=code: choose(cc))
                row.addWidget(b)
            return w

        # White pieces on top, black pieces directly below - both shown at once,
        # so there's no extra color-toggle click.
        for color in ("w", "b"):
            act = QWidgetAction(menu)
            act.setDefaultWidget(make_row(color, wking_exists if color == "w" else bking_exists))
            menu.addAction(act)

        btn = self.cell_buttons[(file, rank)]
        menu.exec(btn.mapToGlobal(btn.rect().bottomLeft()))

    # ── Rendering ───────────────────────────────────────────────
    def _refresh_square(self, file, rank):
        btn = self.cell_buttons[(file, rank)]
        piece = self.board[rank][file]
        if piece:
            btn.setIcon(_piece_icon(piece, 46))
        else:
            btn.setIcon(QIcon())

    def _refresh_all(self):
        for (file, rank), _btn in self.cell_buttons.items():
            self._refresh_square(file, rank)

    # ── Result ──────────────────────────────────────────────────
    def _on_ok(self):
        errors = self._validate()
        if errors:
            if len(errors) == 1:
                msg = errors[0]
            else:
                msg = ("This position has a few problems:\n\n"
                       + "\n".join(f"•  {e}" for e in errors))
            showInfo(msg, parent=self, title="Invalid Position")
            return  # keep the editor open so the user can fix it
        self.result_fen = self.to_fen()
        self.accept()
