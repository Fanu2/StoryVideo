from storyvideo.core.database import get_connection


def project_exists(project_id):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT id
        FROM projects
        WHERE id=?
        """,
        (project_id,)
    ).fetchone()

    conn.close()

    return row is not None



def get_project(project_id):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT id,name
        FROM projects
        WHERE id=?
        """,
        (project_id,)
    ).fetchone()

    conn.close()

    return row