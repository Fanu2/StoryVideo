"""
Media Manager Layer

Handles project-owned assets.

Uses project_id as the permanent identity.

Responsibilities:
- calculate managed asset location
- prepare imported assets
- avoid duplicate copies

No UI logic.
No database logic.
"""


from pathlib import Path

from .storage import (
    copy_file,
)

from .metadata import (
    get_media_category,
)



def create_project_media_path(
    project_id,
    source_file
):

    """
    Create managed project media path.

    Example:

    projects/project_10/media/images/photo.jpg
    """


    category = get_media_category(
        source_file
    )


    folders = {

        "image": "images",

        "video": "videos",

        "audio": "audio",

    }


    folder = folders.get(
        category,
        "other"
    )


    return (
        Path("projects")
        /
        f"project_{project_id}"
        /
        "media"
        /
        folder
        /
        Path(source_file).name
    )



def prepare_asset(
    project_id,
    source_file
):

    """
    Copy external asset into project storage.
    """


    destination = create_project_media_path(
        project_id,
        source_file
    )


    return copy_file(
        source_file,
        destination
    )
