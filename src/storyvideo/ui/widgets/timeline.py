from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QInputDialog,
)


class TimelineWidget(QWidget):

    def __init__(self):

        super().__init__()

        layout = QVBoxLayout()

        self.title = QLabel(
            "Timeline"
        )

        self.list = QListWidget()

        self.edit_button = QPushButton(
            "Change Duration"
        )

        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.list
        )

        layout.addWidget(
            self.edit_button
        )

        self.setLayout(
            layout
        )


    def load_scenes(self, scenes):

        self.list.clear()

        for scene in scenes:

            self.list.addItem(
                f"{scene[0]} | "
                f"{scene[1]} | "
                f"{scene[2]} sec"
            )


    def selected_scene(self):

        item = self.list.currentItem()

        if item:

            return int(
                item.text()
                .split("|")[0]
                .strip()
            )

        return None
