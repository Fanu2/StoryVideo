from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
)

from PySide6.QtCore import Signal



class TimelineListWidget(QListWidget):

    """
    Timeline drop target.

    Accepts asset paths from Asset Browser.
    """


    asset_dropped = Signal(str)



    def __init__(self):

        super().__init__()


        self.setAcceptDrops(
            True
        )


        # Do not use DropOnly mode.
        # It interferes with custom mime drops.


        self.viewport().setAcceptDrops(
            True
        )



    def dragEnterEvent(
        self,
        event
    ):

        print(
            "TIMELINE DRAG ENTER"
        )


        if event.mimeData().hasText():

            event.accept()



    def dragMoveEvent(
        self,
        event
    ):

        if event.mimeData().hasText():

            event.accept()



    def dropEvent(
        self,
        event
    ):

        print(
            "TIMELINE DROP",
            event.mimeData().text()
        )


        if not event.mimeData().hasText():

            return


        self.asset_dropped.emit(
            event.mimeData().text()
        )


        event.accept()



class TimelineWidget(QWidget):

    """
    Timeline scene browser.
    """


    asset_dropped = Signal(
        int,
        str
    )



    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Timeline"
        )


        self.list = TimelineListWidget()


        self.list.asset_dropped.connect(
            self.handle_drop
        )


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



    def load_scenes(
        self,
        scenes
    ):

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



    def handle_drop(
        self,
        path
    ):

        scene_id = self.selected_scene()


        if scene_id:

            self.asset_dropped.emit(
                scene_id,
                path
            )