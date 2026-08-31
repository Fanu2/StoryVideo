import glob
import math
import os
import random
import subprocess
import sys
import threading

from PIL import Image, ImageDraw, ImageFont

from PyQt6.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QFileDialog,
    QMessageBox, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QSlider,
    QTextEdit, QScrollArea, QFrame, QStyleFactory, QSizePolicy, QGroupBox,
)

BG = "#1e1e2e"
CARD = "#2a2a3e"
ACCENT = "#89b4fa"
INK_BLUE = "#f5a3c6"
INK_GREEN = "#a6e3a1"
TEXT = "#e5e5f0"
MUTED = "#a0a0bb"

PAGE_W, PAGE_H = 1240, 1754
DPI = 150
MAX_PREVIEW_W = 760

PAPER_TYPES = ["Ruled", "Notebook", "Grid", "Dotted", "Blank", "Aged"]
INK_COLORS = {
    "Black": (20, 20, 20),
    "Blue": (25, 50, 120),
    "Red": (180, 30, 30),
    "Gray": (90, 90, 95),
}

SEARCH_KEYS = ["hand", "script", "cursive", "comic", "chancery", "dancing",
               "monotype", "brush", "italic", "cavolini", "fairfax"]


def discover_handwriting_fonts():
    fonts = {}
    try:
        res = subprocess.run(
            ["fc-list", ":", "file", "family"], capture_output=True,
            text=True, timeout=5,
        )
        for line in res.stdout.splitlines():
            if ":" not in line:
                continue
            path, info = line.split(":", 1)
            family = info.split(",")[0].strip()
            base = os.path.basename(path).lower()
            if any(k in family.lower() or k in base for k in SEARCH_KEYS):
                fonts[f"{family} ({base})"] = path.strip()
    except Exception:
        pass

    if not fonts:
        patterns = [
            "/usr/share/fonts/**/*.ttf", "/usr/share/fonts/**/*.otf",
            "/usr/share/fonts/**/*.ttc",
            os.path.expanduser("~/.fonts/*.ttf"),
            os.path.expanduser("~/.local/share/fonts/*.ttf"),
        ]
        for pattern in patterns:
            for p in glob.glob(pattern, recursive=True):
                base = os.path.basename(p).lower()
                if any(k in base for k in SEARCH_KEYS):
                    fonts[os.path.splitext(base)[0]] = p
    return fonts


def load_font(font_path, size):
    if font_path:
        return ImageFont.truetype(font_path, size)
    candidates = ["/usr/share/fonts/opentype/urw-base35/URWChanceryL-Medi.otf",
                  "/usr/share/fonts/truetype/abcz/ABCSocial.ttc",
                  "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
                  ImageFont.load_default().path]
    for c in candidates:
        try:
            if os.path.exists(c):
                return ImageFont.truetype(c, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def base_color_for_paper(paper):
    if paper == "Aged":
        return (252, 247, 232)
    return (255, 255, 255)


def draw_paper(paper, font_size, line_spacing, margin, page_size):
    img = Image.new("RGB", page_size, base_color_for_paper(paper))
    draw = ImageDraw.Draw(img)
    w, h = page_size
    pitch = int(font_size * line_spacing)

    if paper == "Ruled":
        for y in range(margin, h - margin, pitch):
            draw.line([(margin + 60, y), (w - margin, y)], fill=(170, 190, 220), width=1)
        draw.line([(margin, margin), (margin, h - margin)], fill=(210, 90, 80), width=2)

    elif paper == "Notebook":
        draw.line([(margin + 70, margin), (margin + 70, h - margin)],
                  fill=(214, 98, 92), width=2)
        for y in range(margin, h - margin, pitch):
            draw.line([(margin + 70, y), (w - margin, y)], fill=(178, 198, 226), width=1)

    elif paper == "Grid":
        for y in range(margin, h - margin, pitch):
            draw.line([(margin, y), (w - margin, y)], fill=(198, 212, 232), width=1)
        for x in range(margin, w - margin, pitch):
            draw.line([(x, margin), (x, h - margin)], fill=(198, 212, 232), width=1)

    elif paper == "Dotted":
        rng = random.Random(1234)
        for y in range(margin, h - margin, pitch):
            for x in range(margin, w - margin, pitch):
                draw.ellipse([x, y, x + 2, y + 2], fill=(180, 190, 210))

    elif paper == "Aged":
        rng = random.Random(99)
        for _ in range((w * h) // 250):
            x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
            s = rng.randint(0, 18)
            draw.point((x, y), fill=(252 - s, 247 - s, 232 - s))
        for _ in range((w * h) // 1800):
            x, y = rng.randint(0, w - 1), rng.randint(0, h - 1)
            draw.ellipse([x, y, x + rng.randint(3, 9), y + rng.randint(3, 9)],
                         fill=(240, 228, 200))
    return img


class Renderer:
    def render_pages(self, text, opts):
        random.seed(opts["seed"])
        font = load_font(opts["font_path"], opts["font_size"])
        size = opts["font_size"]
        ink = opts["ink"]
        margin = opts["margin"]

        metrics = {}
        self._cursor = (margin, margin + int(size * 0.35))
        self._x0 = margin
        self._line_pitch = int(size * opts["line_spacing"])
        self._jitter = opts["jitter"] / 100.0
        self._width = PAGE_W - 2 * margin
        self._content_end = PAGE_H - margin
        cur_x, cur_y = self._cursor
        self._lines = []

        paragraphs = text.split("\n")
        for para in paragraphs:
            words = para.split()
            if not words:
                self._lines.append((None, None))
                cur_y += self._line_pitch
                continue
            line_words, line_w = [], 0.0
            space_w = self._measure(" ", font, metrics)
            for word in words:
                word_w = sum(self._measure(c, font, metrics) for c in word)
                add = word_w if not line_words else word_w + space_w
                if line_w + add > self._width and line_words:
                    self._lines.append((line_words, line_w))
                    line_words, line_w = [word], word_w
                else:
                    line_words.append(word)
                    line_w += add
            if line_words:
                self._lines.append((line_words, line_w))

        pages = []
        page = draw_paper(opts["paper"], size, opts["line_spacing"], margin,
                          (PAGE_W, PAGE_H)).convert("RGB")
        draw = ImageDraw.Draw(page)
        y = int(margin + size * 0.35)

        for words, line_w in self._lines:
            if words is None:
                y += self._line_pitch
                continue
            if y + self._line_pitch > self._content_end:
                pages.append(page)
                page = draw_paper(opts["paper"], size, opts["line_spacing"],
                                  margin, (PAGE_W, PAGE_H)).convert("RGB")
                draw = ImageDraw.Draw(page)
                y = int(margin + size * 0.35)
            x = margin
            slope = random.uniform(-0.9, 0.9)
            for word in words:
                for i, ch in enumerate(word):
                    x = self._draw_char(page, draw, ch, font, metrics,
                                        x, y, ink, slope, i)
                if x + self._measure(" ", font, metrics) <= self._width - margin:
                    x += self._measure(" ", font, metrics) * random.uniform(0.5, 1.1)
            y += self._line_pitch
        pages.append(page)
        return pages

    def _measure(self, ch, font, metrics):
        m = metrics.get(ch)
        if m is None:
            w = font.getlength(ch)
            left, top, right, bottom = font.getbbox(ch)
            metrics[ch] = (w, right - left, top, bottom)
            m = metrics[ch]
        return float(m[0])

    def _draw_char(self, page, draw, ch, font, metrics, x, y, ink, slope, i):
        if ch in (" ", "\t", "\n"):
            return x + self._measure(" ", font, metrics)

        # Ensure the metric exists before reading it.
        self._measure(ch, font, metrics)
        w, cw, top, bottom = metrics[ch]

        wobble = (math.sin(x * 0.016 + slope) * 2.5
                  + random.gauss(0, 1 + self._jitter * 2.5))
        dy = int(wobble) + random.gauss(0, self._jitter * 1.4)
        angle = random.gauss(0, self._jitter * 7.0)
        angle = max(-14, min(14, angle))
        wlx = random.gauss(0, self._jitter)
        sx = (x + wlx) + random.uniform(0, cw * 0.04 * self._jitter)

        pad = int(max(6, font.size // 2))
        tw = int(cw) + pad * 2
        th = int(font.size * 1.7) + pad
        tile = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
        td = ImageDraw.Draw(tile)
        td.text((pad - top, pad), ch, font=font, fill=ink + (255,))
        tile = tile.rotate(angle, expand=True, resample=Image.Resampling.BILINEAR)
        paste_x = int(sx) - pad
        paste_y = int(y + dy) - pad + top
        page.paste(tile, (paste_x, paste_y), tile)
        return sx + cw + random.gauss(0, self._jitter * 0.5)


class RenderWorker(QObject):
    """Render PIL pages in a Qt worker thread and return results safely."""

    finished = pyqtSignal(object)
    failed = pyqtSignal(str)

    def __init__(self, renderer, text, options):
        super().__init__()
        self.renderer = renderer
        self.text = text
        self.options = options

    def run(self):
        try:
            pages = self.renderer.render_pages(
                self.text,
                self.options,
            )
            self.finished.emit(pages)
        except Exception as error:
            self.failed.emit(str(error))


class MainWindow(QMainWindow):
    def __init__(self, fonts):
        super().__init__()
        self.fonts = fonts
        self.pages = []
        self.page_index = 0
        self.custom_font = None
        self.ink = "Black"
        self._thread = None
        self._worker = None

        self.setWindowTitle("Handwriting Letter Maker")
        self.resize(1240, 880)
        self.setStyleSheet(self._qss())

        self.renderer = Renderer()
        self._build_ui()
        self.statusBar().showMessage("Type your letter, pick a style, and press Render.")

    @staticmethod
    def _qss():
        return f"""
        QMainWindow, QWidget {{ background: {BG}; color: {TEXT}; }}
        QLabel {{ color: {TEXT}; }}
        QLabel#title {{ font-size: 22px; font-weight: bold; }}
        QLabel#section {{ color: {INK_BLUE}; font-weight: bold; font-size: 13px; }}
        QFrame#card {{ background: {CARD}; border-radius: 10px; }}
        QGroupBox {{
            background: {CARD}; border: 1px solid #313244; border-radius: 8px;
            margin-top: 10px; padding-top: 6px; color: {INK_BLUE}; font-weight: bold;
        }}
        QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; }}
        QPushButton {{
            background: {ACCENT}; color: #11111b; border: none; border-radius: 6px;
            padding: 8px 16px; font-weight: bold;
        }}
        QPushButton:hover {{ background: #74c7ec; }}
        QPushButton#ghost {{
            background: {CARD}; color: {ACCENT}; border: 1px solid {ACCENT}; padding: 6px 12px;
        }}
        QPushButton#ghost:hover {{ background: #313244; }}
        QPushButton#ink {{
            background: {CARD}; border: 2px solid #313244; border-radius: 10px;
        }}
        QPushButton#pink {{ background: {INK_BLUE}; color: #11111b; }}
        QTextEdit {{
            background: #181825; color: {TEXT}; border: 1px solid #313244;
            border-radius: 8px; padding: 8px; font-size: 14px;
        }}
        QComboBox {{
            background: #181825; color: {TEXT}; border: 1px solid #313244;
            border-radius: 6px; padding: 6px;
        }}
        QComboBox QAbstractItemView {{ background: {CARD}; color: {TEXT}; }}
        QSlider::groove:horizontal {{ background: #313244; height: 6px; border-radius: 3px; }}
        QSlider::handle:horizontal {{
            background: {INK_BLUE}; width: 16px; height: 16px; margin: -5px 0;
            border-radius: 8px;
        }}
        QScrollArea {{ border: none; }}
        QStatusBar {{ background: {CARD}; color: {MUTED}; }}
        """

    def _build_ui(self):
        toolbar = self.addToolBar("Actions")
        toolbar.setMovable(False)
        render_act = QAction("Render / Preview", self)
        render_act.triggered.connect(self.render)
        toolbar.addAction(render_act)
        reink_act = QAction("Re-ink (new seed)", self)
        reink_act.triggered.connect(self.reink)
        toolbar.addAction(reink_act)

        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # ---------- left controls ----------
        left = QWidget()
        left.setFixedWidth(360)
        self.left_layout = QVBoxLayout(left)
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_layout.setSpacing(8)

        title = QLabel("\u270d\ufe0f  Handwriting Letter Maker")
        title.setObjectName("title")
        self.left_layout.addWidget(title)

        text_box = QGroupBox("Your letter")
        tb = QVBoxLayout(text_box)
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(SAMPLE)
        self.text_edit.setFixedHeight(170)
        tb.addWidget(self.text_edit)
        self.left_layout.addWidget(text_box)

        style_box = QGroupBox("Handwriting style")
        sb = QGridLayout(style_box)
        sb.setSpacing(6)

        sb.addWidget(QLabel("Font"), 0, 0)
        self.font_combo = QComboBox()
        for name in self.fonts:
            self.font_combo.addItem(name)
        self.font_combo.addItem("Use default font")
        self.font_combo.setCurrentIndex(self.font_combo.count() - 1)
        sb.addWidget(self.font_combo, 0, 1, 1, 2)
        self.font_btn = QPushButton("Browse font...")
        self.font_btn.setObjectName("ghost")
        self.font_btn.clicked.connect(self.browse_font)
        sb.addWidget(self.font_btn, 1, 1)

        self.font_btn_label = QLabel("")
        self.font_btn_label.setStyleSheet(f"color: {MUTED};")
        sb.addWidget(self.font_btn_label, 1, 2)

        sb.addWidget(QLabel("Paper"), 2, 0)
        self.paper_combo = QComboBox()
        self.paper_combo.addItems(PAPER_TYPES)
        sb.addWidget(self.paper_combo, 2, 1, 1, 2)

        sb.addWidget(QLabel("Ink"), 3, 0)
        ink_row = QHBoxLayout()
        self.ink_buttons = {}
        for name, color in INK_COLORS.items():
            btn = QPushButton()
            btn.setObjectName("ink")
            btn.setFixedSize(30, 26)
            btn.setStyleSheet(
                f"QPushButton {{ background: rgb({color[0]},{color[1]},{color[2]});"
                f" border: 2px solid #313244; border-radius: 8px; }}"
                f"QPushButton:hover {{ border: 2px solid {ACCENT}; }}"
            )
            btn.setToolTip(name)
            btn.setCheckable(True)
            if name == "Black":
                btn.setChecked(True)
                btn.setStyleSheet(
                    btn.styleSheet().replace("#313244", ACCENT)
                )
            btn.clicked.connect(lambda _, n=name, b=btn: self.pick_ink(n, b))
            ink_row.addWidget(btn)
            self.ink_buttons[name] = btn
        ink_row.addStretch()
        sb.addLayout(ink_row, 3, 1, 1, 2)

        self._field(style_box, 4, "Font size", "font_size", 16, 80, 36)
        self._field(style_box, 5, "Line spacing", "line_spacing", 80, 220, 140)
        self._field(style_box, 6, "Messiness / jitter", "jitter", 0, 100, 60)
        self._field(style_box, 7, "Left margin", "margin", 30, 160, 90)

        self.left_layout.addWidget(style_box)

        btn_row = QHBoxLayout()
        self.render_btn = QPushButton("Render")
        self.render_btn.clicked.connect(self.render)
        self.reink_btn = QPushButton("Re-ink")
        self.reink_btn.setObjectName("ghost")
        self.reink_btn.clicked.connect(self.reink)
        btn_row.addWidget(self.render_btn)
        btn_row.addWidget(self.reink_btn)
        self.left_layout.addLayout(btn_row)

        self.export_btn = QPushButton("Export PNG")
        self.export_btn.setObjectName("pink")
        self.export_btn.clicked.connect(self.export_png)
        self.left_layout.addWidget(self.export_btn)
        self.pdf_btn = QPushButton("Export PDF (all pages)")
        self.pdf_btn.setObjectName("pink")
        self.pdf_btn.clicked.connect(self.export_pdf)
        self.left_layout.addWidget(self.pdf_btn)

        self.left_layout.addStretch()

        # ---------- right preview ----------
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(4, 0, 0, 0)

        self.page_nav = QLabel("No pages yet")
        self.page_nav.setStyleSheet(f"color: {MUTED};")
        nav_row = QHBoxLayout()
        self.prev_btn = QPushButton("\u2190 Prev")
        self.prev_btn.setObjectName("ghost")
        self.prev_btn.clicked.connect(self.prev_page)
        self.next_btn = QPushButton("Next \u2192")
        self.next_btn.setObjectName("ghost")
        self.next_btn.clicked.connect(self.next_page)
        nav_row.addStretch()
        nav_row.addWidget(self.prev_btn)
        nav_row.addWidget(self.page_nav)
        nav_row.addWidget(self.next_btn)
        nav_row.addStretch()
        right_layout.addLayout(nav_row)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.preview_label = QLabel("Render a letter to see the handwriting preview.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet(f"color: {MUTED};")
        self.scroll.setWidget(self.preview_label)
        right_layout.addWidget(self.scroll, 1)

        root.addWidget(left)
        root.addWidget(right, 1)

    def _field(self, layout, row, label, attr, lo, hi, default):
        layout.addWidget(QLabel(label), row, 0)
        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(lo, hi)
        slider.setValue(default)
        layout.addWidget(slider, row, 1)
        value = QLabel(str(default))
        value.setStyleSheet(f"color: {ACCENT}; font-weight: bold;")
        layout.addWidget(value, row, 2)
        setattr(self, f"{attr}_slider", slider)
        slider.valueChanged.connect(lambda v: value.setText(str(v)))

    def pick_ink(self, name, btn):
        self.ink = name
        for other_name, other in self.ink_buttons.items():
            other.setChecked(False)
            other.setStyleSheet(
                other.styleSheet().replace(f"border: 2px solid {ACCENT};",
                                           "border: 2px solid #313244;")
            )
        btn.setChecked(True)
        btn.setStyleSheet(btn.styleSheet().replace("border: 2px solid #313244;",
                                                   f"border: 2px solid {ACCENT};"))

    def browse_font(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select handwriting font",
            os.path.expanduser("~/.fonts"),
            "Fonts (*.ttf *.otf *.ttc);;All files (*.*)"
        )
        if path:
            self.custom_font = path
            self.font_btn_label.setText(os.path.basename(path))

    def _font_path(self):
        if self.custom_font:
            return self.custom_font
        name = self.font_combo.currentText()
        return self.fonts.get(name)

    def _options(self, seed=None):
        return {
            "font_path": self._font_path(),
            "font_size": self.font_size_slider.value(),
            "line_spacing": self.line_spacing_slider.value() / 100.0,
            "jitter": self.jitter_slider.value(),
            "margin": self.margin_slider.value(),
            "paper": self.paper_combo.currentText(),
            "ink": INK_COLORS[self.ink],
            "seed": random.randint(0, 10_000_000) if seed is None else seed,
        }

    def render(self):
        text = self.text_edit.toPlainText().strip()

        if not text:
            QMessageBox.information(
                self,
                "No Text",
                "Please write some text first.",
            )
            return

        if getattr(self, "_thread", None) is not None:
            return

        options = self._options()

        self.render_btn.setEnabled(False)
        self.reink_btn.setEnabled(False)
        self.render_btn.setText("Rendering...")
        self.statusBar().showMessage("Rendering letter...")

        self._thread = QThread(self)
        self._worker = RenderWorker(
            self.renderer,
            text,
            options,
        )
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._render_finished)
        self._worker.failed.connect(self._render_failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_render)

        self._thread.start()

    def reink(self):
        # A fresh call creates a new random seed in _options().
        self.render()

    def _render_finished(self, pages):
        self.pages = pages
        self.page_index = 0
        self.show_page()
        self.statusBar().showMessage(
            f"Rendered {len(pages)} page(s) — press Re-ink for a fresh scribble."
        )

    def _render_failed(self, message):
        self.statusBar().showMessage("Rendering failed.")
        QMessageBox.critical(self, "Render Error", message)

    def _cleanup_render(self):
        if getattr(self, "_worker", None) is not None:
            self._worker.deleteLater()

        if getattr(self, "_thread", None) is not None:
            self._thread.deleteLater()

        self._worker = None
        self._thread = None
        self.render_btn.setEnabled(True)
        self.reink_btn.setEnabled(True)
        self.render_btn.setText("Render")

    def show_page(self):
        if not self.pages:
            return
        idx = min(max(0, self.page_index), len(self.pages) - 1)
        pil_page = self.pages[idx].convert("RGB")
        data = pil_page.tobytes("raw", "RGB")
        from PyQt6.QtGui import QImage
        qimg = QImage(data, pil_page.width, pil_page.height,
                      3 * pil_page.width, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg)
        if pix.width() > MAX_PREVIEW_W:
            pix = pix.scaledToWidth(MAX_PREVIEW_W, Qt.TransformationMode.SmoothTransformation)
        self.preview_label.setPixmap(pix)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_nav.setText(f"Page {idx + 1} of {len(self.pages)}")
        self.prev_btn.setEnabled(idx > 0)
        self.next_btn.setEnabled(idx < len(self.pages) - 1)

    def prev_page(self):
        if self.pages:
            self.page_index = max(0, self.page_index - 1)
            self.show_page()

    def next_page(self):
        if self.pages:
            self.page_index = min(len(self.pages) - 1, self.page_index + 1)
            self.show_page()

    def export_png(self):
        if not self.pages:
            QMessageBox.information(self, "Nothing to Export", "Render a letter first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PNG",
            f"handwritten_page_{self.page_index + 1}.png", "PNG image (*.png)"
        )
        if not path:
            return
        if not path.lower().endswith(".png"):
            path += ".png"
        if self.pages[self.page_index].save(path, dpi=(DPI, DPI)):
            self.statusBar().showMessage(f"Saved page to {path}")
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        else:
            QMessageBox.critical(self, "Export Error", "Could not write PNG.")

    def export_pdf(self):
        if not self.pages:
            QMessageBox.information(self, "Nothing to Export", "Render a letter first.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "handwritten_letter.pdf", "PDF file (*.pdf)"
        )
        if not path:
            return
        if not path.lower().endswith(".pdf"):
            path += ".pdf"
        try:
            self.pages[0].save(path, "PDF", resolution=DPI,
                               save_all=True, append_images=self.pages[1:])
            self.statusBar().showMessage(f"Saved {len(self.pages)} pages to {path}")
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))


SAMPLE = """My Dearest,

From the moment our eyes first met, the world has seemed softer, warmer, and full of light. Every day with you is a gift I could never deserve, yet somehow, you keep on giving it to me.

I wrote this letter by hand, with all my heart, so that you might keep a piece of me with you. You are my sun, my moon, and every star I wished upon.

Forever and always yours,
With love"""


def main():
    QApplication.setStyle(QStyleFactory.create("Fusion"))
    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica", 10))
    window = MainWindow(discover_handwriting_fonts())
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()