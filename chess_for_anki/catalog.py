"""Public destinations and planned languages; no content is fetched on startup."""
DOWNLOADS_URL = "https://github.com/fernandomec/chess-for-anki-community/releases/tag/v1.4.2-preview"
ASSET_BASE = "https://github.com/fernandomec/chess-for-anki-community/releases/download/v1.4.2-preview/"
FEEDBACK_REPOSITORY_URL = "https://github.com/fernandomec/chess-for-anki-community"
SUPPORT_URL = "https://github.com/fernandomec/chess-for-anki-community/blob/downloads/SUPPORT.md"
STARTER_FILENAME = "Chess-for-Anki-Foundations.apkg"
NATURAL_ENGLISH_FILENAME = "English-Michael-Voice-Pack.zip"
STARTER_DOWNLOAD_URL = ASSET_BASE + STARTER_FILENAME
VOICE_DOWNLOAD_URL = ASSET_BASE + NATURAL_ENGLISH_FILENAME

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


def open_voice_download():
    from aqt.utils import openLink
    openLink(VOICE_DOWNLOAD_URL)


def open_support():
    from aqt.utils import openLink
    openLink(SUPPORT_URL)
