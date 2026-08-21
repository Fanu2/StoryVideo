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
    - Provide visual drag feedback

    Does not:
    - access database
    - call services
    - modify projects
    """


    asset_dropped = Signal(str)



    def __init__(self):

        super().__init__()


        # Enable custom drops

        self.setAcceptDrops(
            True
        )


        # QListWidget receives
        # events through viewport

        self.viewport().setAcceptDrops(
            True
        )



    def dragEnterEvent(
        self,
        event
    ):

        if event.mimeData().hasText():

            self.setStyleSheet(
                "border: 2px solid green;"
            )

            event.accept()



    def dragMoveEvent(
        self,
        event
    ):

        if event.mimeData().hasText():

            event.accept()



    def dragLeaveEvent(
        self,
        event
    ):

        self.setStyleSheet(
            ""
        )



    def dropEvent(
        self,
        event
    ):

        if not event.mimeData().hasText():

            return


        self.setStyleSheet(
            ""
        )


        self.asset_dropped.emit(
            event.mimeData().text()
        )


        event.accept()





class TimelineWidget(QWidget):

    """
    Simple story timeline.

    Provides:
    - scene list
    - media visibility
    - empty scene warning
    - drag/drop support
    - selected scene lookup
    - scene information display

    Future:
    - thumbnail support

    Does not:
    - access database
    - modify projects
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


        self.status = QLabel(
            "Select a scene"
        )


        # UI-only scene cache
        # Future thumbnail support

        self.scene_data = {}



        self.list = TimelineListWidget()



        self.list.asset_dropped.connect(
            self.handle_drop
        )


        self.list.currentItemChanged.connect(
            self.update_selection_info
        )



        self.edit_button = QPushButton(
            "Change Duration"
        )



        layout.addWidget(
            self.title
        )


        layout.addWidget(
            self.status
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
        Load scenes into timeline.

        media_counts example:

        {
            12: 5,
            26: 1
        }

        No database access.
        """


        self.list.clear()

        self.scene_data.clear()



        for scene in scenes:


            scene_id = scene[0]


            self.scene_data[scene_id] = {
                "name": scene[1],
                "duration": scene[2],
            }



            count = 0


            if media_counts:

                count = media_counts.get(
                    scene_id,
                    0
                )



            text = (
                f"{scene_id} | "
                f"{scene[1]} | "
                f"Duration: {scene[2]} sec"
            )



            if count == 0:

                text += (
                    " | ⚠ No media"
                )


            elif count == 1:

                text += (
                    " | 🖼 1 image"
                )


            else:

                text += (
                    f" | 🖼 {count} images"
                )



            self.list.addItem(
                text
            )



    def update_selection_info(
        self,
        current,
        previous
    ):

        """
        Show selected scene summary.
        """


        if not current:

            self.status.setText(
                "Select a scene"
            )

            return



        scene_id = int(
            current.text()
            .split("|")[0]
            .strip()
        )


        data = self.scene_data.get(
            scene_id,
            {}
        )


        self.status.setText(
            f"Scene {scene_id} | "
            f"{data.get('name', '')} | "
            f"{data.get('duration', 0)} sec"
        )



    def selected_scene(
        self
    ):

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
        Convert dropped path
        into scene asset event.
        """


        scene_id = self.selected_scene()



        if scene_id:

            self.asset_dropped.emit(
                scene_id,
                path
            )