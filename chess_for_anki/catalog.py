"""Public destinations and planned languages; no content is fetched on startup."""
DOWNLOADS_URL = "https://github.com/Chess-for-Anki/chess-for-anki/releases/tag/v1.6.0-preview"
ASSET_BASE = "https://github.com/Chess-for-Anki/chess-for-anki/releases/download/v1.6.0-preview/"
FEEDBACK_REPOSITORY_URL = "https://github.com/Chess-for-Anki/chess-for-anki"
SUPPORT_URL = "https://github.com/Chess-for-Anki/chess-for-anki/blob/downloads/SUPPORT.md"
STARTER_FILENAME = "Chess-for-Anki-Free-Sample.apkg"
NATURAL_ENGLISH_FILENAME = "English-Michael-Voice-Pack.zip"
STARTER_DOWNLOAD_URL = ASSET_BASE + STARTER_FILENAME
STARTER_PAGE_URL = "https://ankiweb.net/shared/info/1810293290"
VOICE_DOWNLOAD_URL = "https://github.com/Chess-for-Anki/chess-for-anki/releases/download/v1.4.2-preview/" + NATURAL_ENGLISH_FILENAME
TRAINING_PACKS_URL = "https://github.com/Chess-for-Anki/chess-for-anki/blob/downloads/TRAINING-PACKS.md"

LANGUAGES = (
    ("en-US", "English", True),
    ("pt-BR", "Português", False),
    ("es-ES", "Español", False),
    ("ru-RU", "Русский", False),
    ("zh-CN", "中文", False),
    ("ja-JP", "日本語", False),
    ("fr-FR", "Français", False),
    ("de-DE", "Deutsch", False),
)


def open_downloads():
    from aqt.utils import openLink
    openLink(DOWNLOADS_URL)


def open_starter_download():
    from aqt.utils import openLink
    openLink(STARTER_DOWNLOAD_URL)


def open_starter_page():
    from aqt.utils import openLink
    openLink(STARTER_PAGE_URL)


def open_voice_download():
    from aqt.utils import openLink
    openLink(VOICE_DOWNLOAD_URL)


def open_support():
    from aqt.utils import openLink
    openLink(SUPPORT_URL)


def open_training_packs():
    from aqt.utils import openLink
    openLink(TRAINING_PACKS_URL)
