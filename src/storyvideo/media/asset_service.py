"""
Asset Service

Provides project assets for UI
and future features.

No Qt dependency.
No rendering dependency.
"""


from pathlib import Path

from storyvideo.core.scene import get_scenes
from storyvideo.core.media import get_media



def get_project_assets(project_id):

    """
    Return all assets belonging to a project.

    Output format:

    {
        id,
        scene_id,
        path,
        type,
        exists
    }
    """


    assets = []


    scenes = get_scenes(
        project_id
    )


    for scene in scenes:


        media_items = get_media(
            scene[0]
        )


        for item in media_items:


            assets.append(
                {
                    "id": item[0],
                    "scene_id": scene[0],
                    "path": item[1],
                    "type": item[2],
                    "exists": Path(item[1]).exists(),
                }
            )


    return assets
