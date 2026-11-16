"""
Manual move-entry dialog for Chess for Anki.

Opens an interactive board (the same look as the review card) where the user
plays moves by clicking or dragging pieces. Illegal moves are rejected with a
small on-board message; pawn promotions prompt for a piece. The moves build a
live PGN below the board, and stepping back to play a different move creates a
branch (rendered with parentheses) so a single entry can produce several lines.

Clicking "Set" returns the generated PGN to the main dialog's PGN box.

Implementation notes
--------------------
* Uses a plain QWebEngineView (not AnkiWebView) so there is no Anki-specific
  web-view teardown to deadlock on.
* The dialog is shown with open() (NOT exec()) so there is no nested Qt event
  loop. Destroying a QtWebEngine page while a nested loop unwinds is a known
  freeze; open() + the finished signal avoids it entirely.
* "Set" reads the PGN via an async runJavaScript callback, then closes on the
  NEXT event-loop tick (QTimer) so we never tear the page down from inside its
  own JS callback.
"""

import os

from aqt.qt import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, Qt, QTimer, QWebEngineView
)
from aqt.utils import showWarning


class ManualEntryDialog(QDialog):
    def __init__(self, parent=None, start_fen="", player_color="white",
                 initial_pgn=""):
        super().__init__(parent)
        self.setWindowTitle("Chess for Anki - Manual Input")
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.result_pgn = None
        self.resize(560, 780)
        self.setMinimumSize(440, 600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.web = QWebEngineView(self)
        layout.addWidget(self.web, 1)

        bar = QHBoxLayout()
        bar.setContentsMargins(12, 8, 12, 12)
        reset_btn = QPushButton("Reset")
        reset_btn.setToolTip("Clear all moves and return to the starting position")
        reset_btn.clicked.connect(self._on_reset)
        bar.addWidget(reset_btn)
        bar.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        bar.addWidget(cancel_btn)
        set_btn = QPushButton("Set")
        set_btn.setDefault(True)
        set_btn.setToolTip("Use these moves and close")
        set_btn.clicked.connect(self._on_set)
        bar.addWidget(set_btn)
        layout.addLayout(bar)

        self._load_board(start_fen or "", player_color or "white",
                         initial_pgn or "")

    # -- helpers --
    def _web_dir(self):
        return os.path.join(os.path.dirname(__file__), "web")

    def _read(self, name):
        with open(os.path.join(self._web_dir(), name), encoding="utf-8") as f:
            return f.read()

    def _load_board(self, start_fen, player_color, initial_pgn=""):
        body = self._read("manual_board.html")
        body = body.replace("/*__CHESS_MIN_JS__*/", self._read("chess_min.js"))
        body = body.replace("/*__PIECES_JS__*/", self._read("pieces.js"))
        # FEN is injected into a JS string literal; guard against stray quotes.
        safe_fen = (start_fen or "").replace('"', "").replace("\\", "")
        body = body.replace("__START_FEN__", safe_fen)
        body = body.replace("__PLAYER_COLOR__", player_color)
        # Previously-entered moves (serializeContinuation format) so reopening
        # Manual Input restores the line. Same string-literal escaping as the FEN.
        safe_moves = (initial_pgn or "").replace("\\", "").replace('"', "")
        body = body.replace("__INITIAL_MOVES__", safe_moves)
        # Theme + sound from the user's settings.
        try:
            from . import config as cfg
            c = cfg.get_config()
            light, dark = cfg.board_colors(c)
            sound_on = bool(c.get("sound_enabled", True))
            (move_uri, cap_uri, chk_uri, cas_uri,
             mate_uri) = (cfg.sound_data_uris() if sound_on
                          else ("", "", "", "", ""))
            piece_set = c.get("piece_set", cfg.DEFAULTS["piece_set"])
            texture = cfg.texture_pattern(c.get("board_texture", "solid")) or "none"
        except Exception:
            light, dark, sound_on, move_uri, cap_uri = "#f0d9b5", "#b58863", False, "", ""
            chk_uri, cas_uri, mate_uri = "", "", ""
            piece_set, texture = "cburnett", "none"
        body = body.replace("__SQ_LIGHT__", light).replace("__SQ_DARK__", dark)
        body = body.replace("__SOUND_ENABLED__", "true" if sound_on else "false")
        body = body.replace("__MOVE_SRC__", move_uri)
        body = body.replace("__CAPTURE_SRC__", cap_uri)
        body = body.replace("__CHECK_SRC__", chk_uri)
        body = body.replace("__CASTLE_SRC__", cas_uri)
        body = body.replace("__MATE_SRC__", mate_uri)
        body = body.replace("__PIECE_SET__", piece_set)
        body = body.replace("__TEXTURE_BG__", texture)
        html = (
            "<!DOCTYPE html><html><head><meta charset='utf-8'></head>"
            "<body style='margin:0;background:#262421'>" + body + "</body></html>"
        )
        self.web.setHtml(html)

    def _run_js(self, js, cb=None):
        page = self.web.page()
        if page is None:
            return
        if cb is None:
            page.runJavaScript(js)
        else:
            page.runJavaScript(js, cb)

    # -- button actions --
    def _on_reset(self):
        self._run_js("window.resetBoard && window.resetBoard();")

    def _on_set(self):
        self._run_js("window.getPGN ? window.getPGN() : '';", self._got_pgn)

    def _got_pgn(self, pgn):
        pgn = (pgn or "").strip()
        if not pgn:
            showWarning("No moves entered yet. Play some moves on the board, "
                        "or click Cancel to dismiss.")
            return
        self.result_pgn = pgn
        # Close on the NEXT tick -- never from inside the JS callback.
        QTimer.singleShot(0, self.accept)
