from __future__ import annotations

import os
import re
import shutil
import tempfile
import threading
import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageDraw, ImageFont

try:
    from moviepy import (
        AudioFileClip,
        ImageSequenceClip,
    )
except ImportError:
    from moviepy.editor import (
        AudioFileClip,
        ImageSequenceClip,
    )

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

SUCCESS = "#a6e3a1"

class TextVideoApp:
    """
    Create an MP4 slideshow from PNG, JPG, and JPEG images.

    Features:
    - Natural image sorting
    - Optional text caption
    - Custom font and colour
    - Aspect-ratio-preserving resize
    - Letterboxing instead of image distortion
    - Temporary frame preparation to reduce RAM usage
    - Thread-safe GUI updates
    - Output folder browsing
    - Configurable total slideshow duration
    """

    SUPPORTED_FORMATS = (
        ".jpg",
        ".jpeg",
        ".png",
    )

    def __init__(self, root):

        self.root = root

        self.root.title(
            "Image Slideshow Video Maker"
        )

        self.root.geometry(
            "760x780"
        )

        self.root.minsize(
            680,
            620,
        )

        self.root.configure(
            bg=BG
        )

        # ----------------------------------------------------------
        # Application state
        # ----------------------------------------------------------

        self.input_folder = tk.StringVar()

        self.output_folder = tk.StringVar(
            value=str(Path.home())
        )

        self.output_name = tk.StringVar(
            value="video.mp4"
        )

        # ----------------------------------------------------------
        # Text settings
        # ----------------------------------------------------------

        self.text = tk.StringVar(
            value="Love u Jodha"
        )

        self.font_path = tk.StringVar()

        self.font_size = tk.IntVar(
            value=70
        )

        self.font_color = "#ffffff"

        # ----------------------------------------------------------
        # Video settings
        # ----------------------------------------------------------

        self.total_duration = tk.IntVar(
            value=30
        )

        self.width = tk.IntVar(
            value=1920
        )

        self.height = tk.IntVar(
            value=1080
        )

        self.fps = tk.IntVar(
            value=24
        )

        self.resize = tk.BooleanVar(
            value=True
        )

        self.loop = tk.BooleanVar(
            value=False
        )

        # ----------------------------------------------------------
        # Application status
        # ----------------------------------------------------------

        self.status_text = tk.StringVar(
            value="Ready"
        )

        # ----------------------------------------------------------
        # Build interface
        # ----------------------------------------------------------

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
                22,
                "bold",
            ),
        )

        style.configure(
            "Sub.TLabel",
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
            fieldbackground="#181825",
            foreground=TEXT,
            padding=7,
        )

        style.configure(
            "Accent.TButton",
            padding=(
                14,
                8,
            ),
        )

        style.configure(
            "Accent.Horizontal.TProgressbar",
            troughcolor=CARD,
            background=ACCENT,
        )

    # ------------------------------------------------------------------
    # User interface
    # ------------------------------------------------------------------

    def _build_ui(self):

        main = ttk.Frame(
            self.root,
            style="App.TFrame",
            padding=20,
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
            text="Image Slideshow Video Maker",
            style="Title.TLabel",
        ).pack(
            anchor="w"
        )

        ttk.Label(
            main,
            text=(
                "Turn PNG, JPG, and JPEG images into a "
                "high-quality MP4 slideshow with captions."
            ),
            style="Sub.TLabel",
        ).pack(
            anchor="w",
            pady=(
                4,
                18,
            ),
        )

        # --------------------------------------------------------------
        # Main card
        # --------------------------------------------------------------

        card = ttk.Frame(
            main,
            style="Card.TFrame",
            padding=18,
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
            text="Files",
            style="Section.TLabel",
        ).grid(
            row=0,
            column=0,
            columnspan=3,
            sticky="w",
        )

        self._folder_row(
            card,
            1,
            "Images folder",
            self.input_folder,
        )

        self._folder_row(
            card,
            2,
            "Output folder",
            self.output_folder,
        )

        ttk.Label(
            card,
            text="Output file",
            style="Label.TLabel",
        ).grid(
            row=3,
            column=0,
            sticky="w",
            pady=(
                10,
                4,
            ),
        )

        ttk.Entry(
            card,
            textvariable=self.output_name,
            style="Value.TEntry",
        ).grid(
            row=3,
            column=1,
            columnspan=2,
            sticky="ew",
            pady=(
                10,
                4,
            ),
        )

        # --------------------------------------------------------------
        # Caption
        # --------------------------------------------------------------

        ttk.Separator(
            card,
        ).grid(
            row=4,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=16,
        )

        ttk.Label(
            card,
            text="Caption",
            style="Section.TLabel",
        ).grid(
            row=5,
            column=0,
            columnspan=3,
            sticky="w",
        )

        ttk.Entry(
            card,
            textvariable=self.text,
            style="Value.TEntry",
        ).grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(
                8,
                4,
            ),
        )

        self._font_row(
            card,
            7,
        )

        self._color_row(
            card,
            8,
        )

        self._spin(
            card,
            9,
            "Font size",
            self.font_size,
            (
                8,
                300,
                1,
            ),
        )

        # --------------------------------------------------------------
        # Video settings
        # --------------------------------------------------------------

        ttk.Separator(
            card,
        ).grid(
            row=10,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=16,
        )

        ttk.Label(
            card,
            text="Video Settings",
            style="Section.TLabel",
        ).grid(
            row=11,
            column=0,
            columnspan=3,
            sticky="w",
        )

        # --------------------------------------------------------------
        # Total duration
        # --------------------------------------------------------------

        self._spin(
            card,
            12,
            "Total duration (seconds)",
            self.total_duration,
            (
                1,
                7200,
                1,
            ),
        )

        self._spin(
            card,
            13,
            "Width (px)",
            self.width,
            (
                64,
                7680,
                1,
            ),
        )

        self._spin(
            card,
            14,
            "Height (px)",
            self.height,
            (
                64,
                4320,
                1,
            ),
        )

        self._spin(
            card,
            15,
            "FPS",
            self.fps,
            (
                1,
                120,
                1,
            ),
        )

        ttk.Checkbutton(
            card,
            text=(
                "Fit images to video size "
                "(preserve aspect ratio)"
            ),
            variable=self.resize,
        ).grid(
            row=16,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(
                8,
                0,
            ),
        )

        # --------------------------------------------------------------
        # Progress
        # --------------------------------------------------------------

        ttk.Separator(
            card,
        ).grid(
            row=17,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=16,
        )

        self.progress = ttk.Progressbar(
            card,
            mode="indeterminate",
            style="Accent.Horizontal.TProgressbar",
        )

        self.progress.grid(
            row=18,
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
            text="Create Video",
            style="Accent.TButton",
            command=self._start,
        )

        self.run_button.grid(
            row=19,
            column=2,
            sticky="ew",
        )

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
                10,
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
                10,
                4,
            ),
        )

        ttk.Button(
            parent,
            text="Browse...",
            command=lambda:
                self._pick_folder(
                    variable,
                    f"Select {label}",
                ),
        ).grid(
            row=row,
            column=2,
            sticky="ew",
            pady=(
                10,
                4,
            ),
        )

    def _font_row(
        self,
        parent,
        row,
    ):

        ttk.Label(
            parent,
            text="Font",
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

        ttk.Entry(
            parent,
            textvariable=self.font_path,
            style="Value.TEntry",
        ).grid(
            row=row,
            column=1,
            sticky="ew",
            padx=(
                12,
                8,
            ),
        )

        ttk.Button(
            parent,
            text="Browse...",
            command=self._select_font,
        ).grid(
            row=row,
            column=2,
            sticky="ew",
        )

    def _color_row(
        self,
        parent,
        row,
    ):

        ttk.Label(
            parent,
            text="Text color",
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

        self.color_swatch = tk.Canvas(
            parent,
            width=28,
            height=24,
            bg=self.font_color,
            highlightthickness=1,
        )

        self.color_swatch.grid(
            row=row,
            column=1,
            sticky="w",
            padx=(
                12,
                0,
            ),
        )

        ttk.Button(
            parent,
            text="Choose...",
            command=self._pick_color,
        ).grid(
            row=row,
            column=2,
            sticky="ew",
        )

    def _spin(
        self,
        parent,
        row,
        label,
        variable,
        range_,
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
            from_=range_[0],
            to=range_[1],
            increment=range_[2],
            width=14,
        ).grid(
            row=row,
            column=1,
            sticky="w",
            padx=(
                12,
                0,
            ),
        )

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------

    def _pick_folder(
        self,
        variable,
        title,
    ):

        path = filedialog.askdirectory(
            title=title
        )

        if path:

            variable.set(
                path
            )

    def _select_font(self):

        path = filedialog.askopenfilename(
            title="Select font file",
            filetypes=[
                (
                    "TrueType fonts",
                    "*.ttf *.otf",
                ),
                (
                    "All files",
                    "*.*",
                ),
            ],
        )

        if path:

            self.font_path.set(
                path
            )

    def _pick_color(self):

        color = colorchooser.askcolor(
            initialcolor=self.font_color
        )[1]

        if color:

            self.font_color = color

            self.color_swatch.config(
                bg=color
            )

    # ------------------------------------------------------------------
    # Start conversion
    # ------------------------------------------------------------------

    def _start(self):

        # ----------------------------------------------------------
        # Capture all Tkinter values in the main thread.
        # ----------------------------------------------------------

        input_folder_text = (
            self.input_folder.get().strip()
        )

        output_folder_text = (
            self.output_folder.get().strip()
        )

        output_name = (
            self.output_name.get().strip()
            or "video.mp4"
        )

        caption = (
            self.text.get()
        )

        font_path = (
            self.font_path.get().strip()
        )

        font_color = (
            self.font_color
        )

        resize = (
            self.resize.get()
        )

        try:

            # ------------------------------------------------------
            # Video settings
            # ------------------------------------------------------

            duration = self.total_duration.get()

            width = self.width.get()

            height = self.height.get()

            fps = self.fps.get()

            # ------------------------------------------------------
            # Text settings
            # ------------------------------------------------------

            font_size = self.font_size.get()

        except tk.TclError:

            messagebox.showerror(
                "Invalid Settings",
                "Please enter valid numeric values.",
            )

            return

        # ----------------------------------------------------------
        # Validate folders
        # ----------------------------------------------------------

        if not input_folder_text:

            messagebox.showerror(
                "Input Folder",
                "Please select an images folder.",
            )

            return

        input_folder = Path(
            input_folder_text
        ).expanduser()

        if not input_folder.is_dir():

            messagebox.showerror(
                "Input Folder",
                "The selected images folder does not exist.",
            )

            return

        if not output_folder_text:

            messagebox.showerror(
                "Output Folder",
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

        # ----------------------------------------------------------
        # Validate video settings
        # ----------------------------------------------------------

        if duration <= 0:

            messagebox.showerror(
                "Invalid Duration",
                "Total duration must be greater than zero.",
            )

            return

        if width <= 0 or height <= 0:

            messagebox.showerror(
                "Invalid Resolution",
                "Width and height must be greater than zero.",
            )

            return

        if fps <= 0:

            messagebox.showerror(
                "Invalid FPS",
                "FPS must be greater than zero.",
            )

            return

        if font_size <= 0:

            messagebox.showerror(
                "Invalid Font Size",
                "Font size must be greater than zero.",
            )

            return

        # ----------------------------------------------------------
        # FFmpeg check
        # ----------------------------------------------------------

        if not shutil.which(
            "ffmpeg"
        ):

            messagebox.showerror(
                "FFmpeg Not Found",
                "FFmpeg was not found in your system PATH.",
            )

            return

        # ----------------------------------------------------------
        # Find images
        # ----------------------------------------------------------

        images = self._find_images(
            input_folder
        )

        if not images:

            messagebox.showerror(
                "No Images Found",
                "No PNG, JPG, or JPEG images were found.",
            )

            return

        # ----------------------------------------------------------
        # Output filename
        # ----------------------------------------------------------

        if not output_name.lower().endswith(
            ".mp4"
        ):

            output_name += ".mp4"

        output_path = (
            output_folder /
            output_name
        )

        # ----------------------------------------------------------
        # Worker settings
        # ----------------------------------------------------------

        settings = {

            "images": images,

            "output_path": output_path,

            # ------------------------------------------------------
            # IMPORTANT:
            # Total slideshow duration in seconds.
            # This fixes the KeyError: 'duration'
            # ------------------------------------------------------

            "duration": duration,

            "caption": caption,

            "font_path": font_path,

            "font_color": font_color,

            "font_size": font_size,

            "width": width,

            "height": height,

            "fps": fps,

            "resize": resize,
        }

        # ----------------------------------------------------------
        # Start processing
        # ----------------------------------------------------------

        self.run_button.config(
            state=tk.DISABLED
        )

        self.progress.start(
            12
        )

        self._set_status(
            f"Found {len(images)} images. "
            f"Creating {duration}-second video..."
        )

        threading.Thread(
            target=self._build,
            args=(
                settings,
            ),
            daemon=True,
        ).start()

    # ------------------------------------------------------------------
    # Image discovery
    # ------------------------------------------------------------------

    def _find_images(
        self,
        folder,
    ):

        images = [

            path

            for path in folder.iterdir()

            if (
                path.is_file()
                and path.suffix.lower()
                in self.SUPPORTED_FORMATS
            )

        ]

        return sorted(
            images,
            key=self._natural_sort_key,
        )

    @staticmethod
    def _natural_sort_key(
        path,
    ):

        return [

            int(part)
            if part.isdigit()
            else part.lower()

            for part in re.split(
                r"(\d+)",
                path.name,
            )

        ]

    # ------------------------------------------------------------------
    # Frame preparation
    # ------------------------------------------------------------------

    def _render_frame(
        self,
        image_path,
        output_path,
        settings,
    ):

        with Image.open(
            image_path
        ) as image:

            image = image.convert(
                "RGB"
            )

            width = settings[
                "width"
            ]

            height = settings[
                "height"
            ]

            if settings[
                "resize"
            ]:

                image.thumbnail(
                    (
                        width,
                        height,
                    ),
                    Image.Resampling.LANCZOS,
                )

                canvas = Image.new(
                    "RGB",
                    (
                        width,
                        height,
                    ),
                    "black",
                )

                x = (
                    width - image.width
                ) // 2

                y = (
                    height - image.height
                ) // 2

                canvas.paste(
                    image,
                    (
                        x,
                        y,
                    ),
                )

                image = canvas

            # ------------------------------------------------------
            # Caption
            # ------------------------------------------------------

            caption = settings[
                "caption"
            ].strip()

            if caption:

                draw = ImageDraw.Draw(
                    image
                )

                font = self._load_font(
                    settings
                )

                bbox = draw.textbbox(
                    (
                        0,
                        0,
                    ),
                    caption,
                    font=font,
                )

                text_width = (
                    bbox[2] - bbox[0]
                )

                text_height = (
                    bbox[3] - bbox[1]
                )

                x = (
                    image.width - text_width
                ) // 2

                y = (
                    image.height
                    - text_height
                    - 30
                )

                draw.text(
                    (
                        x,
                        y,
                    ),
                    caption,
                    font=font,
                    fill=settings[
                        "font_color"
                    ],
                )

            image.save(
                output_path,
                "PNG",
            )

    def _load_font(
        self,
        settings,
    ):

        font_path = settings[
            "font_path"
        ]

        font_size = settings[
            "font_size"
        ]

        if font_path:

            try:

                return ImageFont.truetype(
                    font_path,
                    font_size,
                )

            except OSError:

                pass

        fallback_fonts = [

            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",

            "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
        ]

        for path in fallback_fonts:

            if os.path.isfile(
                path
            ):

                try:

                    return ImageFont.truetype(
                        path,
                        font_size,
                    )

                except OSError:

                    pass

        return ImageFont.load_default()

    # ------------------------------------------------------------------
    # Build video
    # ------------------------------------------------------------------

    def _build(
        self,
        settings,
    ):

        clip = None

        try:

            images = settings[
                "images"
            ]

            output_path = settings[
                "output_path"
            ]

            duration = settings[
                "duration"
            ]

            fps = settings[
                "fps"
            ]

            total_images = len(
                images
            )

            if total_images == 0:

                raise RuntimeError(
                    "No images were found."
                )

            # --------------------------------------------------
            # Calculate how long each image should appear.
            #
            # Example:
            # 22 images / 30-second video
            # = approximately 1.36 seconds per image.
            # --------------------------------------------------

            image_duration = (
                duration / total_images
            )

            with tempfile.TemporaryDirectory() as temp_dir:

                temp_dir = Path(
                    temp_dir
                )

                prepared_images = []

                # --------------------------------------------------
                # Process images one at a time.
                #
                # This avoids storing all high-resolution images
                # in RAM.
                # --------------------------------------------------

                for index, image_path in enumerate(
                    images,
                    start=1,
                ):

                    self._set_status(
                        f"Preparing image "
                        f"{index} of "
                        f"{total_images}..."
                    )

                    prepared_path = (
                        temp_dir /
                        f"frame_{index:06d}.png"
                    )

                    self._render_frame(
                        image_path,
                        prepared_path,
                        settings,
                    )

                    prepared_images.append(
                        str(
                            prepared_path
                        )
                    )

                # --------------------------------------------------
                # Create video.
                #
                # IMPORTANT:
                # Each image receives image_duration seconds.
                # --------------------------------------------------

                self._set_status(
                    "Creating video..."
                )

                clip = ImageSequenceClip(
                    prepared_images,
                    durations=[
                        image_duration
                        for _ in prepared_images
                    ],
                )

                # --------------------------------------------------
                # Explicitly enforce the requested final duration.
                # --------------------------------------------------

                try:

                    clip = clip.with_duration(
                        duration
                    )

                except AttributeError:

                    clip = clip.set_duration(
                        duration
                    )

                # --------------------------------------------------
                # Write MP4 file.
                # --------------------------------------------------

                self._set_status(
                    "Writing MP4 file..."
                )

                clip.write_videofile(
                    str(
                        output_path
                    ),
                    codec="libx264",
                    audio=False,
                    fps=fps,
                    logger=None,
                    threads=4,
                )

            self._finish(
                True,
                (
                    "Video created successfully:\n\n"
                    f"{output_path}"
                ),
            )

        except Exception as error:

            self._finish(
                False,
                str(
                    error
                ),
            )

        finally:

            if clip is not None:

                try:

                    clip.close()

                except Exception:

                    pass

    # ------------------------------------------------------------------
    # Thread-safe status updates
    # ------------------------------------------------------------------

    def _set_status(
        self,
        message,
    ):

        self.root.after(
            0,
            lambda:
                self.status_text.set(
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
            lambda:
                self._finish_ui(
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
                "Video created successfully."
            )

            messagebox.showinfo(
                "Success",
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

    TextVideoApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()