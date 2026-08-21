from .database import get_connection


def add_media(scene_id, file_path, media_type):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO media
        (scene_id, file_path, media_type)
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


def get_media(scene_id):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, file_path, media_type
        FROM media
        WHERE scene_id=?
        """,
        (scene_id,)
    ).fetchall()

    conn.close()

    return rows


def get_project_media(project_id):

    """
    Get all media belonging to a project.

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
