from .database import get_connection


def create_scene(project_id, title, duration=5):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO scenes
        (project_id, title, duration)
        VALUES (?, ?, ?)
        """,
        (
            project_id,
            title,
            duration
        )
    )

    conn.commit()
    conn.close()


def get_scenes(project_id):

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT id, title, duration
        FROM scenes
        WHERE project_id=?
        ORDER BY id
        """,
        (project_id,)
    ).fetchall()

    conn.close()

    return rows


def update_scene_duration(scene_id, duration):

    conn = get_connection()

    conn.execute(
        """
        UPDATE scenes
        SET duration=?
        WHERE id=?
        """,
        (
            duration,
            scene_id
        )
    )

    conn.commit()
    conn.close()


def delete_scene(scene_id):

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM scenes
        WHERE id=?
        """,
        (scene_id,)
    )

    conn.commit()
    conn.close()
