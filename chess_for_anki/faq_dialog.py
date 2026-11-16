from pathlib import Path

from anki import lang
from aqt.qt import QDialog, QDialogButtonBox, QLabel, QPushButton, QTabWidget, QTextBrowser, QVBoxLayout, QTimer
from aqt.utils import openLink

ROOT = Path(__file__).parent


def uses_portuguese():
    return str(lang.current_lang).lower().startswith("pt")


class FaqDialog(QDialog):
    def __init__(self, parent=None, welcome=False):
        super().__init__(parent)
        self.setWindowTitle("♟️ Chess for Anki · Tutorial" if welcome else "Chess for Anki · Guide and credits")
        self.resize(700, 650)
        layout = QVBoxLayout(self)
        from . import catalog, language_packs
        pt = uses_portuguese()
        intro = QLabel("O add-on não cria cards nem instala vozes automaticamente. Escolha como começar." if pt else "The add-on does not create cards or install voice packs automatically. Choose how to begin.")
        intro.setWordWrap(True)
        layout.addWidget(intro)
        starter = QPushButton("Baixar deck inicial gratuito (.apkg)" if pt else "Download free starter deck (.apkg)")
        starter.setObjectName("cfa-download-starter")
        starter.clicked.connect(catalog.open_starter_download)
        layout.addWidget(starter)
        filename = QLabel(catalog.STARTER_FILENAME + (" · Baixe e importe pelo menu Arquivo do Anki." if pt else " · Download, then import through Anki's File menu."))
        filename.setWordWrap(True)
        layout.addWidget(filename)
        create = QPushButton("Criar meus próprios cards" if pt else "Create my own cards")
        create.setObjectName("cfa-create-own-cards")
        def create_own():
            from .main import create_cards
            self.accept()
            QTimer.singleShot(0, create_cards)
        create.clicked.connect(create_own)
        layout.addWidget(create)
        voices = QPushButton("Vozes e pacotes de idioma" if pt else "Voices and language packs")
        voices.setObjectName("cfa-open-voices")
        voices.clicked.connect(lambda: language_packs.open_manager(parent=self))
        layout.addWidget(voices)
        tabs = QTabWidget()
        self.tabs = tabs
        for label, filename in [
            ("Start here / Comece aqui", "GETTING_STARTED.md"),
            ("English", "README.md"),
            ("Português", "Tutorial.pt-BR.md"),
            ("Credits", "CREDITS.md"),
        ]:
            page = QTextBrowser()
            page.setOpenExternalLinks(True)
            page.setMarkdown((ROOT / filename).read_text(encoding="utf8"))
            tabs.addTab(page, label)
        tabs.setCurrentIndex(0)
        layout.addWidget(tabs)
        settings_hint = QLabel()
        open_settings = QPushButton()
        def update_settings_text():
            pt = uses_portuguese() if tabs.currentIndex()==0 else tabs.currentIndex()==2
            settings_hint.setText("Para voltar depois, abra ♟️ Chess for Anki → Settings no menu superior." if pt
                                  else "To change these later, open ♟️ Chess for Anki → Settings in the top menu.")
            open_settings.setText("Abrir configurações" if pt else "Open settings")
        tabs.currentChanged.connect(update_settings_text)
        update_settings_text()
        layout.addWidget(settings_hint)
        layout.addWidget(open_settings)
        from .feedback import FeedbackDialog
        feedback = QPushButton("Feedback / Report an issue")
        feedback.clicked.connect(lambda: FeedbackDialog(self).exec())
        layout.addWidget(feedback)
        from .main import settings
        open_settings.clicked.connect(lambda: settings(parent=self))
        if not welcome:
            support = QPushButton("Buy me a coffee · fernandomec")
            support.clicked.connect(lambda: openLink("https://buymeacoffee.com/fernandomec"))
            layout.addWidget(support)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        if welcome:
            buttons.button(QDialogButtonBox.StandardButton.Ok).setText("Continuar" if uses_portuguese() else "Continue")
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
