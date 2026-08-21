from pathlib import Path


from storyvideo.core.media import (
    add_media,
    media_exists,
)



class MediaDropService:

    """
    Handles adding assets into scenes.

    Responsibilities:
    - validate asset path
    - prevent duplicate scene media
    - create media relationship

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



        # Validate file exists

        if not Path(path).exists():

            raise FileNotFoundError(
                path
            )



        # Prevent duplicate attachment

        if media_exists(
            scene_id,
            path
        ):

            return {
                "scene_id": scene_id,
                "path": path,
                "type": media_type,
                "status": "already_exists",
            }



        # Create scene-media relationship

        add_media(
            scene_id,
            path,
            media_type
        )



        return {
            "scene_id": scene_id,
            "path": path,
            "type": media_type,
            "status": "added",
        }