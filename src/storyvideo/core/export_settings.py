from storyvideo.core.database import get_connection



def create_export_settings(
    project_id
):

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO export_settings
        (project_id)

        VALUES (?)
        """,

        (
            project_id,
        )
    )


    conn.commit()

    conn.close()



def get_export_settings(
    project_id
):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT
        resolution,
        fps,
        quality

        FROM export_settings

        WHERE project_id=?
        """,

        (
            project_id,
        )
    ).fetchone()


    conn.close()


    return row