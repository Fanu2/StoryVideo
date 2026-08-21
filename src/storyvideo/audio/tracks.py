from storyvideo.core.database import get_connection



def add_audio_track(
    project_id,
    file_path,
    track_type="music",
    volume=1.0
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO audio_tracks
        (
            project_id,
            file_path,
            track_type,
            volume
        )

        VALUES (?, ?, ?, ?)
        """,

        (
            project_id,
            file_path,
            track_type,
            volume
        )
    )


    conn.commit()

    conn.close()



def get_audio_tracks(project_id):

    conn = get_connection()


    rows = conn.execute(
        """
        SELECT
        id,
        file_path,
        track_type,
        volume

        FROM audio_tracks

        WHERE project_id=?
        """,

        (
            project_id,
        )
    ).fetchall()


    conn.close()


    return rows