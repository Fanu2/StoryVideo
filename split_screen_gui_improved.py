import json
import math
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QStyleFactory,
    QVBoxLayout,
    QWidget,
)

BG = "#1e1e2e"
CARD = "#2a2a3e"
ACCENT = "#89b4fa"
TEXT = "#e5e5f0"
MUTED = "#a0a0bb"
BLANK = "0x0a0a14"


@dataclass(frozen=True)
class VideoInfo:
    width: int
    height: int
    fps: float
    duration: float
    has_audio: bool


@dataclass(frozen=True)
class RenderSettings:
    input_path: str
    output_path: str
    duration: float
    width: int
    height: int
    fps: float
    rows: int
    cols: int
    total_cells: int
    active_indices: tuple[int, ...]
    limit_enabled: bool
    limit_seconds: int
    mute: bool


def require_tool(name: str) -> None:
    if not shutil.which(name):
        raise RuntimeError(
            f"{name} was not found in your system PATH. "
            "Install FFmpeg and try again."
        )


def probe_video(path: str) -> VideoInfo:
    require_tool("ffprobe")

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration:stream=codec_type,width,height,r_frame_rate",
        "-of",
        "json",
        path,
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or "ffprobe could not read the file."
        raise RuntimeError(message)

    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        video_stream = next(
            stream
            for stream in data.get("streams", [])
            if stream.get("codec_type") == "video"
        )
        rate = video_stream.get("r_frame_rate", "0/1")
        numerator, denominator = rate.split("/", 1)
        denominator_value = float(denominator)
        fps = float(numerator) / denominator_value if denominator_value else 0.0
        has_audio = any(
            stream.get("codec_type") == "audio"
            for stream in data.get("streams", [])
        )
    except (KeyError, StopIteration, ValueError, ZeroDivisionError) as error:
        raise RuntimeError(
            f"Could not read valid video information: {error}"
        ) from error

    if duration <= 0:
        raise RuntimeError("The input video has no usable duration.")

    return VideoInfo(
        width=int(video_stream["width"]),
        height=int(video_stream["height"]),
        fps=fps,
        duration=duration,
        has_audio=has_audio,
    )


class RenderWorker(QThread):
    status = pyqtSignal(str)
    progress = pyqtSignal(int)
    render_finished = pyqtSignal(bool, str)

    def __init__(self, settings: RenderSettings):
        super().__init__()
        self.settings = settings
        self._process = None
        self._cancel_requested = False

    def cancel(self) -> None:
        self._cancel_requested = True
        process = self._process
        if process and process.poll() is None:
            process.terminate()

    def run(self) -> None:
        try:
            require_tool("ffmpeg")
            command, output_duration = self._build_command()

            self.status.emit("Starting FFmpeg...")
            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            if self._process.stdout is None:
                raise RuntimeError("Could not read FFmpeg progress.")

            stderr_lines = []

            while True:
                if self._cancel_requested:
                    self._process.terminate()
                    self._process.wait(timeout=5)
                    self.render_finished.emit(False, "Video creation was cancelled.")
                    return

                line = self._process.stdout.readline()

                if not line:
                    if self._process.poll() is not None:
                        break
                    continue

                line = line.strip()

                if line.startswith("out_time_ms="):
                    try:
                        value = int(line.split("=", 1)[1])
                        seconds = value / 1_000_000
                        percent = int(
                            min(100, max(0, seconds / output_duration * 100))
                        )
                        self.progress.emit(percent)
                    except (ValueError, ZeroDivisionError):
                        pass

                elif line == "progress=end":
                    self.progress.emit(100)

            if self._process.stderr is not None:
                stderr_lines = self._process.stderr.read().splitlines()

            return_code = self._process.wait()

            if self._cancel_requested:
                self.render_finished.emit(False, "Video creation was cancelled.")
                return

            if return_code != 0:
                detail = "\n".join(stderr_lines[-12:]).strip()
                raise RuntimeError(detail or "FFmpeg failed to create the video.")

            self.render_finished.emit(
                True,
                f"Split-screen video created successfully:\n\n"
                f"{self.settings.output_path}",
            )

        except Exception as error:
            self.render_finished.emit(False, str(error))

        finally:
            self._process = None

    def _build_command(self) -> tuple[list[str], float]:
        settings = self.settings
        active = list(settings.active_indices)

        if not active:
            raise RuntimeError("Enable at least one grid segment.")

        active_count = len(active)
        source_segment_duration = settings.duration / active_count

        output_duration = source_segment_duration
        if settings.limit_enabled:
            output_duration = min(
                output_duration,
                float(settings.limit_seconds),
            )

        if output_duration <= 0:
            raise RuntimeError("Output duration must be greater than zero.")

        cell_width = max(2, settings.width // settings.cols)
        cell_height = max(2, settings.height // settings.rows)

        # libx264 works best with even dimensions.
        cell_width -= cell_width % 2
        cell_height -= cell_height % 2

        active_order = {
            cell_index: segment_number
            for segment_number, cell_index in enumerate(active)
        }

        filters = []
        input_labels = []

        for cell_index in range(settings.total_cells):
            label = f"cell{cell_index}"

            if cell_index in active_order:
                segment_number = active_order[cell_index]
                start = segment_number * source_segment_duration

                filters.append(
                    f"[0:v]"
                    f"trim=start={start:.6f}:duration={output_duration:.6f},"
                    f"setpts=PTS-STARTPTS,"
                    f"scale={cell_width}:{cell_height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={cell_width}:{cell_height}:"
                    f"(ow-iw)/2:(oh-ih)/2:color={BLANK},"
                    f"setsar=1[{label}]"
                )
            else:
                filters.append(
                    f"color=c={BLANK}:"
                    f"s={cell_width}x{cell_height}:"
                    f"r={settings.fps:.6f}:"
                    f"d={output_duration:.6f}[{label}]"
                )

            input_labels.append(f"[{label}]")

        layout = "|".join(
            f"{(index % settings.cols) * cell_width}_"
            f"{(index // settings.cols) * cell_height}"
            for index in range(settings.total_cells)
        )

        filters.append(
            "".join(input_labels)
            + f"xstack=inputs={settings.total_cells}:"
            + f"layout={layout}:shortest=1[vout]"
        )

        if not settings.mute:
            filters.append(
                f"[0:a]atrim=start=0:duration={output_duration:.6f},"
                f"asetpts=PTS-STARTPTS[aout]"
            )

        command = [
            "ffmpeg",
            "-hide_banner",
            "-v",
            "error",
            "-y",
            "-i",
            settings.input_path,
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
        ]

        if not settings.mute:
            command.extend(["-map", "[aout]"])

        command.extend(
            [
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                "-r",
                f"{settings.fps:.6f}",
            ]
        )

        if not settings.mute:
            command.extend(["-c:a", "aac", "-b:a", "192k"])

        command.extend(
            [
                "-t",
                f"{output_duration:.6f}",
                "-progress",
                "pipe:1",
                "-nostats",
                settings.output_path,
            ]
        )

        return command, output_duration


class MainWindow(QMainWindow):
    MAX_CELLS = 16

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Split-Screen Video Maker")
        self.resize(900, 800)
        self.setMinimumSize(760, 680)
        self.setStyleSheet(self._qss())

        self.input_video = ""
        self.output_folder = ""
        self.video_info = None
        self.grid = []
        self._worker = None

        self._build_ui()

    @staticmethod
    def _qss() -> str:
        return f"""
        QMainWindow, QWidget {{
            background: {BG};
            color: {TEXT};
        }}
        QLabel {{
            color: {TEXT};
        }}
        QLabel#title {{
            font-size: 22px;
            font-weight: bold;
        }}
        QLabel#sub {{
            color: {MUTED};
            font-size: 12px;
        }}
        QLabel#info {{
            color: {ACCENT};
            font-weight: bold;
        }}
        QWidget#card {{
            background: {CARD};
            border-radius: 10px;
        }}
        QLineEdit, QSpinBox {{
            background: #181825;
            color: {TEXT};
            border: 1px solid #313244;
            border-radius: 6px;
            padding: 6px;
        }}
        QLineEdit:focus, QSpinBox:focus {{
            border: 1px solid {ACCENT};
        }}
        QPushButton {{
            background: {ACCENT};
            color: #11111b;
            border: none;
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: #74c7ec;
        }}
        QPushButton:disabled {{
            background: #45475a;
            color: {MUTED};
        }}
        QPushButton#ghost {{
            background: {CARD};
            color: {ACCENT};
            border: 1px solid {ACCENT};
        }}
        QPushButton#ghost:hover {{
            background: #313244;
        }}
        QCheckBox {{
            color: {TEXT};
        }}
        QProgressBar {{
            background: #181825;
            border: 1px solid #313244;
            border-radius: 6px;
            text-align: center;
            color: {TEXT};
            min-height: 20px;
        }}
        QProgressBar::chunk {{
            background: {ACCENT};
            border-radius: 5px;
        }}
        QToolBar {{
            background: {CARD};
            spacing: 6px;
        }}
        QStatusBar {{
            background: {CARD};
            color: {MUTED};
        }}
        """

    def _build_ui(self) -> None:
        toolbar = self.addToolBar("Actions")
        toolbar.setMovable(False)

        open_action = QAction("Open Video", self)
        open_action.triggered.connect(self.select_input)
        toolbar.addAction(open_action)

        create_action = QAction("Create Split Screen", self)
        create_action.triggered.connect(self.start)
        toolbar.addAction(create_action)

        central = QWidget()
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(12)

        title = QLabel("Split-Screen Video Maker")
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel(
            "Split one video into time segments and play the segments "
            "simultaneously in a configurable grid."
        )
        subtitle.setObjectName("sub")
        root.addWidget(subtitle)

        card = QWidget()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(12)
        root.addWidget(card, 1)

        card_layout.addWidget(
            self._entry_row(
                "Input video",
                "Select input video...",
                self.select_input,
            )
        )
        card_layout.addWidget(
            self._entry_row(
                "Output folder",
                "Select output folder...",
                self.select_output,
            )
        )
        card_layout.addWidget(
            self._entry_row(
                "Output file name",
                "output_split_screen.mp4",
                None,
            )
        )

        self.info_label = QLabel("No video selected.")
        self.info_label.setObjectName("info")
        self.info_label.setWordWrap(True)
        card_layout.addWidget(self.info_label)

        grid_title = QLabel(
            "Grid layout — checked cells receive consecutive time segments:"
        )
        grid_title.setObjectName("sub")
        card_layout.addWidget(grid_title)

        self.grid_control = QGridLayout()
        self.grid_control.setSpacing(8)
        card_layout.addLayout(self.grid_control)

        button_row = QHBoxLayout()
        self.grow_button = self._ghost_button("+ Add Cell", self.add_cell)
        self.shrink_button = self._ghost_button(
            "- Remove Cell",
            self.remove_cell,
        )
        self.reset_button = self._ghost_button(
            "Reset 2x2",
            self.reset_grid,
        )

        button_row.addWidget(self.grow_button)
        button_row.addWidget(self.shrink_button)
        button_row.addWidget(self.reset_button)
        button_row.addStretch()
        card_layout.addLayout(button_row)

        self.grid = []
        self.reset_grid(force=True)

        options = QWidget()
        options.setObjectName("card")
        options_layout = QHBoxLayout(options)
        options_layout.setContentsMargins(12, 10, 12, 10)

        self.apply_duration = QCheckBox("Limit output to")
        self.apply_duration.toggled.connect(
            lambda enabled: self.max_duration.setEnabled(enabled)
        )

        self.max_duration = QSpinBox()
        self.max_duration.setRange(1, 86400)
        self.max_duration.setValue(60)
        self.max_duration.setEnabled(False)

        seconds_label = QLabel("seconds")
        seconds_label.setObjectName("sub")

        self.mute = QCheckBox("Mute output")

        options_layout.addWidget(self.apply_duration)
        options_layout.addWidget(self.max_duration)
        options_layout.addWidget(seconds_label)
        options_layout.addStretch()
        options_layout.addWidget(self.mute)

        card_layout.addWidget(options)

        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("info")
        card_layout.addWidget(self.status_label)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        card_layout.addWidget(self.progress)

        self.create_button = QPushButton("Create Split Screen")
        self.create_button.clicked.connect(self.start)
        card_layout.addWidget(self.create_button)

        self.statusBar().showMessage("Open a video to begin.")

    def _ghost_button(self, text: str, handler) -> QPushButton:
        button = QPushButton(text)
        button.setObjectName("ghost")
        button.clicked.connect(handler)
        return button

    def _entry_row(self, label: str, placeholder: str, action):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        caption = QLabel(label)
        caption.setObjectName("sub")
        caption.setMinimumWidth(110)
        layout.addWidget(caption)

        edit = QLineEdit()
        edit.setPlaceholderText(placeholder)
        layout.addWidget(edit, 1)

        if action is not None:
            browse = QPushButton("Browse...")
            browse.setObjectName("ghost")
            browse.clicked.connect(action)
            layout.addWidget(browse)

        if label == "Input video":
            self.input_edit = edit
        elif label == "Output folder":
            self.output_edit = edit
        else:
            self.name_edit = edit

        return row

    def select_input(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select input video",
            self.input_video or str(Path.home()),
            "Videos (*.mp4 *.mkv *.avi *.mov *.webm *.m4v);;All files (*.*)",
        )

        if not path:
            return

        try:
            info = probe_video(path)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Video Error",
                f"Could not open this video:\n\n{error}",
            )
            return

        self.input_video = path
        self.video_info = info
        self.input_edit.setText(path)

        if not self.output_folder:
            self.output_folder = str(Path(path).parent)
            self.output_edit.setText(self.output_folder)

        self.show_info()

    def select_output(self) -> None:
        start_folder = self.output_folder or str(Path.home())

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
            start_folder,
        )

        if folder:
            self.output_folder = folder
            self.output_edit.setText(folder)

    def show_info(self) -> None:
        if self.video_info is None:
            self.info_label.setText("No video selected.")
            return

        info = self.video_info
        rows, cols = self._grid_shape()
        active_count = self._active_count()

        if active_count:
            segment_duration = info.duration / active_count
            segment_text = f"{segment_duration:.1f}s per active segment"
        else:
            segment_text = "no active segments"

        audio_text = "audio" if info.has_audio else "no audio"

        self.info_label.setText(
            f"Duration: {info.duration:.2f}s  |  "
            f"Size: {info.width}x{info.height}  |  "
            f"FPS: {info.fps:.2f}  |  "
            f"Grid: {rows}x{cols}  |  "
            f"{active_count} active  |  {segment_text}  |  {audio_text}"
        )

    def add_cell(self) -> None:
        if len(self.grid) >= self.MAX_CELLS:
            QMessageBox.information(
                self,
                "Maximum Reached",
                f"The grid supports up to {self.MAX_CELLS} cells.",
            )
            return

        self._add_cell_widget()
        self._refresh_grid()
        self._update_status()
        self.show_info()

    def remove_cell(self) -> None:
        if len(self.grid) <= 1:
            return

        button = self.grid.pop()
        self.grid_control.removeWidget(button)
        button.deleteLater()

        self._refresh_grid()
        self._update_status()
        self.show_info()

    def reset_grid(self, force: bool = False) -> None:
        if not force and len(self.grid) == 4:
            return

        while self.grid_control.count():
            item = self.grid_control.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        self.grid = []

        for _ in range(4):
            self._add_cell_widget(refresh=False)

        self._refresh_grid()
        self._update_status()
        self.show_info()

    def _add_cell_widget(self, refresh: bool = True) -> None:
        index = len(self.grid)

        button = QPushButton(f"Segment {index + 1}")
        button.setCheckable(True)
        button.setChecked(True)
        button.setMinimumHeight(48)
        button.setStyleSheet(
            f"QPushButton {{"
            f"background: #181825; color: {ACCENT}; "
            f"border: 2px dashed #45475a; border-radius: 8px; "
            f"font-weight: bold; font-size: 13px;"
            f"}}"
            f"QPushButton:checked {{"
            f"background: {ACCENT}; color: #11111b; "
            f"border: 2px solid {ACCENT};"
            f"}}"
            f"QPushButton:hover {{ border-color: {ACCENT}; }}"
        )
        button.toggled.connect(self._grid_changed)

        self.grid.append(button)

        if refresh:
            self._refresh_grid()
            self._update_status()
            self.show_info()

    def _grid_changed(self, checked: bool) -> None:
        self._update_status()
        self.show_info()

    def _grid_shape(self) -> tuple[int, int]:
        count = max(1, len(self.grid))

        if count == 1:
            cols = 1
        elif count <= 4:
            cols = 2
        elif count <= 9:
            cols = 3
        else:
            cols = 4

        rows = math.ceil(count / cols)
        return rows, cols

    def _refresh_grid(self) -> None:
        while self.grid_control.count():
            self.grid_control.takeAt(0)

        rows, cols = self._grid_shape()

        for index, button in enumerate(self.grid):
            self.grid_control.addWidget(
                button,
                index // cols,
                index % cols,
            )

        for row in range(rows):
            self.grid_control.setRowStretch(row, 1)

        for column in range(cols):
            self.grid_control.setColumnStretch(column, 1)

    def _active_count(self) -> int:
        return sum(button.isChecked() for button in self.grid)

    def _update_status(self) -> None:
        active = self._active_count()
        total = len(self.grid)

        self.status_label.setText(
            f"{active} of {total} grid cells enabled."
        )

        self.statusBar().showMessage(
            f"Grid: {total} cells, {active} active. "
            "Active cells receive consecutive time segments; "
            "unchecked cells are blank."
        )

    def _set_busy(self, busy: bool) -> None:
        self.create_button.setEnabled(not busy)
        self.grow_button.setEnabled(not busy)
        self.shrink_button.setEnabled(not busy)
        self.reset_button.setEnabled(not busy)

        if busy:
            self.progress.setVisible(True)
            self.progress.setValue(0)
        else:
            self.progress.setVisible(False)

    def start(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        input_path = self.input_edit.text().strip()
        output_folder = self.output_edit.text().strip()
        output_name = self.name_edit.text().strip() or "output_split_screen.mp4"

        if not input_path or not Path(input_path).is_file():
            QMessageBox.warning(
                self,
                "Input Video",
                "Please select a valid input video.",
            )
            return

        if not output_folder:
            QMessageBox.warning(
                self,
                "Output Folder",
                "Please select an output folder.",
            )
            return

        try:
            require_tool("ffmpeg")
            info = probe_video(input_path)
            Path(output_folder).mkdir(parents=True, exist_ok=True)
        except Exception as error:
            QMessageBox.critical(self, "Setup Error", str(error))
            return

        if not output_name.lower().endswith(".mp4"):
            output_name += ".mp4"

        output_path = str(Path(output_folder) / output_name)

        active_indices = tuple(
            index
            for index, button in enumerate(self.grid)
            if button.isChecked()
        )

        if not active_indices:
            QMessageBox.warning(
                self,
                "No Active Segments",
                "Enable at least one grid cell.",
            )
            return

        rows, cols = self._grid_shape()

        settings = RenderSettings(
            input_path=input_path,
            output_path=output_path,
            duration=info.duration,
            width=info.width,
            height=info.height,
            fps=info.fps if info.fps > 0 else 30.0,
            rows=rows,
            cols=cols,
            total_cells=len(self.grid),
            active_indices=active_indices,
            limit_enabled=self.apply_duration.isChecked(),
            limit_seconds=self.max_duration.value(),
            mute=self.mute.isChecked() or not info.has_audio,
        )

        self._set_busy(True)
        self.status_label.setText("Preparing split-screen video...")

        self._worker = RenderWorker(settings)
        self._worker.status.connect(self.status_label.setText)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.render_finished.connect(self._finish)
        self._worker.render_finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _finish(self, success: bool, message: str) -> None:
        self._set_busy(False)

        if success:
            self.status_label.setText("Video created successfully.")
            self.statusBar().showMessage("Done.")
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText("Video creation failed.")
            self.statusBar().showMessage("Failed.")
            QMessageBox.critical(self, "Error", message)

        self._worker = None

    def closeEvent(self, event) -> None:
        worker = self._worker

        if worker is not None and worker.isRunning():
            answer = QMessageBox.question(
                self,
                "Video Creation In Progress",
                "A video is still being created. Cancel it and exit?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            worker.cancel()
            worker.wait(5000)

        event.accept()


def main() -> None:
    QApplication.setStyle(QStyleFactory.create("Fusion"))

    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
