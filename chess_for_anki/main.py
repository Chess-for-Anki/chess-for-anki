from aqt import gui_hooks, mw
from aqt.qt import QAction, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QLabel, QMenu, QPushButton, QVBoxLayout

from . import catalog, config, feedback, language_packs, narration, note_type, progression

dialog=None

def profile_open():
    if not mw.col:
        return
    names=[note_type.NOTETYPE_NAME]+note_type.LEGACY_NOTETYPE_NAMES
    if any(mw.col.models.by_name(name) for name in names):
        note_type.ensure_notetype(mw.col)
    if not mw.col.get_config('chessForAnkiModularWelcomeSeen', False):
        from .faq_dialog import FaqDialog
        welcome = FaqDialog(mw, welcome=True)
        welcome.open()
        mw.col.set_config('chessForAnkiModularWelcomeSeen', True)
        welcome.finished.connect(welcome.deleteLater)

def create_cards():
    global dialog
    if dialog is not None:
        try:
            dialog.show()
            dialog.raise_()
            dialog.activateWindow()
            return
        except RuntimeError:
            dialog=None
    from .import_dialog import ImportDialog
    dialog=ImportDialog(mw)
    dialog.finished.connect(clear_dialog)
    dialog.show()

def clear_dialog(*args):
    global dialog
    dialog=None

def import_starter():
    """Open the external starter download. Importing remains an explicit Anki action."""
    catalog.open_starter_download()

def settings(*args, parent=None):
    dlg=QDialog(parent or mw)
    dlg.setWindowTitle('Chess for Anki · Settings')
    layout=QVBoxLayout(dlg)
    demo=mw.col.get_config(progression.DEMO_KEY,{'enabled':True,'seen':[]})
    demo_box=QCheckBox('Show step-by-step demo on first view')
    demo_box.setChecked(demo['enabled'])
    layout.addWidget(demo_box)
    layout.addWidget(QLabel('Starting level for the next round'))
    levels=QComboBox()
    for label,value in zip(progression.NAMES,progression.LEVELS):
        levels.addItem(label,value)
    levels.setCurrentIndex(progression.LEVELS.index(progression.state()['level']))
    layout.addWidget(levels)
    sounds=QCheckBox('Piece sounds')
    sounds.setChecked(config.get_config()['sound_enabled'])
    layout.addWidget(sounds)
    layout.addWidget(QLabel('Narration speed / Velocidade da voz'))
    speed=QComboBox()
    for rate in config.NARRATION_SPEEDS:
        speed.addItem(f'{rate:g}×',rate)
    speed.setCurrentIndex(speed.findData(config.narration_rate(config.get_config()['narration_rate'])))
    layout.addWidget(speed)
    confetti=QCheckBox('Confetti on completion')
    confetti.setChecked(config.get_config()['confetti_enabled'])
    layout.addWidget(confetti)
    packs_button = QPushButton('Language packs · Text and narration')
    packs_button.clicked.connect(lambda: language_packs.open_manager(parent=dlg))
    layout.addWidget(packs_button)
    layout.addWidget(QLabel('Chess notation language / Idioma da notação'))
    notation=QComboBox()
    for label,value in [('Follow commentary language','auto'),('English · K Q R B N','en'),('Português · R D T B C','pt')]:
        notation.addItem(label,value)
    notation.setCurrentIndex(max(0,notation.findData(config.get_config()['notation_language'])))
    layout.addWidget(notation)
    layout.addWidget(QLabel('Found a bug? Describe it and attach a screenshot on GitHub.'))
    feedback_button = QPushButton('Report a bug')
    feedback_button.clicked.connect(lambda: feedback.FeedbackDialog(dlg).exec())
    layout.addWidget(feedback_button)
    layout.addWidget(QLabel('Three different lines completed without hints and rated Good or Easy unlock the next level.'))
    buttons=QDialogButtonBox(QDialogButtonBox.StandardButton.Save|QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dlg.accept)
    buttons.rejected.connect(dlg.reject)
    layout.addWidget(buttons)
    if dlg.exec()!=QDialog.DialogCode.Accepted:
        return
    demo['enabled']=demo_box.isChecked()
    mw.col.set_config(progression.DEMO_KEY,demo)
    if progression.state()['level']!=levels.currentData():
        mw.col.set_config(progression.KEY,{'level':levels.currentData(),'wins':[]})
    updated=config.get_config()
    updated['sound_enabled']=sounds.isChecked()
    updated['confetti_enabled']=confetti.isChecked()
    updated['notation_language']=notation.currentData()
    updated['narration_rate']=speed.currentData()
    config.save_config(updated)
    if mw.col.models.by_name(note_type.NOTETYPE_NAME):
        note_type.ensure_notetype(mw.col)
    mw.reset()

def help_dialog():
    from .faq_dialog import FaqDialog
    FaqDialog(mw).exec()

menu=QMenu('♟️ Chess for Anki',mw)
for label,callback in [
    ('Create cards / Import PGN',create_cards),
    ('Home / Getting started',help_dialog),
    ('Download starter deck',import_starter),
    ('Settings',settings),
    ('Guide and credits',help_dialog),
    ('Language packs',language_packs.open_manager),
    ('Feedback / Report an issue',feedback.open_feedback),
    ('Support the project',catalog.open_support),
]:
    action=QAction(label,mw)
    action.triggered.connect(callback)
    menu.addAction(action)
mw.form.menubar.addMenu(menu)
mw.addonManager.setConfigAction(__name__,settings)
gui_hooks.profile_did_open.append(profile_open)
progression.register()

def stop_audio(*args):
    narration.stop()
    if mw.reviewer.web:
        mw.reviewer.web.eval('if(window.chessStudioNarrator)window.chessStudioNarrator.stop()')

def stop_previous(card):
    if not note_type.is_chess_notetype(card.note_type()):
        stop_audio()

gui_hooks.reviewer_will_end.append(stop_audio)
gui_hooks.reviewer_did_show_question.append(stop_previous)
