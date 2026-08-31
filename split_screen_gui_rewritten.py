import json
import math
import os
import shutil
import subprocess
import sys
import threading

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFileDialog,
    QFrame,
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


def grid_shape(cell_count):
    """Return a compact rows/columns arrangement for 1..16 cells."""
    if cell_count <= 1:
        return 1, 1
    if cell_count <= 4:
        return math.ceil(cell_count / 2), 2
    if cell_count <= 9:
        return math.ceil(cell_count / 3), 3
    return math.ceil(cell_count / 4), 4


class RenderWorker(QObject):
    progress = pyqtSignal(int)
    status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self._process = None
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except OSError:
                pass

    @staticmethod
    def _probe(path):
        command = [
            "ffprobe",
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-of", "json",
            path,
        ]
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip() or "ffprobe could not read the video."
            )

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as error:
            raise RuntimeError(f"Invalid ffprobe output: {error}") from error

        video_stream = next(
            (
                stream
                for stream in data.get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            None,
        )

        if video_stream is None:
            raise RuntimeError("No video stream was found in the selected file.")

        duration_text = (
            data.get("format", {}).get("duration")
            or video_stream.get("duration")
        )

        try:
            duration = float(duration_text)
        except (TypeError, ValueError) as error:
            raise RuntimeError(
                "Could not determine the duration of the input video."
            ) from error

        if duration <= 0:
            raise RuntimeError("The input video has an invalid duration.")

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))

        if width <= 0 or height <= 0:
            raise RuntimeError("The input video has an invalid frame size.")

        has_audio = any(
            stream.get("codec_type") == "audio"
            for stream in data.get("streams", [])
        )

        return {
            "duration": duration,
            "width": width,
            "height": height,
            "has_audio": has_audio,
        }

    @staticmethod
    def _even(value):
        value = max(2, int(value))
        return value if value % 2 == 0 else value - 1

    def _build_filter(self, info):
        active_indexes = self.settings["active_indexes"]
        cell_count = self.settings["cell_count"]
        limit_enabled = self.settings["limit_enabled"]
        max_duration = self.settings["max_duration"]

        rows, cols = grid_shape(cell_count)

        output_width = self._even(info["width"])
        output_height = self._even(info["height"])

        cell_width = self._even(max(2, output_width // cols))
        cell_height = self._even(max(2, output_height // rows))

        # The timeline is divided only among enabled cells.
        # Disabled cells remain blank but still occupy a visible grid position.
        segment_duration = info["duration"] / len(active_indexes)
        output_duration = min(
            segment_duration,
            float(max_duration) if limit_enabled else segment_duration,
        )

        if output_duration <= 0:
            raise RuntimeError("Calculated output duration is invalid.")

        filters = []
        labels = []

        active_position = {
            cell_index: position
            for position, cell_index in enumerate(active_indexes)
        }

        for cell_index in range(cell_count):
            output_label = f"cell{cell_index}"

            if cell_index in active_position:
                position = active_position[cell_index]
                start = position * segment_duration
                end = min(
                    info["duration"],
                    start + output_duration,
                )

                filters.append(
                    f"[0:v]"
                    f"trim=start={start:.6f}:end={end:.6f},"
                    f"setpts=PTS-STARTPTS,"
                    f"scale={cell_width}:{cell_height}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={cell_width}:{cell_height}:"
                    f"(ow-iw)/2:(oh-ih)/2,"
                    f"setsar=1"
                    f"[{output_label}]"
                )
            else:
                filters.append(
                    f"color=c=#11111b:s={cell_width}x{cell_height}:"
                    f"d={output_duration:.6f}:r=30"
                    f"[{output_label}]"
                )

            labels.append(f"[{output_label}]")

        layout_parts = []
        for index in range(cell_count):
            x = (index % cols) * cell_width
            y = (index // cols) * cell_height
            layout_parts.append(f"{x}_{y}")

        filters.append(
            f"{''.join(labels)}"
            f"xstack=inputs={cell_count}:"
            f"layout={'|'.join(layout_parts)}:"
            f"fill=#11111b,"
            f"trim=duration={output_duration:.6f},"
            f"setpts=PTS-STARTPTS"
            f"[vout]"
        )

        audio_label = None

        if (
            not self.settings["mute"]
            and info["has_audio"]
        ):
            # Use audio belonging to the first enabled segment so the audio
            # timeline matches the first visible active cell.
            first_start = 0.0
            first_end = min(
                info["duration"],
                first_start + output_duration,
            )

            filters.append(
                f"[0:a]"
                f"atrim=start={first_start:.6f}:end={first_end:.6f},"
                f"asetpts=PTS-STARTPTS"
                f"[aout]"
            )
            audio_label = "[aout]"

        return (
            ";".join(filters),
            output_duration,
            audio_label,
        )

    def run(self):
        try:
            self.status.emit("Reading video information...")
            info = self._probe(self.settings["input_path"])

            if self._cancel_requested:
                self.finished.emit(False, "Rendering was cancelled.")
                return

            self.status.emit("Building split-screen layout...")
            filter_complex, output_duration, audio_label = (
                self._build_filter(info)
            )

            output_path = self.settings["output_path"]

            command = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-i", self.settings["input_path"],
                "-filter_complex", filter_complex,
                "-map", "[vout]",
            ]

            if audio_label is not None:
                command.extend([
                    "-map", audio_label,
                    "-c:a", "aac",
                    "-b:a", "192k",
                ])

            command.extend([
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",
                "-pix_fmt", "yuv420p",
                "-movflags", "+faststart",
                "-t", f"{output_duration:.6f}",
                "-progress", "pipe:1",
                "-nostats",
                output_path,
            ])

            self.status.emit("Encoding video...")
            self.progress.emit(0)

            self._process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stderr_lines = []

            def read_stderr():
                for line in self._process.stderr:
                    stderr_lines.append(line)

            stderr_thread = threading.Thread(
                target=read_stderr,
                daemon=True,
            )
            stderr_thread.start()

            for line in self._process.stdout:
                if self._cancel_requested:
                    self.cancel()
                    break

                line = line.strip()

                if line.startswith("out_time_ms="):
                    try:
                        value = int(line.split("=", 1)[1])
                        seconds = value / 1_000_000
                        percent = int(
                            min(
                                99,
                                max(
                                    0,
                                    seconds / output_duration * 100,
                                ),
                            )
                        )
                        self.progress.emit(percent)
                    except (TypeError, ValueError):
                        pass

            return_code = self._process.wait()
            stderr_thread.join(timeout=2)

            if self._cancel_requested:
                try:
                    if os.path.exists(output_path):
                        os.remove(output_path)
                except OSError:
                    pass
                self.finished.emit(False, "Rendering was cancelled.")
                return

            if return_code != 0:
                error_text = "".join(stderr_lines).strip()
                if not error_text:
                    error_text = "FFmpeg failed without returning an error message."
                raise RuntimeError(error_text)

            self.progress.emit(100)
            self.finished.emit(
                True,
                f"Split-screen video created successfully:\n\n{output_path}",
            )

        except Exception as error:
            self.finished.emit(False, str(error))

        finally:
            self._process = None


class MainWindow(QMainWindow):
    MAX_CELLS = 16

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Split-Screen Video Maker")
        self.resize(900, 820)
        self.setMinimumSize(720, 650)
        self.setStyleSheet(self._qss())

        self.input_video = ""
        self.output_folder = ""
        self.grid_cells = []

        self._thread = None
        self._worker = None

        self._build_ui()
        self.reset_grid(force=True)

    @staticmethod
    def _qss():
        return f"""
        QMainWindow, QWidget {{
            background: {BG};
            color: {TEXT};
        }}
        QLabel {{
            color: {TEXT};
        }}
        QLabel#title {{
            font-size: 24px;
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
        QFrame#card {{
            background: {CARD};
            border-radius: 10px;
        }}
        QLineEdit, QSpinBox {{
            background: #181825;
            color: {TEXT};
            border: 1px solid #313244;
            border-radius: 6px;
            padding: 7px;
            selection-background-color: {ACCENT};
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
        }}
        QProgressBar::chunk {{
            background: {ACCENT};
            border-radius: 6px;
        }}
        QStatusBar {{
            background: {CARD};
            color: {MUTED};
        }}
        """

    def _build_ui(self):
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
            "Split one video's timeline into sequential segments and show "
            "the selected segments simultaneously in a grid."
        )
        subtitle.setObjectName("sub")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        card = QFrame()
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

        grid_text = QLabel(
            "Grid layout — checked cells receive sequential video segments; "
            "unchecked cells remain blank."
        )
        grid_text.setObjectName("sub")
        grid_text.setWordWrap(True)
        card_layout.addWidget(grid_text)

        self.grid_control = QGridLayout()
        self.grid_control.setSpacing(8)
        card_layout.addLayout(self.grid_control)

        button_row = QHBoxLayout()

        self.grow_button = self._ghost_button(
            "+ Add Cell",
            self.add_cell,
        )
        self.remove_button = self._ghost_button(
            "− Remove Cell",
            self.remove_cell,
        )
        self.reset_button = self._ghost_button(
            "Reset 2×2",
            self.reset_grid,
        )

        button_row.addWidget(self.grow_button)
        button_row.addWidget(self.remove_button)
        button_row.addWidget(self.reset_button)
        button_row.addStretch()
        card_layout.addLayout(button_row)

        options = QFrame()
        options.setObjectName("card")
        options_layout = QHBoxLayout(options)
        options_layout.setContentsMargins(12, 10, 12, 10)

        self.apply_duration = QCheckBox("Limit each segment to")
        self.max_duration = QSpinBox()
        self.max_duration.setRange(1, 86400)
        self.max_duration.setValue(60)
        self.max_duration.setEnabled(False)
        self.apply_duration.toggled.connect(
            self.max_duration.setEnabled
        )

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

        progress_row = QHBoxLayout()

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setVisible(False)
        progress_row.addWidget(self.progress, 1)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("ghost")
        self.cancel_button.setVisible(False)
        self.cancel_button.clicked.connect(self.cancel_render)
        progress_row.addWidget(self.cancel_button)

        card_layout.addLayout(progress_row)

        self.create_button = QPushButton("Create Split Screen")
        self.create_button.clicked.connect(self.start)
        card_layout.addWidget(self.create_button)

        self.statusBar().showMessage("Open a video to begin.")

    def _ghost_button(self, text, handler):
        button = QPushButton(text)
        button.setObjectName("ghost")
        button.clicked.connect(handler)
        return button

    def _entry_row(self, label, placeholder, action):
        row = QWidget()
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        label_widget = QLabel(label)
        label_widget.setObjectName("sub")
        layout.addWidget(label_widget)

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

    def select_input(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select input video",
            "",
            (
                "Videos (*.mp4 *.mkv *.avi *.mov *.webm *.m4v);;"
                "All files (*.*)"
            ),
        )

        if not path:
            return

        self.input_video = path
        self.input_edit.setText(path)

        if not self.output_folder:
            self.output_folder = os.path.dirname(path)
            self.output_edit.setText(self.output_folder)

        self.show_info(path)

    def select_output(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select output folder",
        )

        if folder:
            self.output_folder = folder
            self.output_edit.setText(folder)

    def _probe_video(self, path):
        command = [
            "ffprobe",
            "-v", "error",
            "-show_streams",
            "-show_format",
            "-of", "json",
            path,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise RuntimeError(
                result.stderr.strip()
                or "Could not read video information."
            )

        data = json.loads(result.stdout)

        video_stream = next(
            (
                stream
                for stream in data.get("streams", [])
                if stream.get("codec_type") == "video"
            ),
            None,
        )

        if video_stream is None:
            raise RuntimeError("No video stream found.")

        rate = video_stream.get("avg_frame_rate") or "0/1"

        try:
            numerator, denominator = rate.split("/")
            fps = float(numerator) / float(denominator)
        except (ValueError, ZeroDivisionError):
            fps = 0.0

        duration = float(
            data.get("format", {}).get("duration", 0)
        )

        return {
            "duration": duration,
            "width": int(video_stream.get("width", 0)),
            "height": int(video_stream.get("height", 0)),
            "fps": fps,
        }

    def show_info(self, path):
        try:
            info = self._probe_video(path)
            active_count = sum(
                1
                for button in self.grid_cells
                if button.isChecked()
            )
            active_count = max(1, active_count)
            part_duration = info["duration"] / active_count

            self.info_label.setText(
                f"Duration: {info['duration']:.1f}s  |  "
                f"Size: {info['width']}×{info['height']}  |  "
                f"FPS: {info['fps']:.2f}  |  "
                f"Enabled segments: {active_count}  |  "
                f"Each segment: ~{part_duration:.1f}s"
            )

        except Exception as error:
            self.info_label.setText(
                f"Could not read video information: {error}"
            )

    def add_cell(self):
        if len(self.grid_cells) >= self.MAX_CELLS:
            QMessageBox.information(
                self,
                "Maximum Grid Size",
                f"The grid is limited to {self.MAX_CELLS} cells.",
            )
            return

        self._add_cell_widget()
        self._update_status()

    def remove_cell(self):
        if len(self.grid_cells) <= 1:
            return

        button = self.grid_cells.pop()
        self.grid_control.removeWidget(button)
        button.deleteLater()

        self._refresh_grid()
        self._update_status()

    def reset_grid(self, force=False):
        if not force and len(self.grid_cells) == 4:
            return

        while self.grid_cells:
            button = self.grid_cells.pop()
            self.grid_control.removeWidget(button)
            button.deleteLater()

        for _ in range(4):
            self._add_cell_widget(refresh=False)

        self._refresh_grid()
        self._update_status()

    def _add_cell_widget(self, refresh=True):
        index = len(self.grid_cells)

        button = QPushButton(f"Segment {index + 1}")
        button.setObjectName("segment")
        button.setCheckable(True)
        button.setChecked(True)
        button.setMinimumHeight(56)

        button.setStyleSheet(
            f"""
            QPushButton {{
                background: #181825;
                color: {ACCENT};
                border: 2px dashed #45475a;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:checked {{
                background: {ACCENT};
                color: #11111b;
                border: 2px solid {ACCENT};
            }}
            QPushButton:hover {{
                border-color: {ACCENT};
            }}
            """
        )

        button.toggled.connect(self._cell_toggled)

        self.grid_cells.append(button)

        if refresh:
            self._refresh_grid()

    def _cell_toggled(self):
        self._update_status()

    def _refresh_grid(self):
        while self.grid_control.count():
            item = self.grid_control.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

        rows, cols = grid_shape(len(self.grid_cells))

        for index, button in enumerate(self.grid_cells):
            button.setText(f"Segment {index + 1}")
            row = index // cols
            column = index % cols
            self.grid_control.addWidget(button, row, column)
            self.grid_control.setRowStretch(row, 1)

        for column in range(cols):
            self.grid_control.setColumnStretch(column, 1)

    def _update_status(self):
        active = sum(
            1
            for button in self.grid_cells
            if button.isChecked()
        )
        total = len(self.grid_cells)

        self.status_label.setText(
            f"{active} of {total} cells enabled."
        )

        self.statusBar().showMessage(
            f"Grid: {total} cells, {active} enabled. "
            f"Enabled cells receive consecutive timeline segments."
        )

        if self.input_video:
            self.show_info(self.input_video)

    def _read_paths_from_ui(self):
        input_path = self.input_edit.text().strip()
        output_folder = self.output_edit.text().strip()

        if input_path:
            self.input_video = input_path

        if output_folder:
            self.output_folder = output_folder

        return input_path, output_folder

    def start(self):
        input_path, output_folder = self._read_paths_from_ui()

        if not shutil.which("ffmpeg"):
            QMessageBox.critical(
                self,
                "FFmpeg Not Found",
                "FFmpeg was not found in your system PATH.",
            )
            return

        if not shutil.which("ffprobe"):
            QMessageBox.critical(
                self,
                "FFprobe Not Found",
                "FFprobe was not found in your system PATH.",
            )
            return

        if not input_path or not os.path.isfile(input_path):
            QMessageBox.warning(
                self,
                "No Video",
                "Please select a valid input video.",
            )
            return

        if not output_folder:
            QMessageBox.warning(
                self,
                "No Output Folder",
                "Please select an output folder.",
            )
            return

        try:
            os.makedirs(output_folder, exist_ok=True)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Output Folder Error",
                str(error),
            )
            return

        active_indexes = [
            index
            for index, button in enumerate(self.grid_cells)
            if button.isChecked()
        ]

        if not active_indexes:
            QMessageBox.warning(
                self,
                "No Segments Enabled",
                "Enable at least one grid cell.",
            )
            return

        output_name = (
            self.name_edit.text().strip()
            or "output_split_screen.mp4"
        )

        if not output_name.lower().endswith(".mp4"):
            output_name += ".mp4"

        output_path = os.path.join(
            output_folder,
            output_name,
        )

        settings = {
            "input_path": input_path,
            "output_path": output_path,
            "cell_count": len(self.grid_cells),
            "active_indexes": active_indexes,
            "limit_enabled": self.apply_duration.isChecked(),
            "max_duration": self.max_duration.value(),
            "mute": self.mute.isChecked(),
        }

        self._set_rendering(True)

        self._thread = QThread(self)
        self._worker = RenderWorker(settings)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress.setValue)
        self._worker.status.connect(self.status_label.setText)
        self._worker.finished.connect(self._render_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_thread)

        self._thread.start()

    def _set_rendering(self, rendering):
        self.create_button.setEnabled(not rendering)
        self.grow_button.setEnabled(not rendering)
        self.remove_button.setEnabled(not rendering)
        self.reset_button.setEnabled(not rendering)

        self.progress.setVisible(rendering)
        self.cancel_button.setVisible(rendering)

        if rendering:
            self.progress.setValue(0)
            self.status_label.setText("Starting...")
            self.statusBar().showMessage("Rendering in progress...")

    def cancel_render(self):
        if self._worker is not None:
            self.status_label.setText("Cancelling...")
            self._worker.cancel()
            self.cancel_button.setEnabled(False)

    def _render_finished(self, success, message):
        self._set_rendering(False)
        self.cancel_button.setEnabled(True)

        if success:
            self.status_label.setText("Done.")
            self.statusBar().showMessage("Video created successfully.")
            QMessageBox.information(
                self,
                "Success",
                message,
            )
        else:
            self.status_label.setText(
                "Cancelled." if message == "Rendering was cancelled."
                else "Failed."
            )
            self.statusBar().showMessage(
                "Rendering cancelled."
                if message == "Rendering was cancelled."
                else "Video creation failed."
            )

            if message == "Rendering was cancelled.":
                QMessageBox.information(
                    self,
                    "Cancelled",
                    message,
                )
            else:
                QMessageBox.critical(
                    self,
                    "Error",
                    message,
                )

    def _cleanup_thread(self):
        worker = self._worker
        thread = self._thread

        if worker is not None:
            worker.deleteLater()

        if thread is not None:
            thread.deleteLater()

        self._worker = None
        self._thread = None

    def closeEvent(self, event):
        if self._thread is not None and self._thread.isRunning():
            answer = QMessageBox.question(
                self,
                "Rendering in Progress",
                "A video is still being rendered. Cancel and close?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return

            self.cancel_render()
            self._thread.quit()
            self._thread.wait(3000)

        event.accept()


def main():
    QApplication.setStyle(QStyleFactory.create("Fusion"))

    app = QApplication(sys.argv)
    app.setFont(QFont("Helvetica", 10))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
