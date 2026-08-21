from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
)


class AudioTracksWidget(QWidget):
    """
    Displays project-level audio tracks.
    """

    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Project Audio"
        )


        self.list = QListWidget()


        layout.addWidget(
            self.title
        )


        layout.addWidget(
            self.list
        )


        self.setLayout(
            layout
        )


    def load_tracks(
        self,
        tracks
    ):

        self.list.clear()


        for track in tracks:

            self.list.addItem(
                f"{track[2]} : {track[1]}"
            )