"""Declarative commentary packs. Imported archives contain JSON and MP3 media only."""
import json
import html
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile

from aqt import mw
from . import config

ROOT = Path(__file__).parent
PACKS = ROOT / "user_files" / "language_packs"
BUILTIN = ROOT / "explanations.en.json"
MAX_BYTES = 256 * 1024 * 1024
AUDIO_NAME = re.compile(r"(?:_cfa_(?:expl|voice)_[a-f0-9]{16,64}|_chess_michael_[a-f0-9]{16,64})\.mp3")


def validate(data):
    if not isinstance(data,dict) or type(data.get("schema")) is not int or data["schema"] not in (1,2):
        raise ValueError("Unsupported language pack schema.")
    if not isinstance(data.get("id"),str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", data["id"]):
        raise ValueError("Invalid pack ID.")
    if not isinstance(data.get("language"),str) or not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*", data["language"]):
        raise ValueError("Invalid language code.")
    if not isinstance(data.get("name"), str) or not 1 <= len(data["name"]) <= 120:
        raise ValueError("The pack needs a short display name.")
    minimum = 1 if data["schema"] == 1 else 0
    if not isinstance(data.get("lines"), list) or not minimum <= len(data["lines"]) <= 1000:
        raise ValueError("Invalid number of commentary lines.")
    voice=data.get("narration")
    if voice is not None:
        if data["schema"]!=2 or not isinstance(voice,dict):
            raise ValueError("Narration requires pack schema 2.")
        if not re.fullmatch(r"[a-z]{2,3}(?:-[A-Za-z0-9]{2,8})*",voice.get("language","")):
            raise ValueError("Invalid narration language.")
        clips=voice.get("clips")
        if not isinstance(clips,dict) or not 1<=len(clips)<=2000:
            raise ValueError("A voice pack needs between 1 and 2000 clips.")
        for text,filename in clips.items():
            if not isinstance(text,str) or not 1<=len(text)<=3000 or not isinstance(filename,str) or not AUDIO_NAME.fullmatch(filename):
                raise ValueError("Invalid narration clip.")
        phrases=voice.get("translations",{})
        if not isinstance(phrases,dict) or len(phrases)>2000 or any(not isinstance(k,str) or not 1<=len(k)<=3000 or not isinstance(v,str) or not 1<=len(v)<=3000 for k,v in phrases.items()):
            raise ValueError("Invalid narration translations.")
    if not data["lines"] and voice is None:
        raise ValueError("The pack must contain commentary or narration.")
    seen = set()
    for line in data["lines"]:
        if not isinstance(line,dict):
            raise ValueError("Invalid commentary line.")
        moves, notes = line.get("moves"), line.get("notes")
        if not isinstance(line.get("start_fen"), str) or len(line["start_fen"]) > 200:
            raise ValueError("Invalid starting position.")
        if not isinstance(moves, list) or not 1 <= len(moves) <= 600:
            raise ValueError("A line needs between 1 and 600 moves.")
        if not all(isinstance(m, str) and 1 <= len(m) <= 20 for m in moves):
            raise ValueError("Invalid move notation.")
        if not isinstance(notes, list) or len(notes) != len(moves):
            raise ValueError("Every move must have an explanation.")
        key = (line["start_fen"], tuple(moves))
        if key in seen:
            raise ValueError("Duplicate line in language pack.")
        seen.add(key)
        for move, note in zip(moves, notes):
            if not isinstance(note,dict):
                raise ValueError("Invalid commentary note.")
            if note.get("san") != move:
                raise ValueError("Explanations must follow the same move order.")
            if not isinstance(note.get("text"), str) or not 1 <= len(note["text"].strip()) <= 2500:
                raise ValueError("An explanation must contain 1 to 2500 characters.")
            if note.get("audio") and not AUDIO_NAME.fullmatch(note["audio"]):
                raise ValueError("Invalid audio filename.")
    return data


def audio_files(data):
    files={n["audio"] for line in data["lines"] for n in line["notes"] if n.get("audio")}
    files.update(data.get("narration",{}).get("clips",{}).values())
    return files


def available():
    builtin = json.loads(BUILTIN.read_text(encoding="utf8"))
    packs = {builtin["id"]: builtin}
    for path in PACKS.glob("*.json"):
        try:
            data = validate(json.loads(path.read_text(encoding="utf8")))
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue
        packs[data["id"]] = data
    return packs


def selected():
    packs = available()
    pack=packs.get(config.get_config()["explanation_pack"])
    return pack if pack and pack["lines"] else packs["starter-en"]


def selected_voice():
    settings=config.get_config()
    pack=available().get(settings["voice_pack"])
    if pack and pack.get("narration") and voice_installed(pack):
        return dict(pack["narration"],id=pack["id"])
    from .catalog import LANGUAGES
    locale=settings["voice_language"]
    if locale not in {item[0] for item in LANGUAGES}:
        locale="en-US"
    return {"id":"system","language":locale,"clips":{},"translations":{}}


def voice_installed(pack):
    directory=Path(mw.col.media.dir())
    return all((directory/name).is_file() for name in pack.get("narration",{}).get("clips",{}).values())


def import_pack(filename):
    with zipfile.ZipFile(filename) as archive:
        infos = archive.infolist()
        if len(infos) > 3000 or sum(i.file_size for i in infos) > MAX_BYTES:
            raise ValueError("The expanded pack exceeds the 256 MB or 3000-file limit.")
        names = set()
        for info in infos:
            path = PurePosixPath(info.filename)
            if info.filename in names or path.is_absolute() or ".." in path.parts or "\\" in info.filename:
                raise ValueError("Unsafe or duplicate path in pack.")
            names.add(info.filename)
            if info.is_dir() and info.filename == "audio/":
                continue
            if info.file_size > 8 * 1024 * 1024:
                raise ValueError("A pack file exceeds 8 MB.")
            if info.filename != "pack.json" and not (len(path.parts) == 2 and path.parts[0] == "audio" and AUDIO_NAME.fullmatch(path.name)):
                raise ValueError("Packs may contain only pack.json and audio/*.mp3 files.")
        if "pack.json" not in names:
            raise ValueError("The archive is missing pack.json.")
        data = validate(json.loads(archive.read("pack.json").decode("utf8")))
        required = audio_files(data)
        if {"audio/" + name for name in required} != names - {"pack.json", "audio/"}:
            raise ValueError("The audio files must exactly match the commentary references.")
        # Validate the whole archive before installing any media.
        if archive.testzip():
            raise ValueError("The pack contains a damaged file.")
        for name in required:
            raw = archive.read("audio/" + name)
            if not (raw.startswith(b"ID3") or (len(raw) > 2 and raw[0] == 255 and raw[1] & 224 == 224)):
                raise ValueError("A narration file is not an MP3.")
            existing = Path(mw.col.media.dir()) / name
            if existing.exists() and existing.read_bytes() != raw:
                raise ValueError("A narration filename conflicts with installed media. The pack author must use a new filename.")
        for name in required:
            installed = mw.col.media.write_data(name, archive.read("audio/" + name))
            if installed != name:
                raise ValueError("Media changed during installation. Import the pack again.")
    PACKS.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=PACKS, delete=False, suffix=".tmp", mode="w", encoding="utf8") as file:
            temporary = Path(file.name)
            json.dump(data, file, ensure_ascii=False)
        os.replace(temporary, PACKS / (data["id"] + ".json"))
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
    settings = config.get_config()
    if data["lines"]:
        settings["explanation_pack"] = data["id"]
    if data.get("narration"):
        settings["voice_pack"] = data["id"]
        settings["voice_language"] = data["narration"]["language"]
    config.save_config(settings)
    return data


def open_manager(parent=None):
    from aqt.qt import QComboBox, QDialog, QDialogButtonBox, QFileDialog, QLabel, QPushButton, QVBoxLayout
    from aqt.utils import showInfo, showWarning
    from . import note_type
    dialog = QDialog(parent or mw)
    dialog.setWindowTitle("Chess for Anki · Language packs")
    layout = QVBoxLayout(dialog)
    intro = QLabel("Start with the device's basic system voice, or download and import a natural voice ZIP.\nText and narrator can be selected separately. No voice is downloaded automatically.")
    intro.setWordWrap(True)
    layout.addWidget(intro)
    choices = QComboBox()
    voices=QComboBox()
    voices.setObjectName("cfa-voice-pack")
    locale=QComboBox()
    locale.setObjectName("cfa-system-language")
    from .catalog import LANGUAGES, NATURAL_ENGLISH_FILENAME, open_voice_download
    for code,name,_ in LANGUAGES:
        locale.addItem(name,code)
    locale.setCurrentIndex(max(0,locale.findData(config.get_config()["voice_language"])))
    def refresh():
        choices.clear()
        voices.clear()
        voices.addItem("System voice · Basic speech synthesis", "system")
        current = selected()["id"]
        for key, pack in available().items():
            if pack["lines"]:
                choices.addItem(pack["name"], key)
            if pack.get("narration") and voice_installed(pack):
                voices.addItem(pack["name"],key)
        choices.setCurrentIndex(choices.findData(current))
        voices.setCurrentIndex(max(0,voices.findData(selected_voice()["id"])))
        locale.setEnabled(voices.currentData()=="system")
    refresh()
    layout.addWidget(QLabel("Commentary text"))
    layout.addWidget(choices)
    layout.addWidget(QLabel("Narrator"))
    layout.addWidget(voices)
    layout.addWidget(QLabel("Basic system speech language · Requires an installed system voice"))
    layout.addWidget(locale)
    voices.currentIndexChanged.connect(lambda:locale.setEnabled(voices.currentData()=="system"))
    status=QLabel("Available natural download: English · Michael.\n"+NATURAL_ENGLISH_FILENAME+"\nPlanned natural packs: Português, Español, Русский, 中文, 日本語, Français, Deutsch.\nThese recordings are not yet available.")
    status.setWordWrap(True)
    layout.addWidget(status)
    from aqt.utils import openLink
    download = QPushButton("Download English Michael voice pack (.zip)")
    download.clicked.connect(open_voice_download)
    layout.addWidget(download)
    install = QPushButton("Import language pack (.zip)")
    def choose_file():
        filename, _ = QFileDialog.getOpenFileName(dialog, "Import language pack", "", "Language pack (*.zip)")
        if not filename:
            return
        try:
            data = import_pack(filename)
        except (OSError, ValueError, zipfile.BadZipFile, TypeError, KeyError, AttributeError) as error:
            showWarning(str(error), parent=dialog)
            return
        refresh()
        showInfo(html.escape(data["name"]) + " installed. Save your choices for the next round.", parent=dialog)
    install.clicked.connect(choose_file)
    layout.addWidget(install)
    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)
    layout.addWidget(buttons)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        settings = config.get_config()
        settings["explanation_pack"] = choices.currentData()
        settings["voice_pack"] = voices.currentData()
        settings["voice_language"] = locale.currentData()
        config.save_config(settings)
    if mw.col.models.by_name(note_type.NOTETYPE_NAME):
        note_type.ensure_notetype(mw.col)
    mw.reset()
