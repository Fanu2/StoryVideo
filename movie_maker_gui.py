import os
import re
import shutil
import subprocess
import threading
import tkinter as tk

from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext, ttk


SUPPORTED_IMAGES = {".jpg", ".jpeg", ".png", ".webp"}
SUPPORTED_AUDIO = (
    "*.mp3 *.wav *.m4a *.aac *.ogg *.flac"
)


def natural_sort_key(value):
    """
    Sort filenames naturally:
    1.jpg, 2.jpg, 10.jpg
    instead of:
    1.jpg, 10.jpg, 2.jpg
    """
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", value)
    ]


class MovieMakerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Movie Maker with Background Music")
        self.root.geometry("700x560")
        self.root.minsize(600, 450)

        self.image_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.background_music = tk.StringVar()

        self.duration_per_image = tk.IntVar(value=5)
        self.rename_sequentially = tk.BooleanVar(value=False)
        self.keep_individual = tk.BooleanVar(value=False)

        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=12)
        main.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main,
            text="Images folder:"
        ).grid(
            row=0,
            column=0,
            sticky="w",
            pady=(0, 4)
        )

        self._browse_row(
            main,
            1,
            self.image_folder,
            self._select_image_folder,
            "Select images folder"
        )

        ttk.Label(
            main,
            text="Output folder:"
        ).grid(
            row=2,
            column=0,
            sticky="w",
            pady=(8, 4)
        )

        self._browse_row(
            main,
            3,
            self.output_folder,
            self._select_output_folder,
            "Select output folder"
        )

        ttk.Label(
            main,
            text="Background music (optional):"
        ).grid(
            row=4,
            column=0,
            sticky="w",
            pady=(8, 4)
        )

        self._browse_row(
            main,
            5,
            self.background_music,
            self._select_music,
            "Select background music"
        )

        # --------------------------------------------------------------
        # Options
        # --------------------------------------------------------------

        options = ttk.LabelFrame(
            main,
            text="Options",
            padding=10
        )

        options.grid(
            row=6,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(10, 6)
        )

        ttk.Label(
            options,
            text="Seconds per image:"
        ).grid(
            row=0,
            column=0,
            sticky="w"
        )

        ttk.Spinbox(
            options,
            from_=1,
            to=120,
            textvariable=self.duration_per_image,
            width=6
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(8, 20)
        )

        ttk.Checkbutton(
            options,
            text="Rename images sequentially (1.jpg, 2.jpg, ...)",
            variable=self.rename_sequentially
        ).grid(
            row=1,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(8, 0)
        )

        ttk.Checkbutton(
            options,
            text="Also create individual videos for each image",
            variable=self.keep_individual
        ).grid(
            row=2,
            column=0,
            columnspan=3,
            sticky="w",
            pady=(4, 0)
        )

        # --------------------------------------------------------------
        # Log
        # --------------------------------------------------------------

        ttk.Label(
            main,
            text="Log:"
        ).grid(
            row=7,
            column=0,
            sticky="w",
            pady=(6, 4)
        )

        self.log_area = scrolledtext.ScrolledText(
            main,
            height=12,
            state=tk.DISABLED
        )

        self.log_area.grid(
            row=8,
            column=0,
            columnspan=3,
            sticky="nsew"
        )

        # --------------------------------------------------------------
        # Controls
        # --------------------------------------------------------------

        run_frame = ttk.Frame(main)

        run_frame.grid(
            row=9,
            column=0,
            columnspan=3,
            sticky="ew",
            pady=(10, 0)
        )

        self.progress = ttk.Progressbar(
            run_frame,
            mode="indeterminate"
        )

        self.progress.pack(
            side=tk.LEFT,
            fill=tk.X,
            expand=True,
            padx=(0, 10)
        )

        self.run_button = ttk.Button(
            run_frame,
            text="Create Movie",
            command=self._start
        )

        self.run_button.pack(
            side=tk.RIGHT
        )

        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(8, weight=1)

    # ------------------------------------------------------------------
    # File selection
    # ------------------------------------------------------------------

    def _browse_row(self, parent, row, variable, action, title):

        entry = ttk.Entry(
            parent,
            textvariable=variable
        )

        entry.grid(
            row=row,
            column=0,
            columnspan=2,
            sticky="ew",
            padx=(0, 6)
        )

        ttk.Button(
            parent,
            text="Browse...",
            command=lambda: action(title)
        ).grid(
            row=row,
            column=2,
            sticky="ew"
        )

    def _select_image_folder(self, title):

        path = filedialog.askdirectory(
            title=title
        )

        if path:
            self.image_folder.set(path)

            if not self.output_folder.get():
                self.output_folder.set(path)

    def _select_output_folder(self, title):

        path = filedialog.askdirectory(
            title=title
        )

        if path:
            self.output_folder.set(path)

    def _select_music(self, title):

        path = filedialog.askopenfilename(
            title=title,
            filetypes=[
                ("Audio files", SUPPORTED_AUDIO),
                ("All files", "*.*")
            ]
        )

        if path:
            self.background_music.set(path)

    # ------------------------------------------------------------------
    # Thread-safe UI helpers
    # ------------------------------------------------------------------

    def _log(self, message):

        self.root.after(
            0,
            self._write_log,
            message
        )

    def _write_log(self, message):

        self.log_area.config(
            state=tk.NORMAL
        )

        self.log_area.insert(
            tk.END,
            message + "\n"
        )

        self.log_area.see(
            tk.END
        )

        self.log_area.config(
            state=tk.DISABLED
        )

    def _finish(self, success, message):

        self.root.after(
            0,
            self._finish_ui,
            success,
            message
        )

    def _finish_ui(self, success, message):

        self.progress.stop()

        self.run_button.config(
            state=tk.NORMAL
        )

        if success:

            self._write_log(message)

            messagebox.showinfo(
                "Done",
                message
            )

        else:

            self._write_log(
                f"ERROR: {message}"
            )

            messagebox.showerror(
                "Error",
                message
            )

    # ------------------------------------------------------------------
    # Start
    # ------------------------------------------------------------------

    def _start(self):

        image_folder = self.image_folder.get()
        output_folder = self.output_folder.get()

        if not image_folder or not output_folder:

            messagebox.showerror(
                "Error",
                "Please select the image and output folders."
            )

            return

        if not shutil.which("ffmpeg"):

            messagebox.showerror(
                "FFmpeg not found",
                "FFmpeg is not installed or is not available in PATH."
            )

            return

        os.makedirs(
            output_folder,
            exist_ok=True
        )

        self.run_button.config(
            state=tk.DISABLED
        )

        self.progress.start(10)

        threading.Thread(
            target=self._build_movie,
            daemon=True
        ).start()

    # ------------------------------------------------------------------
    # Image handling
    # ------------------------------------------------------------------

    def _get_images(self, folder):

        images = [
            path
            for path in Path(folder).iterdir()
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_IMAGES
        ]

        return sorted(
            images,
            key=lambda path: natural_sort_key(path.name)
        )

    def _rename_images_sequentially(self, images):

        self._log(
            "Renaming images sequentially..."
        )

        temporary_files = []

        # Stage 1:
        # Rename everything to unique temporary names.
        for index, image in enumerate(images):

            temporary = image.with_name(
                f".movie_maker_tmp_{index}{image.suffix.lower()}"
            )

            image.rename(
                temporary
            )

            temporary_files.append(
                temporary
            )

        # Stage 2:
        # Rename temporary files to final names.
        renamed_images = []

        for index, temporary in enumerate(temporary_files):

            final_name = temporary.with_name(
                f"{index + 1}{temporary.suffix.lower()}"
            )

            temporary.rename(
                final_name
            )

            renamed_images.append(
                final_name
            )

        return renamed_images

    # ------------------------------------------------------------------
    # FFmpeg execution
    # ------------------------------------------------------------------

    def _run_ffmpeg(self, command):

        self._log(
            "Running FFmpeg..."
        )

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        if result.stdout:

            self._log(
                result.stdout[-2000:]
            )

        if result.returncode != 0:

            raise RuntimeError(
                "FFmpeg failed."
            )

    # ------------------------------------------------------------------
    # Movie creation
    # ------------------------------------------------------------------

    def _build_movie(self):

        try:

            self._log(
                "Starting movie creation..."
            )

            image_folder = Path(
                self.image_folder.get()
            )

            output_folder = Path(
                self.output_folder.get()
            )

            music = self.background_music.get()

            duration = self.duration_per_image.get()

            if not image_folder.is_dir():

                raise RuntimeError(
                    f"Image folder does not exist:\n{image_folder}"
                )

            images = self._get_images(
                image_folder
            )

            if not images:

                raise RuntimeError(
                    "No supported images found.\n"
                    "Supported formats: JPG, JPEG, PNG, WEBP."
                )

            if self.rename_sequentially.get():

                images = self._rename_images_sequentially(
                    images
                )

            output_folder.mkdir(
                parents=True,
                exist_ok=True
            )

            base_name = image_folder.name

            output_video = (
                output_folder /
                f"{base_name}.mp4"
            )

            final_output = (
                output_folder /
                f"{base_name}_with_music.mp4"
            )

            # ----------------------------------------------------------
            # Individual videos
            # ----------------------------------------------------------

            if self.keep_individual.get():

                self._log(
                    "Creating individual videos..."
                )

                self._create_individual_videos(
                    images,
                    output_folder,
                    duration
                )

            # ----------------------------------------------------------
            # Combined movie
            # ----------------------------------------------------------

            self._log(
                f"Creating combined movie from "
                f"{len(images)} images..."
            )

            self._create_combined_movie(
                images,
                output_video,
                duration
            )

            # ----------------------------------------------------------
            # Add music
            # ----------------------------------------------------------

            if music:

                music_path = Path(
                    music
                )

                if not music_path.is_file():

                    raise RuntimeError(
                        f"Music file does not exist:\n{music_path}"
                    )

                self._log(
                    "Adding background music..."
                )

                self._add_background_music(
                    output_video,
                    music_path,
                    final_output
                )

                try:
                    output_video.unlink()
                except OSError:
                    pass

                result_message = (
                    "Movie created successfully:\n"
                    f"{final_output}"
                )

            else:

                result_message = (
                    "Movie created successfully:\n"
                    f"{output_video}"
                )

            self._finish(
                True,
                result_message
            )

        except Exception as error:

            self._finish(
                False,
                str(error)
            )

    # ------------------------------------------------------------------
    # Individual videos
    # ------------------------------------------------------------------

    def _create_individual_videos(
        self,
        images,
        output_folder,
        duration
    ):

        individual_folder = (
            output_folder /
            "individual_videos"
        )

        individual_folder.mkdir(
            exist_ok=True
        )

        for index, image in enumerate(images, start=1):

            output_file = (
                individual_folder /
                f"{image.stem}.mp4"
            )

            self._log(
                f"Creating individual video "
                f"{index}/{len(images)}..."
            )

            command = [
                "ffmpeg",
                "-y",
                "-loop", "1",
                "-i", str(image),
                "-t", str(duration),
                "-r", "30",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                str(output_file)
            ]

            self._run_ffmpeg(
                command
            )

    # ------------------------------------------------------------------
    # Combined movie
    # ------------------------------------------------------------------

    def _create_combined_movie(
        self,
        images,
        output_file,
        duration
    ):

        list_file = (
            output_file.parent /
            ".movie_maker_images.txt"
        )

        try:

            with open(
                list_file,
                "w",
                encoding="utf-8"
            ) as file:

                for image in images:

                    safe_path = (
                        str(image.resolve())
                        .replace("'", r"'\''")
                    )

                    file.write(
                        f"file '{safe_path}'\n"
                    )

                    file.write(
                        f"duration {duration}\n"
                    )

                # FFmpeg concat demuxer needs
                # the last image repeated.
                last_image = (
                    str(images[-1].resolve())
                    .replace("'", r"'\''")
                )

                file.write(
                    f"file '{last_image}'\n"
                )

            command = [
                "ffmpeg",
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", str(list_file),
                "-vsync", "vfr",
                "-pix_fmt", "yuv420p",
                "-c:v", "libx264",
                str(output_file)
            ]

            self._run_ffmpeg(
                command
            )

        finally:

            try:
                list_file.unlink()
            except OSError:
                pass

    # ------------------------------------------------------------------
    # Background music
    # ------------------------------------------------------------------

    def _add_background_music(
        self,
        video_file,
        music_file,
        output_file
    ):

        command = [
            "ffmpeg",
            "-y",
            "-stream_loop", "-1",
            "-i", str(music_file),
            "-i", str(video_file),
            "-map", "1:v:0",
            "-map", "0:a:0",
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            str(output_file)
        ]

        self._run_ffmpeg(
            command
        )


def main():

    root = tk.Tk()

    MovieMakerApp(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()