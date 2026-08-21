from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QPushButton,
    QHBoxLayout,
)

from PySide6.QtCore import Signal

from PySide6.QtGui import QPixmap



class PreviewWidget(QWidget):

    """
    Scene media preview.

    Responsibilities:
    - Display images attached to selected scene
    - Navigate between scene images
    - Show media information
    - Request image removal

    Does not:
    - access database
    - manage scenes
    - delete files
    - render video
    """


    # Sends selected media database id
    # to MainWindow for removal

    media_remove_requested = Signal(int)



    def __init__(self):

        super().__init__()


        # Current scene images

        self.images = []


        # Database ids matching images

        self.media_ids = []


        # Current image position

        self.current_index = 0



        layout = QVBoxLayout()



        # Scene media information

        self.info = QLabel(
            "No scene selected"
        )



        # Current image position

        self.counter = QLabel(
            ""
        )



        # Image display area

        self.label = QLabel(
            "Preview"
        )


        self.label.setMinimumHeight(
            300
        )


        self.label.setScaledContents(
            True
        )



        # Navigation controls

        buttons = QHBoxLayout()



        self.previous = QPushButton(
            "Previous"
        )


        self.next = QPushButton(
            "Next"
        )


        self.remove = QPushButton(
            "Remove Image"
        )



        self.previous.clicked.connect(
            self.show_previous
        )


        self.next.clicked.connect(
            self.show_next
        )


        self.remove.clicked.connect(
            self.remove_current_image
        )



        buttons.addWidget(
            self.previous
        )


        buttons.addWidget(
            self.next
        )


        buttons.addWidget(
            self.remove
        )



        layout.addWidget(
            self.info
        )


        layout.addWidget(
            self.counter
        )


        layout.addWidget(
            self.label
        )


        layout.addLayout(
            buttons
        )


        self.setLayout(
            layout
        )



    def set_images(
        self,
        images,
        media_ids
    ):

        """
        Receive scene image paths
        and matching database ids.
        """


        self.images = images


        self.media_ids = media_ids


        self.current_index = 0


        self.update_preview()



    def update_preview(
        self
    ):

        """
        Display current image.
        """


        if not self.images:

            self.label.setText(
                "No image"
            )


            self.counter.setText(
                ""
            )


            return



        path = self.images[
            self.current_index
        ]


        pixmap = QPixmap(
            path
        )


        if not pixmap.isNull():

            self.label.setPixmap(
                pixmap
            )



        self.counter.setText(
            f"Image {self.current_index + 1} / {len(self.images)}"
        )



    def show_previous(
        self
    ):

        """
        Move to previous image.
        """


        if not self.images:

            return



        self.current_index -= 1


        if self.current_index < 0:

            self.current_index = len(
                self.images
            ) - 1



        self.update_preview()



    def show_next(
        self
    ):

        """
        Move to next image.
        """


        if not self.images:

            return



        self.current_index += 1


        if self.current_index >= len(
            self.images
        ):

            self.current_index = 0



        self.update_preview()



    def remove_current_image(
        self
    ):

        """
        Request removal of current image.

        MainWindow handles database removal.
        """


        if not self.media_ids:

            return



        media_id = self.media_ids[
            self.current_index
        ]


        self.media_remove_requested.emit(
            media_id
        )



    def show_scene_info(
        self,
        count
    ):

        """
        Display scene image count.
        """


        if count == 0:

            self.info.setText(
                "Scene Media: none"
            )


        elif count == 1:

            self.info.setText(
                "Scene Media: 1 image"
            )


        else:

            self.info.setText(
                f"Scene Media: {count} images"
            )