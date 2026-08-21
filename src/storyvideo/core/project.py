from .database import get_connection



def create_project(name):

    conn = get_connection()


    conn.execute(
        "INSERT INTO projects (name) VALUES (?)",
        (name,)
    )


    conn.commit()

    conn.close()



def get_projects():

    conn = get_connection()


    rows = conn.execute(
        """
        SELECT id, name
        FROM projects
        ORDER BY id DESC
        """
    ).fetchall()


    conn.close()


    return rows

def get_project_name(project_id):

    """
    Return project name from project id.
    """

    conn = get_connection()


    row = conn.execute(
        """
        SELECT name
        FROM projects
        WHERE id=?
        """,
        (
            project_id,
        )
    ).fetchone()


    conn.close()


    if row:

        return row[0]


    return None
