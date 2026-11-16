"""Plain-text bug reports with a normalized raster attachment."""
from datetime import datetime, timezone
import json
from pathlib import Path
import platform
import re
from urllib.parse import urlencode, urlparse

from anki import version
from aqt import mw
from aqt.qt import QApplication, QBuffer, QByteArray, QCheckBox, QDialog, QFileDialog, QHBoxLayout, QIODevice, QImage, QImageReader, QLabel, QLineEdit, QPainter, QPixmap, QPlainTextEdit, QPushButton, Qt, QVBoxLayout
from aqt.utils import openLink, showWarning
from . import config, note_type

ROOT = Path(__file__).parent
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def github_repository(url):
    parsed = urlparse(url.strip())
    parts = parsed.path.strip("/").split("/")
    if parsed.scheme != "https" or parsed.netloc != "github.com" or parsed.query or parsed.fragment:
        raise ValueError("Use an HTTPS GitHub repository URL, such as https://github.com/owner/repository.")
    if len(parts) != 2 or not all(re.fullmatch(r"[A-Za-z0-9_.-]+", p) and p not in (".", "..") for p in parts):
        raise ValueError("Enter the repository URL without /issues or other suffixes.")
    return "https://github.com/" + "/".join(parts)


def repository_url():
    from .catalog import FEEDBACK_REPOSITORY_URL
    value=config.get_config().get('feedback_url')
    if not value or value.rstrip('/')=='https://github.com/fernandomec/chess-for-anki':
        value=FEEDBACK_REPOSITORY_URL
    return github_repository(value)


def fenced(text, language='text'):
    runs=re.findall(r'`+',text)
    fence='`'*max(3,max((len(run) for run in runs),default=0)+1)
    return fence+language+'\n'+text+'\n'+fence


def issue_body(data):
    body='## Description\n\n'+fenced(data['message'])
    details={key:data[key] for key in ['created','addon_version','anki_version','platform']}
    if 'chess_card' in data:details['chess_card']=data['chess_card']
    return body+'\n\n## Environment\n\n'+fenced(json.dumps(details,ensure_ascii=False,indent=2),'json')


def normalize_image(filename):
    path = Path(filename)
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg", ".webp"):
        raise ValueError("Choose a PNG, JPEG or WebP image.")
    if path.stat().st_size > MAX_IMAGE_BYTES:
        raise ValueError("The image must be smaller than 10 MB.")
    reader = QImageReader(str(path))
    if bytes(reader.format()).lower() not in (b"png", b"jpeg", b"jpg", b"webp"):
        raise ValueError("The file content is not a supported raster image.")
    size = reader.size()
    if not size.isValid() or size.width() * size.height() > 16_000_000:
        raise ValueError("The image must contain at most 16 million pixels.")
    reader.setAutoTransform(True)
    decoded = reader.read()
    if decoded.isNull():
        raise ValueError("The image could not be decoded.")
    # Draw onto a new image so metadata and trailing input bytes are discarded.
    clean = QImage(decoded.size(), QImage.Format.Format_RGB32)
    clean.fill(Qt.GlobalColor.white)
    painter = QPainter(clean)
    painter.drawImage(0, 0, decoded)
    painter.end()
    while True:
        payload = QByteArray()
        stream = QBuffer(payload)
        stream.open(QIODevice.OpenModeFlag.WriteOnly)
        if not clean.save(stream, "PNG"):
            raise ValueError("The image could not be normalized.")
        stream.close()
        if payload.size()<=MAX_IMAGE_BYTES:
            break
        clean=clean.scaled(max(1,int(clean.width()*.8)),max(1,int(clean.height()*.8)),Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
    return bytes(payload), clean


class FeedbackDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Chess for Anki · Feedback")
        self.resize(620, 650)
        self.attachment = None
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Report an error or suggest an improvement"))
        self.subject = QLineEdit()
        self.subject.setPlaceholderText("What happened?")
        self.subject.setMaxLength(160)
        layout.addWidget(self.subject)
        self.message = QPlainTextEdit()
        self.message.setPlaceholderText("What did you try, what did you expect, and what happened instead?")
        self.message.textChanged.connect(self.limit_message)
        layout.addWidget(self.message)
        self.count = QLabel("0 / 5000 characters")
        layout.addWidget(self.count)
        self.context = QCheckBox("Include the current chess card title and moves")
        self.context.setChecked(True)
        layout.addWidget(self.context)
        self.preview = QLabel("Optional image · PNG, JPEG or WebP · up to 10 MB")
        self.preview.setWordWrap(True)
        layout.addWidget(self.preview)
        row = QHBoxLayout()
        attach = QPushButton("Attach image")
        attach.clicked.connect(self.choose_image)
        clear = QPushButton("Remove image")
        clear.clicked.connect(self.clear_image)
        row.addWidget(attach)
        row.addWidget(clear)
        layout.addLayout(row)
        self.destination = QLabel()
        self.destination.setWordWrap(True)
        self.destination.setText("Reports are public on GitHub. Review your text and screenshot before submitting. Screenshots are copied as images to paste into the issue; no ZIP or executable is sent. A GitHub account is needed to post a report.")
        layout.addWidget(self.destination)
        copy_row=QHBoxLayout()
        copy_text=QPushButton('Copy report text')
        copy_text.clicked.connect(self.copy_report)
        copy_row.addWidget(copy_text)
        self.copy_screenshot=QPushButton('Copy screenshot')
        self.copy_screenshot.setEnabled(False)
        self.copy_screenshot.clicked.connect(self.copy_image)
        copy_row.addWidget(self.copy_screenshot)
        layout.addLayout(copy_row)
        self.send=QPushButton('Review and submit on GitHub')
        self.send.setObjectName('cfa-open-github-issue')
        self.send.clicked.connect(self.open_issue)
        layout.addWidget(self.send)
        issues=QPushButton('View reported issues')
        issues.clicked.connect(self.view_issues)
        layout.addWidget(issues)
        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def limit_message(self):
        text = self.message.toPlainText()
        if len(text) > 5000:
            cursor = self.message.textCursor()
            cursor.setPosition(5000)
            cursor.movePosition(cursor.MoveOperation.End, cursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
        if hasattr(self, "count"):
            self.count.setText(f"{len(self.message.toPlainText())} / 5000 characters")

    def choose_image(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Attach an image", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not filename:
            return
        try:
            self.attachment, image = normalize_image(filename)
        except (OSError, ValueError) as error:
            showWarning(str(error), parent=self)
            return
        self.preview.setPixmap(QPixmap.fromImage(image).scaled(520,180,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        self.preview.setToolTip(f"Normalized PNG · {image.width()} × {image.height()}")
        self.copy_screenshot.setEnabled(True)

    def clear_image(self):
        self.attachment = None
        self.preview.setText("Optional image · PNG, JPEG or WebP · up to 10 MB")
        self.copy_screenshot.setEnabled(False)

    def report(self):
        if not self.subject.text().strip() or not self.message.toPlainText().strip():
            raise ValueError("Enter a subject and describe the issue.")
        data = {
            "schema": 1, "created": datetime.now(timezone.utc).isoformat(),
            "addon_version": json.loads((ROOT / "manifest.json").read_text(encoding="utf8"))["version"],
            "anki_version": version, "platform": platform.system(),
            "subject": self.subject.text().strip(), "message": self.message.toPlainText().strip(),
        }
        card = mw.reviewer.card
        if self.context.isChecked() and mw.state == "review" and card and note_type.is_chess_notetype(card.note_type()):
            note = card.note()
            limits={'Title':300,'PlayerColor':20,'MovesPGN':12000,'StartFEN':200}
            data["chess_card"] = {field: note[field][:limit] for field,limit in limits.items()}
        return data

    def copy_report(self):
        try:
            data = self.report()
        except ValueError as error:
            showWarning(str(error), parent=self)
            return
        QApplication.clipboard().setText(issue_body(data))
        self.destination.setText('Report text copied. Paste it into the GitHub issue, then use Copy screenshot if needed.')

    def copy_image(self):
        if not self.attachment:
            return
        image=QImage.fromData(self.attachment,'PNG')
        if image.isNull():
            return
        QApplication.clipboard().setImage(image)
        self.destination.setText('Screenshot copied. Paste it into the GitHub issue with Ctrl+V (Cmd+V on macOS), then submit the issue.')

    def view_issues(self):
        try:
            url=repository_url()
        except ValueError as error:
            showWarning(str(error),parent=self)
            return
        openLink(url+'/issues')

    def open_issue(self):
        try:
            data = self.report()
            repository = repository_url()
        except ValueError as error:
            showWarning(str(error), parent=self)
            return
        body=issue_body(data)
        url=repository+'/issues/new?'+urlencode({'title':data['subject'],'body':body})
        if len(url)>7500:
            QApplication.clipboard().setText(body)
            url=repository+'/issues/new?'+urlencode({'title':data['subject']})
            self.destination.setText('This report is long, so its full text was copied. Paste the text into the GitHub issue, then return here and use Copy screenshot to paste the image.')
        elif self.attachment:
            self.copy_image()
        else:
            self.destination.setText('Your text is ready on GitHub. Review it and click Submit new issue to send it.')
        openLink(url)


def open_feedback(*args):
    FeedbackDialog().exec()
