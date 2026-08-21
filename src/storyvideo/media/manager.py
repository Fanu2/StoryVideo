"""
Media Manager Layer

Business logic for project media.

Future responsibilities:

- import assets
- duplicate detection
- project portability
- asset validation
- asset lifecycle management

This layer sits between UI/importers
and filesystem/database.
"""


from pathlib import Path

from .storage import (
    copy_file,
)

from .metadata import (
    get_media_category,
)



def create_project_media_path(
    project_name,
    source_file
):

    """
    Calculate managed project path.
    """


    category = get_media_category(
        source_file
    )


    folder_map = {

        "image": "images",

        "video": "videos",

        "audio": "audio",

    }


    folder = folder_map.get(
        category,
        "other"
    )


    return (
        Path("projects")
        /
        project_name
        /
        "media"
        /
        folder
        /
        Path(source_file).name
    )



def prepare_asset(
    project_name,
    source_file
):

    """
    Prepare media asset.

    Does not touch database yet.
    """


    destination = create_project_media_path(
        project_name,
        source_file
    )


    return copy_file(
        source_file,
        destination
    )
