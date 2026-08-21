from pathlib import Path


from moviepy import (
    ImageClip,
    VideoFileClip,
    AudioFileClip,
    CompositeAudioClip,
    concatenate_videoclips,
    concatenate_audioclips,
)


from moviepy.audio.fx.AudioFadeIn import AudioFadeIn
from moviepy.audio.fx.AudioFadeOut import AudioFadeOut


from storyvideo.core.scene import get_scenes
from storyvideo.core.media import get_media

from storyvideo.audio.tracks import (
    get_audio_tracks,
)



# =================================================
# Video settings
# =================================================

VIDEO_WIDTH = 1920
VIDEO_HEIGHT = 1080



# =================================================
# Render validation
# =================================================

def validate_scenes(
    project_id
):
    """
    Validate project before rendering.

    Every scene must contain media.

    Prevents silent skipping of empty scenes.
    """


    scenes = get_scenes(
        project_id
    )


    missing = []


    for scene in scenes:

        media = get_media(
            scene[0]
        )


        if not media:

            missing.append(
                scene[0]
            )



    if missing:

        raise ValueError(
            f"Scenes without media: {missing}"
        )



# =================================================
# Prepare image
# =================================================

def prepare_image(
    path,
    duration
):

    """
    Convert image into
    standard video frame.
    """


    clip = ImageClip(
        path
    )


    clip = clip.resized(
        height=VIDEO_HEIGHT
    )


    if clip.w < VIDEO_WIDTH:

        clip = clip.resized(
            width=VIDEO_WIDTH
        )



    clip = clip.cropped(
        width=VIDEO_WIDTH,
        height=VIDEO_HEIGHT,
        x_center=clip.w / 2,
        y_center=clip.h / 2
    )


    return clip.with_duration(
        duration
    )



# =================================================
# Prepare audio
# =================================================

def prepare_audio(
    audio_file,
    duration,
    volume=1.0
):

    """
    Prepare audio track.

    Features:
    - loop short audio
    - trim long audio
    - volume control
    - fade in/out
    """


    audio = AudioFileClip(
        audio_file
    )


    clips = []

    total = 0



    while total < duration:

        clips.append(
            audio
        )

        total += audio.duration



    if len(clips) > 1:

        audio = concatenate_audioclips(
            clips
        )



    audio = audio.subclipped(
        0,
        duration
    )


    audio = audio.with_volume_scaled(
        volume
    )


    audio = audio.with_effects(
        [
            AudioFadeIn(2),
            AudioFadeOut(3),
        ]
    )


    return audio



# =================================================
# Build video timeline
# =================================================

def build_video(
    project_id
):

    """
    Create video timeline
    from project scenes.
    """


    validate_scenes(
        project_id
    )


    final_clips = []


    scenes = get_scenes(
        project_id
    )



    for scene in scenes:


        scene_clips = []


        media = get_media(
            scene[0]
        )



        for item in media:


            path = item[1]

            kind = item[2]



            if not Path(path).exists():

                raise FileNotFoundError(
                    f"Missing media file: {path}"
                )



            if kind == "image":


                clip = prepare_image(
                    path,
                    scene[2]
                )


                scene_clips.append(
                    clip
                )



            elif kind == "video":


                clip = VideoFileClip(
                    path
                )


                scene_clips.append(
                    clip
                )



        final_clips.append(
            concatenate_videoclips(
                scene_clips
            )
        )



    if not final_clips:

        return None



    return concatenate_videoclips(
        final_clips
    )



# =================================================
# Add audio
# =================================================

def add_project_audio(
    video,
    project_id
):

    """
    Mix project audio tracks.
    """


    tracks = get_audio_tracks(
        project_id
    )


    if not tracks:

        return video



    audio_tracks = []



    for track in tracks:


        if not Path(track[1]).exists():

            raise FileNotFoundError(
                f"Missing audio file: {track[1]}"
            )



        audio = prepare_audio(
            track[1],
            video.duration,
            track[3]
        )


        audio_tracks.append(
            audio
        )



    if audio_tracks:


        mixed_audio = CompositeAudioClip(
            audio_tracks
        )


        video = video.with_audio(
            mixed_audio
        )



    return video



# =================================================
# Export MP4
# =================================================

def render_project(
    project_id,
    output_file="projects/exports/video.mp4"
):

    """
    Render final MP4.
    """


    video = build_video(
        project_id
    )



    if video is None:

        print(
            "No video content"
        )

        return



    video = add_project_audio(
        video,
        project_id
    )



    output = Path(
        output_file
    )


    output.parent.mkdir(
        parents=True,
        exist_ok=True
    )



    print(
        "Rendering:",
        output
    )



    video.write_videofile(
        str(output),
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )



    print(
        "Finished:",
        output
    )