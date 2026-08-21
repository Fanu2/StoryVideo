"""
Media Storage Layer

Responsible only for filesystem operations.

Responsibilities:
- create media folders
- copy files
- move files
- remove files
- check file existence

No UI logic.
No database logic.
No rendering logic.
"""


from pathlib import Path
import shutil



def ensure_folder(folder):
    """
    Create folder if missing.
    """

    path = Path(folder)

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path



def copy_file(
    source,
    destination
):
    """
    Copy media file.
    """

    source = Path(source)
    destination = Path(destination)


    ensure_folder(
        destination.parent
    )


    if not destination.exists():

        shutil.copy2(
            source,
            destination
        )


    return destination



def file_exists(path):

    return Path(path).exists()
