"""
Media Metadata Layer

Future responsibility:

- image dimensions
- video duration
- audio duration
- codecs
- thumbnails
- checksums

Currently only provides extension helpers.
"""


from pathlib import Path



def get_extension(path):

    return Path(path).suffix.lower()



def get_media_category(path):

    ext = get_extension(path)


    if ext in [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    ]:

        return "image"


    if ext in [
        ".mp4",
        ".mkv",
        ".avi",
        ".mov"
    ]:

        return "video"


    if ext in [
        ".mp3",
        ".wav",
        ".ogg"
    ]:

        return "audio"


    return "unknown"
