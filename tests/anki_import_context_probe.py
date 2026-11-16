"""Exercise the real Qt importer in a disposable, non-syncing Anki profile."""
import json
import os
import traceback
from pathlib import Path
from aqt import gui_hooks, mw
from aqt.qt import QTimer

output = Path(os.environ['CFA_IMPORT_OUTPUT'])
report = {}

def run():
    try:
        from chess_for_anki import import_dialog, previous_move
        from chess_for_anki.faq_dialog import FaqDialog
        for child in mw.findChildren(FaqDialog):
            if child.isVisible(): child.accept()
        assert mw.col.card_count() == 0
        warnings = []
        import_dialog.showWarning = warnings.append
        dialog = import_dialog.ImportDialog(mw)
        dialog.custom_rb.setChecked(True)
        dialog.start_pgn_edit.setPlainText('1. e4 (1. d4 d5) e5')
        context = dialog._previous_context()
        assert context['uci'] == 'e7e5'
        assert dialog.custom_fen.split()[1] == 'w'
        report['pgn_mainline_derives_last_move'] = True
        dialog.title_edit.setText('Context importer QA')
        dialog.pgn_edit.setPlainText('2. Nf3 Nc6')
        dialog._on_import()
        assert not warnings and mw.col.card_count() == 1, warnings
        note = mw.col.get_note(mw.col.find_notes('')[0])
        assert previous_move.loads(note['Previous Move'], note['StartFEN'])['uci'] == 'e7e5'
        assert not dialog.previous_fen_edit.text() and not dialog.previous_uci_edit.text()
        report['saved_note_and_reset_have_correct_context'] = True

        dialog.custom_rb.setChecked(True)
        dialog.start_pgn_edit.setPlainText('1. e4 e5')
        target = dialog.custom_fen
        assert dialog.previous_uci_edit.text() == 'e7e5'
        dialog.start_pgn_edit.setPlainText(target)
        assert dialog.custom_fen == target and not dialog.previous_uci_edit.text()
        dialog.title_edit.setText('Missing context must not import')
        dialog.pgn_edit.setPlainText('2. Nf3 Nc6')
        dialog._on_import()
        assert warnings and mw.col.card_count() == 1
        report['bare_fen_clears_stale_context_and_blocks_import'] = True

        warnings.clear()
        dialog.start_pgn_edit.setPlainText('1. e4 e5 2. Qh8')
        assert not dialog.custom_fen and not dialog.previous_uci_edit.text()
        report['illegal_setup_rejects_partial_prefix'] = True
        dialog.start_pgn_edit.setPlainText('1. e4 e5')
        assert dialog.previous_uci_edit.text() == 'e7e5'
        dialog.black_rb.setChecked(True)
        assert not dialog.previous_uci_edit.text()
        report['changing_side_clears_context'] = True
        dialog.close()
        assert mw.col.db.scalar('select count(*) from revlog') == 0
    except Exception:
        report['error'] = traceback.format_exc()
    (output / 'import-verification.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    QTimer.singleShot(100, mw.unloadProfileAndExit)

gui_hooks.profile_did_open.append(lambda: QTimer.singleShot(900, run))
