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