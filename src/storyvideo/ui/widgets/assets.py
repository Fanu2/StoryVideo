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
)

from PySide6.QtGui import (
    QIcon,
    QPixmap,
)


class AssetsWidget(QWidget):

    """
    Project asset browser.

    Features:
    - Thumbnail grid
    - Search
    - Type filter
    - Asset selection signal

    Receives data from Asset Service only.
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


        self.list = QListWidget()


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

        """
        Receive assets from Asset Service.
        """

        self.assets = assets

        self.apply_filter()



    def apply_filter(self):

        """
        Filter assets without touching service layer.
        """

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

        filename = Path(
            path
        ).name


        item.setText(
            f"{asset['type'].upper()} : {filename}"
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
