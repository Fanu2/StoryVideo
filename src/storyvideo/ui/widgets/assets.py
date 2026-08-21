from pathlib import Path


from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
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

    Displays:
    - Images
    - Videos
    - Audio files

    Receives data from Asset Service only.
    """


    asset_selected = Signal(dict)



    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Project Assets"
        )


        self.list = QListWidget()


        # Better thumbnail view

        self.list.setIconSize(
            QSize(
                96,
                96
            )
        )


        # Thumbnail grid mode

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
        Load assets from Asset Service.
        """


        self.list.clear()


        self.assets = assets



        for asset in assets:


            item = QListWidgetItem()


            path = asset["path"]


            filename = Path(
                path
            ).name



            item.setText(
                f"{asset['type'].upper()} : {filename}"
            )



            # Image thumbnail

            if (
                asset["type"] == "image"
                and Path(path).exists()
            ):

                pixmap = QPixmap(
                    path
                )


                if not pixmap.isNull():

                    thumbnail = pixmap.scaled(
                        96,
                        96
                    )


                    item.setIcon(
                        QIcon(
                            thumbnail
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

        """
        Emit selected asset.
        """


        asset = item.data(
            1000
        )


        if asset:

            self.asset_selected.emit(
                asset
            )
