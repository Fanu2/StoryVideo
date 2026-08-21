from pathlib import Path


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QComboBox,
)


from PySide6.QtCore import (
    Signal,
    QSize,
    QMimeData,
    Qt,
    QPoint,
)


from PySide6.QtGui import (
    QIcon,
    QPixmap,
    QDrag,
)



class AssetListWidget(QListWidget):

    """
    Custom asset browser list.

    Responsibilities:
    - start drag operation
    - send asset path

    Does not access:
    - database
    - services
    """


    def __init__(self):

        super().__init__()

        self.drag_start_position = QPoint()



    def mousePressEvent(
        self,
        event
    ):

        if event.button() == Qt.LeftButton:

            self.drag_start_position = event.position().toPoint()


        super().mousePressEvent(
            event
        )



    def mouseMoveEvent(
        self,
        event
    ):

        if not (
            event.buttons()
            &
            Qt.LeftButton
        ):

            return


        if (
            event.position().toPoint()
            -
            self.drag_start_position
        ).manhattanLength() < 10:

            return



        item = self.currentItem()


        if not item:

            return



        asset = item.data(
            1000
        )


        if not asset:

            return



        mime = QMimeData()


        mime.setText(
            asset["path"]
        )



        drag = QDrag(
            self
        )


        drag.setMimeData(
            mime
        )


        drag.exec(
            Qt.CopyAction
        )



        super().mouseMoveEvent(
            event
        )




class AssetsWidget(QWidget):

    """
    Project asset browser.

    Features:
    - thumbnail grid
    - search
    - type filter
    - selection signal
    - drag source
    """


    asset_selected = Signal(dict)



    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()



        self.title = QLabel(
            "Project Assets"
        )



        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search assets..."
        )



        self.filter = QComboBox()

        self.filter.addItems(
            [
                "All",
                "Images",
                "Videos",
                "Audio",
            ]
        )



        self.search.textChanged.connect(
            self.apply_filter
        )


        self.filter.currentTextChanged.connect(
            self.apply_filter
        )



        self.list = AssetListWidget()



        self.list.setDragEnabled(
            True
        )


        self.list.setDragDropMode(
            QListWidget.DragOnly
        )



        self.list.setIconSize(
            QSize(
                96,
                96
            )
        )


        self.list.setViewMode(
            QListWidget.IconMode
        )


        self.list.setResizeMode(
            QListWidget.Adjust
        )


        self.list.setMovement(
            QListWidget.Static
        )


        self.list.setSpacing(
            12
        )


        self.list.setGridSize(
            QSize(
                140,
                140
            )
        )


        self.list.itemClicked.connect(
            self.select_asset
        )



        layout.addWidget(
            self.title
        )

        layout.addWidget(
            self.search
        )

        layout.addWidget(
            self.filter
        )

        layout.addWidget(
            self.list
        )


        self.setLayout(
            layout
        )


        self.assets = []



    def load_assets(
        self,
        assets
    ):

        self.assets = assets

        self.apply_filter()



    def apply_filter(self):

        self.list.clear()


        text = self.search.text().lower()

        selected = self.filter.currentText()



        for asset in self.assets:


            filename = Path(
                asset["path"]
            ).name.lower()



            if text and text not in filename:

                continue



            if selected == "Images" and asset["type"] != "image":

                continue


            if selected == "Videos" and asset["type"] != "video":

                continue


            if selected == "Audio" and asset["type"] != "audio":

                continue



            self.add_asset_item(
                asset
            )



    def add_asset_item(
        self,
        asset
    ):

        item = QListWidgetItem()


        path = asset["path"]


        item.setText(
            f"{asset['type'].upper()} : {Path(path).name}"
        )



        if (
            asset["type"] == "image"
            and Path(path).exists()
        ):

            pixmap = QPixmap(
                path
            )


            if not pixmap.isNull():

                item.setIcon(
                    QIcon(
                        pixmap.scaled(
                            96,
                            96
                        )
                    )
                )



        item.setData(
            1000,
            asset
        )


        self.list.addItem(
            item
        )



    def select_asset(
        self,
        item
    ):

        asset = item.data(
            1000
        )


        if asset:

            self.asset_selected.emit(
                asset
            )