from pathlib import Path


IMAGE_TYPES = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp"
}

VIDEO_TYPES = {
    ".mp4",
    ".mkv",
    ".avi",
    ".mov"
}

AUDIO_TYPES = {
    ".mp3",
    ".wav",
    ".ogg"
}


def scan_folder(folder):

    folder = Path(folder)

    media = []

    for file in sorted(folder.iterdir()):

        if not file.is_file():
            continue

        ext = file.suffix.lower()

        if ext in IMAGE_TYPES:
            media.append(
                (
                    str(file),
                    "image"
                )
            )

        elif ext in VIDEO_TYPES:
            media.append(
                (
                    str(file),
                    "video"
                )
            )

        elif ext in AUDIO_TYPES:
            media.append(
                (
                    str(file),
                    "audio"
                )
            )

    return media
