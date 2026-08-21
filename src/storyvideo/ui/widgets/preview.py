from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)

from PySide6.QtGui import QPixmap


class PreviewWidget(QWidget):

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.label = QLabel(
            "Preview"
        )

        self.label.setMinimumHeight(
            300
        )

        self.label.setScaledContents(
            True
        )

        layout.addWidget(
            self.label
        )

        self.setLayout(
            layout
        )


    def show_image(self, path):

        pixmap = QPixmap(path)

        if not pixmap.isNull():
            self.label.setPixmap(
                pixmap
            )
