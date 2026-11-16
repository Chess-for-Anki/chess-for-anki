"""Basic speech uses Anki's system TTS. Optional voices remain declarative media packs."""
import html
import re

from anki.sound import TTSTag
from aqt.sound import av_player
from aqt.utils import tooltip

from . import config

_warned = set()
_owns_speech = False


def stop():
    global _owns_speech
    if _owns_speech:
        av_player.stop_and_clear_queue()
        _owns_speech=False


def speak(value):
    global _owns_speech
    if not isinstance(value, dict):
        return
    text = value.get("text")
    locale = value.get("language", "en-US")
    rate = value.get("rate", 1.5)
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= 3000:
        return
    if not isinstance(locale, str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", locale):
        return
    if type(rate) not in (int, float) or rate not in config.NARRATION_SPEEDS:
        return
    tag = TTSTag(field_text=html.escape(text), lang=locale.replace("-", "_"), voices=[], speed=float(rate), other_args=[])
    if not any(player.rank_for_tag(tag) is not None for player in av_player.players):
        if locale not in _warned:
            tooltip("No system voice for " + locale + ". Choose another system language or install an optional voice pack.")
            _warned.add(locale)
        return
    if value.get("interrupt") is True:
        stop()
    _owns_speech=True
    av_player.append_tags([tag])
