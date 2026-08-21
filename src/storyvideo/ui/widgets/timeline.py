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

    Responsibilities:
    - Accept dragged asset paths
    - Emit dropped path

    Does not:
    - access database
    - call services
    - modify projects
    """


    asset_dropped = Signal(str)



    def __init__(self):

        super().__init__()


        # Enable custom asset drops

        self.setAcceptDrops(
            True
        )


        # Required because QListWidget
        # receives events through viewport

        self.viewport().setAcceptDrops(
            True
        )



    def dragEnterEvent(
        self,
        event
    ):

        # Accept only asset paths

        if event.mimeData().hasText():

            event.accept()



    def dragMoveEvent(
        self,
        event
    ):

        # Continue accepting valid drags

        if event.mimeData().hasText():

            event.accept()



    def dropEvent(
        self,
        event
    ):

        """
        Receive dropped asset.

        Only emits the path.
        MainWindow handles the action.
        """


        if not event.mimeData().hasText():

            return


        self.asset_dropped.emit(
            event.mimeData().text()
        )


        event.accept()



class TimelineWidget(QWidget):

    """
    Simple scene browser.

    Provides:
    - scene list
    - selected scene lookup
    - asset drop signal
    - media count visibility
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


        # Custom list widget
        # handles asset drops

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
        scenes,
        media_counts=None
    ):

        """
        Load project scenes.

        media_counts example:

        {
            12: 2,
            26: 1
        }

        Shows attached image count
        without changing scene model.
        """


        self.list.clear()



        for scene in scenes:


            scene_id = scene[0]


            text = (
                f"{scene_id} | "
                f"{scene[1]} | "
                f"{scene[2]} sec"
            )


            count = 0


            if media_counts:

                count = media_counts.get(
                    scene_id,
                    0
                )



            if count:


                text += (
                    f" | {count} image"
                    if count == 1
                    else f" | {count} images"
                )



            self.list.addItem(
                text
            )



    def selected_scene(self):

        """
        Return selected scene id.
        """


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

        """
        Convert dropped path into
        scene asset event.
        """


        scene_id = self.selected_scene()


        if scene_id:

            self.asset_dropped.emit(
                scene_id,
                path
            )