from .database import get_connection



def add_media(
    scene_id,
    file_path,
    media_type
):
    """
    Attach media to a scene.
    """


    conn = get_connection()


    conn.execute(
        """
        INSERT INTO media
        (
            scene_id,
            file_path,
            media_type
        )
        VALUES (?, ?, ?)
        """,
        (
            scene_id,
            file_path,
            media_type
        )
    )


    conn.commit()

    conn.close()



def get_media(
    scene_id
):
    """
    Get media attached to a scene.

    Returns ordered media:
    id,
    file_path,
    media_type
    """


    conn = get_connection()


    rows = conn.execute(
        """
        SELECT
            id,
            file_path,
            media_type

        FROM media

        WHERE scene_id=?

        ORDER BY id
        """,
        (
            scene_id,
        )
    ).fetchall()


    conn.close()


    return rows



def get_project_media(
    project_id
):
    """
    Get all media belonging
    to a project.

    Returns:
    id,
    file_path,
    media_type
    """


    conn = get_connection()


    rows = conn.execute(
        """
        SELECT
            media.id,
            media.file_path,
            media.media_type

        FROM media

        JOIN scenes
        ON media.scene_id = scenes.id

        WHERE scenes.project_id=?

        ORDER BY media.id
        """,
        (
            project_id,
        )
    ).fetchall()


    conn.close()


    return rows



def media_exists(
    scene_id,
    file_path
):
    """
    Check whether media is already
    attached to a scene.
    """


    conn = get_connection()


    row = conn.execute(
        """
        SELECT id

        FROM media

        WHERE scene_id=?
        AND file_path=?
        """,
        (
            scene_id,
            file_path
        )
    ).fetchone()


    conn.close()


    return row is not None



def remove_media(
    media_id
):
    """
    Remove media relationship.

    Only removes the database entry.
    Original file remains untouched.
    """


    conn = get_connection()


    conn.execute(
        """
        DELETE FROM media

        WHERE id=?
        """,
        (
            media_id,
        )
    )


    conn.commit()

    conn.close()