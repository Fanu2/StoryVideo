from __future__ import annotations

import shutil
import subprocess
import threading
import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, ttk


# ----------------------------------------------------------------------
# Appearance
# ----------------------------------------------------------------------

BG = "#1e1e2e"
CARD = "#2a2a3e"
INPUT_BG = "#181825"

ACCENT = "#89b4fa"
ACCENT_HOVER = "#74c7ec"

TEXT = "#e5e5f0"
MUTED = "#a0a0bb"


# ----------------------------------------------------------------------
# Application
# ----------------------------------------------------------------------

class PipVideoApp:
    """
    Create a Picture-in-Picture MP4 video using FFmpeg.

    The first video is the background.
    The second video is scaled and overlaid on top.
    """

    VIDEO_FILETYPES = [
        (
            "Video files",
            "*.mp4 *.mkv *.avi *.mov *.webm *.m4v",
        ),
        (
            "All files",
            "*.*",
        ),
    ]

    def __init__(self, root: tk.Tk):

        self.root = root

        self.root.title(
            "Picture-in-Picture Video Maker"
        )

        self.root.geometry(
            "760x670"
        )

        self.root.minsize(
            680,
            600,
        )

        self.root.configure(
            bg=BG
        )

        # --------------------------------------------------------------
        # Application state
        # --------------------------------------------------------------

        self.background_video = tk.StringVar()

        self.pip_video = tk.StringVar()

        self.output_folder = tk.StringVar(
            value=str(Path.home())
        )

        self.output_name = tk.StringVar(
            value="pip_output.mp4"
        )

        self.x_offset = tk.IntVar(
            value=10
        )

        self.y_offset = tk.IntVar(
            value=10
        )

        self.scale_width = tk.IntVar(
            value=320
        )

        self.scale_height = tk.IntVar(
            value=180
        )

        self.status_text = tk.StringVar(
            value="Ready"
        )

        self._build_style()

        self._build_ui()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _build_style(self):

        style = ttk.Style()

        try:

            style.theme_use(
                "clam"
            )

        except tk.TclError:

            pass

        style.configure(
            "App.TFrame",
            background=BG,
        )

        style.configure(
            "Card.TFrame",
            background=CARD,
        )

        style.configure(
            "Title.TLabel",
            background=BG,
            foreground=TEXT,
            font=(
                "Helvetica",
                24,
                "bold",
            ),
        )

        style.configure(
            "Description.TLabel",
            background=BG,
            foreground=MUTED,
            font=(
                "Helvetica",
                10,
            ),
        )

        style.configure(
            "Section.TLabel",
            background=CARD,
            foreground=TEXT,
            font=(
                "Helvetica",
                13,
                "bold",
            ),
        )

        style.configure(
            "Label.TLabel",
            background=CARD,
            foreground=MUTED,
            font=(
                "Helvetica",
                10,
            ),
        )

        style.configure(
            "Status.TLabel",
            background=BG,
            foreground=MUTED,
            font=(
                "Helvetica",
                10,
            ),
        )

        style.configure(
            "Value.TEntry",
            fieldbackground=INPUT_BG,
            foreground=TEXT,
            padding=7,
        )

        style.configure(
            "Accent.TButton",
            padding=(
                12,
                8,
            ),
            font=(
                "Helvetica",
                10,
                "bold",
            ),
        )

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=INPUT_BG,
            background=ACCENT,
        )

        style.map(
            "Accent.TButton",
            background=[
                (
                    "active",
                    ACCENT_HOVER,
                ),
            ],
        )

    # ------------------------------------------------------------------
    # User interface
    # ------------------------------------------------------------------

    def _build_ui(self):

        main = ttk.Frame(
            self.root,
            style="App.TFrame",
            padding=24,
        )

        main.pack(
            fill=tk.BOTH,
            expand=True,
        )

        # --------------------------------------------------------------
        # Header
        # --------------------------------------------------------------

        ttk.Label(
            main,
            text="Picture-in-Picture Video Maker",
            style="Title.TLabel",
        ).pack(
            anchor="w"
        )

        ttk.Label(
            main,
            text=(
                "Overlay one video on top of another "
                "and create a high-quality MP4 video."
            ),
            style="Description.TLabel",
        ).pack(
            anchor="w",
            pady=(
                4,
                20,
            ),
        )

        # --------------------------------------------------------------
        # Main card
        # --------------------------------------------------------------

        card = ttk.Frame(
            main,
            style="Card.TFrame",
            padding=20,
        )

        card.pack(
            fill=tk.BOTH,
            expand=True,
        )

        card.columnconfigure(
            1,
            weight=1,
        )

        # --------------------------------------------------------------
        # Files
        # --------------------------------------------------------------

        ttk.Label(
            card,
            text="Videos",
            style="Section.TLabel",
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
        )

        self._file_row(
            card,
            row=1,
            label="Background video",
            variable=self.background_video,
            title="Select background video",
        )

        self._file_row(
            card,
            row=2,
            label="Picture-in-Picture video",
            variable=self.pip_video,
            title="Select Picture-in-Picture video",
        )

        self._folder_row(
            card,
            row=3,
            label="Output folder",
            variable=self.output_folder,
        )

        # --------------------------------------------------------------
        # Output filename
        # --------------------------------------------------------------

        ttk.Label(
            card,
            text="Output filename",
            style="Label.TLabel",
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(
                12,
                4,
            ),
        )

        ttk.Entry(
            card,
            textvariable=self.output_name,
            style="Value.TEntry",
        ).grid(
            row=4,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(
                12,
                4,
            ),
        )

        ttk.Separator(
            card,
        ).grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=20,
        )

        # --------------------------------------------------------------
        # Overlay settings
        # --------------------------------------------------------------

        ttk.Label(
            card,
            text="Overlay Position and Size",
            style="Section.TLabel",
        ).grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="w",
        )

        self._spin_row(
            card,
            row=7,
            label="X offset (pixels)",
            variable=self.x_offset,
            minimum=0,
            maximum=10000,
            increment=1,
        )

        self._spin_row(
            card,
            row=8,
            label="Y offset (pixels)",
            variable=self.y_offset,
            minimum=0,
            maximum=10000,
            increment=1,
        )

        self._spin_row(
            card,
            row=9,
            label="PiP width (pixels)",
            variable=self.scale_width,
            minimum=16,
            maximum=7680,
            increment=1,
        )

        self._spin_row(
            card,
            row=10,
            label="PiP height (pixels)",
            variable=self.scale_height,
            minimum=16,
            maximum=4320,
            increment=1,
        )

        ttk.Separator(
            card,
        ).grid(
            row=11,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=20,
        )

        # --------------------------------------------------------------
        # Progress
        # --------------------------------------------------------------

        self.progress = ttk.Progressbar(
            card,
            mode="indeterminate",
            style="Accent.Horizontal.TProgressbar",
        )

        self.progress.grid(
            row=12,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(
                0,
                12,
            ),
        )

        self.run_button = ttk.Button(
            card,
            text="Create PiP Video",
            style="Accent.TButton",
            command=self._start,
        )

        self.run_button.grid(
            row=12,
            column=2,
            sticky="ew",
        )

        # --------------------------------------------------------------
        # Status
        # --------------------------------------------------------------

        ttk.Label(
            main,
            textvariable=self.status_text,
            style="Status.TLabel",
        ).pack(
            anchor="w",
            pady=(
                10,
                0,
            ),
        )

    # ------------------------------------------------------------------
    # UI helpers
    # ------------------------------------------------------------------

    def _file_row(
        self,
        parent,
        row,
        label,
        variable,
        title,
    ):

        ttk.Label(
            parent,
            text=label,
            style="Label.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(
                12,
                4,
            ),
        )

        ttk.Entry(
            parent,
            textvariable=variable,
            style="Value.TEntry",
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(
                12,
                8,
            ),
            pady=(
                12,
                4,
            ),
        )

        ttk.Button(
            parent,
            text="Browse...",
            command=lambda: self._select_video(
                variable,
                title,
            ),
        ).grid(
            row=row,
            column=2,
            sticky="ew",
            pady=(
                12,
                4,
            ),
        )

    def _folder_row(
        self,
        parent,
        row,
        label,
        variable,
    ):

        ttk.Label(
            parent,
            text=label,
            style="Label.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(
                12,
                4,
            ),
        )

        ttk.Entry(
            parent,
            textvariable=variable,
            style="Value.TEntry",
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(
                12,
                8,
            ),
            pady=(
                12,
                4,
            ),
        )

        ttk.Button(
            parent,
            text="Browse...",
            command=lambda: self._select_folder(
                variable,
                f"Select {label}",
            ),
        ).grid(
            row=row,
            column=2,
            sticky="ew",
            pady=(
                12,
                4,
            ),
        )

    def _spin_row(
        self,
        parent,
        row,
        label,
        variable,
        minimum,
        maximum,
        increment,
    ):

        ttk.Label(
            parent,
            text=label,
            style="Label.TLabel",
        ).grid(
            row=row,
            column=0,
            sticky="w",
            pady=(
                10,
                4,
            ),
        )

        ttk.Spinbox(
            parent,
            textvariable=variable,
            from_=minimum,
            to=maximum,
            increment=increment,
            width=14,
        ).grid(
            row=row,
            column=1,
            sticky="w",
            padx=(
                12,
                0,
            ),
            pady=(
                10,
                4,
            ),
        )

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------

    def _select_video(
        self,
        variable,
        title,
    ):

        path = filedialog.askopenfilename(
            title=title,
            filetypes=self.VIDEO_FILETYPES,
        )

        if not path:
            return

        variable.set(
            path
        )

        # Automatically suggest the video's folder
        # as the output folder if no folder is set.

        if not self.output_folder.get().strip():

            self.output_folder.set(
                str(
                    Path(path).parent
                )
            )

    def _select_folder(
        self,
        variable,
        title,
    ):

        path = filedialog.askdirectory(
            title=title,
        )

        if path:

            variable.set(
                path
            )

    # ------------------------------------------------------------------
    # Start conversion
    # ------------------------------------------------------------------

    def _start(self):

        # --------------------------------------------------------------
        # Capture values from Tkinter BEFORE starting the worker thread.
        # --------------------------------------------------------------

        background_text = (
            self.background_video.get().strip()
        )

        pip_text = (
            self.pip_video.get().strip()
        )

        output_folder_text = (
            self.output_folder.get().strip()
        )

        output_name = (
            self.output_name.get().strip()
            or "pip_output.mp4"
        )

        try:

            x_offset = self.x_offset.get()

            y_offset = self.y_offset.get()

            pip_width = self.scale_width.get()

            pip_height = self.scale_height.get()

        except tk.TclError:

            messagebox.showerror(
                "Invalid Settings",
                "Please enter valid numeric values.",
            )

            return

        # --------------------------------------------------------------
        # Validate FFmpeg
        # --------------------------------------------------------------

        if not shutil.which(
            "ffmpeg"
        ):

            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg was not found in your system PATH.",
            )

            return

        # --------------------------------------------------------------
        # Validate background video
        # --------------------------------------------------------------

        background_path = Path(
            background_text
        ).expanduser()

        if not background_path.is_file():

            messagebox.showerror(
                "Invalid Background Video",
                "Please select a valid background video.",
            )

            return

        # --------------------------------------------------------------
        # Validate PiP video
        # --------------------------------------------------------------

        pip_path = Path(
            pip_text
        ).expanduser()

        if not pip_path.is_file():

            messagebox.showerror(
                "Invalid PiP Video",
                "Please select a valid Picture-in-Picture video.",
            )

            return

        # --------------------------------------------------------------
        # Validate output folder
        # --------------------------------------------------------------

        if not output_folder_text:

            messagebox.showerror(
                "Invalid Output Folder",
                "Please select an output folder.",
            )

            return

        output_folder = Path(
            output_folder_text
        ).expanduser()

        try:

            output_folder.mkdir(
                parents=True,
                exist_ok=True,
            )

        except OSError as error:

            messagebox.showerror(
                "Output Folder Error",
                str(error),
            )

            return

        # --------------------------------------------------------------
        # Validate overlay settings
        # --------------------------------------------------------------

        if x_offset < 0 or y_offset < 0:

            messagebox.showerror(
                "Invalid Position",
                "X and Y offsets cannot be negative.",
            )

            return

        if pip_width <= 0 or pip_height <= 0:

            messagebox.showerror(
                "Invalid PiP Size",
                "PiP width and height must be greater than zero.",
            )

            return

        # --------------------------------------------------------------
        # Ensure MP4 extension
        # --------------------------------------------------------------

        if not output_name.lower().endswith(
            ".mp4"
        ):

            output_name += ".mp4"

        output_path = (
            output_folder /
            output_name
        )

        # --------------------------------------------------------------
        # Capture worker settings
        # --------------------------------------------------------------

        settings = {

            "background_path":
                background_path,

            "pip_path":
                pip_path,

            "output_path":
                output_path,

            "x_offset":
                x_offset,

            "y_offset":
                y_offset,

            "pip_width":
                pip_width,

            "pip_height":
                pip_height,
        }

        # --------------------------------------------------------------
        # Start conversion
        # --------------------------------------------------------------

        self.run_button.config(
            state=tk.DISABLED
        )

        self.progress.start(
            12
        )

        self._set_status(
            "Preparing Picture-in-Picture video..."
        )

        threading.Thread(
            target=self._build,
            args=(
                settings,
            ),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    # Build video
    # ------------------------------------------------------------------

    def _build(
        self,
        settings,
    ):

        try:

            background_path = settings[
                "background_path"
            ]

            pip_path = settings[
                "pip_path"
            ]

            output_path = settings[
                "output_path"
            ]

            x_offset = settings[
                "x_offset"
            ]

            y_offset = settings[
                "y_offset"
            ]

            pip_width = settings[
                "pip_width"
            ]

            pip_height = settings[
                "pip_height"
            ]

            # ----------------------------------------------------------
            # Video filter
            #
            # 0:v = background video
            # 1:v = Picture-in-Picture video
            # ----------------------------------------------------------

            filter_complex = (
                f"[1:v]"
                f"scale={pip_width}:{pip_height}"
                f"[pip];"

                f"[0:v]"
                f"[pip]"
                f"overlay={x_offset}:{y_offset}"
                f":shortest=1"
                f"[video]"
            )

            command = [

                "ffmpeg",

                "-y",

                "-i",
                str(background_path),

                "-i",
                str(pip_path),

                "-filter_complex",
                filter_complex,

                "-map",
                "[video]",

                # Preserve background audio if available.
                "-map",
                "0:a?",

                "-c:v",
                "libx264",

                "-preset",
                "medium",

                "-crf",
                "18",

                "-c:a",
                "aac",

                "-b:a",
                "192k",

                "-movflags",
                "+faststart",

                "-shortest",

                str(output_path),
            ]

            self._set_status(
                "Creating Picture-in-Picture video..."
            )

            result = subprocess.run(

                command,

                stdout=subprocess.PIPE,

                stderr=subprocess.PIPE,

                text=True,

            )

            if result.returncode != 0:

                error_message = (
                    result.stderr.strip()
                    or
                    "FFmpeg failed to create the video."
                )

                raise RuntimeError(
                    error_message
                )

            if not output_path.is_file():

                raise RuntimeError(
                    "FFmpeg finished, but the output "
                    "video file was not created."
                )

            if output_path.stat().st_size == 0:

                raise RuntimeError(
                    "The output video file was created "
                    "but is empty."
                )

            self._finish(
                True,
                (
                    "Picture-in-Picture video created "
                    "successfully:\n\n"
                    f"{output_path}"
                ),
            )

        except Exception as error:

            self._finish(
                False,
                str(error),
            )

    # ------------------------------------------------------------------
    # Thread-safe UI updates
    # ------------------------------------------------------------------

    def _set_status(
        self,
        message,
    ):

        self.root.after(
            0,
            lambda: self.status_text.set(
                message
            ),
        )

    def _finish(
        self,
        success,
        message,
    ):

        self.root.after(
            0,
            lambda: self._finish_ui(
                success,
                message,
            ),
        )

    def _finish_ui(
        self,
        success,
        message,
    ):

        self.progress.stop()

        self.run_button.config(
            state=tk.NORMAL
        )

        if success:

            self.status_text.set(
                "Picture-in-Picture video created successfully."
            )

            messagebox.showinfo(
                "Video Created",
                message,
            )

        else:

            self.status_text.set(
                "Video creation failed."
            )

            messagebox.showerror(
                "Error",
                message,
            )


# ----------------------------------------------------------------------
# Application entry point
# ----------------------------------------------------------------------

def main():

    root = tk.Tk()

    PipVideoApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":

    main()