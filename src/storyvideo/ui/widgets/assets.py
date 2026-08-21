from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
)


class AssetsWidget(QWidget):

    """
    Project asset browser.

    Displays:
    - Images
    - Videos
    - Audio files
    """

    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Project Assets"
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


    def load_assets(
        self,
        assets
    ):

        self.list.clear()


        for item in assets:

            self.list.addItem(
                f"{item[2]} : {item[1]}"
            )
