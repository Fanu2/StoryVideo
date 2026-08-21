import sqlite3
from pathlib import Path


DB_PATH = (
    Path.home()
    /
    ".storyvideo"
    /
    "storyvideo.db"
)


def get_connection():

    DB_PATH.parent.mkdir(
        exist_ok=True
    )


    conn = sqlite3.connect(
        DB_PATH
    )


    # Projects
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL
        )
        """
    )


    # Scenes
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS scenes (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            project_id INTEGER NOT NULL,

            title TEXT NOT NULL,

            duration INTEGER DEFAULT 5,

            FOREIGN KEY(project_id)
            REFERENCES projects(id)
        )
        """
    )


    # Media attached to scenes
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS media (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            scene_id INTEGER NOT NULL,

            file_path TEXT NOT NULL,

            media_type TEXT NOT NULL,

            FOREIGN KEY(scene_id)
            REFERENCES scenes(id)
        )
        """
    )


    # NEW:
    # Project level audio tracks
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audio_tracks (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            project_id INTEGER NOT NULL,

            file_path TEXT NOT NULL,

            track_type TEXT DEFAULT 'music',

            volume REAL DEFAULT 1.0,

            FOREIGN KEY(project_id)
            REFERENCES projects(id)
        )
        """
    )


    # NEW:
    # Rendering preferences
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS export_settings (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            project_id INTEGER NOT NULL,

            resolution TEXT DEFAULT '1920x1080',

            fps INTEGER DEFAULT 24,

            quality TEXT DEFAULT 'high',

            FOREIGN KEY(project_id)
            REFERENCES projects(id)
        )
        """
    )


    conn.commit()


    return conn