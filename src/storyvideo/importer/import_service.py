"""
StoryVideo Import Service

Responsible for importing external media
into a project.

Responsibilities:
- accept files from UI/importers
- identify media type
- send files to Media Manager
- prepare safe project paths

Does NOT:
- manage UI
- render video
- directly manipulate widgets
"""


from pathlib import Path


from storyvideo.media.manager import (
    prepare_asset,
)


from storyvideo.media.metadata import (
    get_media_category,
)


from storyvideo.core.media import (
    add_media,
)



def import_file(
    project_id,
    scene_id,
    source_file
):
    """
    Import one media file.

    Flow:

    external file
          |
          v
    media manager
          |
          v
    project media folder
          |
          v
    database
    """


    source = Path(
        source_file
    )


    if not source.exists():

        raise FileNotFoundError(
            source_file
        )


    media_type = get_media_category(
        source_file
    )


    if media_type == "unknown":

        raise ValueError(
            f"Unsupported media: {source_file}"
        )



    managed_path = prepare_asset(
        project_id,
        source_file
    )


    add_media(
        scene_id,
        str(managed_path),
        media_type
    )


    return {
        "path": str(managed_path),
        "type": media_type,
    }



def import_files(
    project_id,
    scene_id,
    files
):
    """
    Import multiple files.
    """


    imported = []


    for file in files:

        imported.append(
            import_file(
                project_id,
                scene_id,
                file
            )
        )


    return imported
