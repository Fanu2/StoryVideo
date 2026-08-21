from pathlib import Path

from PIL import Image, ImageOps


DEFAULT_SIZE = (1920, 1080)


def normalize_image(
    input_file,
    output_file,
    size=DEFAULT_SIZE
):

    img = Image.open(
        input_file
    ).convert(
        "RGB"
    )


    img = ImageOps.fit(
        img,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5)
    )


    Path(
        output_file
    ).parent.mkdir(
        parents=True,
        exist_ok=True
    )


    img.save(
        output_file,
        quality=95
    )


    return output_file
