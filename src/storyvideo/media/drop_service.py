from pathlib import Path


from storyvideo.core.media import (
    add_media,
)



class MediaDropService:

    """
    Handles adding assets into scenes.

    UI should not call database functions directly.
    """


    def add_asset_to_scene(
        self,
        scene_id,
        asset
    ):

        """
        Attach an existing asset to a scene.
        """


        path = asset["path"]

        media_type = asset["type"]


        if not Path(path).exists():

            raise FileNotFoundError(
                path
            )


        add_media(
            scene_id,
            path,
            media_type
        )


        return {
            "scene_id": scene_id,
            "path": path,
            "type": media_type,
        }
