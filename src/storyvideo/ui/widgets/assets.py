from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
)

from PySide6.QtCore import Signal


class AssetsWidget(QWidget):

    """
    Project asset browser.

    Displays:
    - Images
    - Videos
    - Audio files

    Does not access database directly.
    """

    asset_selected = Signal(dict)



    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Project Assets"
        )


        self.list = QListWidget()


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
        Load asset data from Asset Service.
        """


        self.list.clear()


        self.assets = assets


        for asset in assets:


            item = QListWidgetItem()


            filename = (
                asset["path"]
                .split("/")[-1]
            )


            item.setText(
                f"{asset['type'].upper()} : {filename}"
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
