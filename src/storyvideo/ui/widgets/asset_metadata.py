from pathlib import Path

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
)


class AssetMetadataWidget(QWidget):

    """
    Displays selected asset information.
    """

    def __init__(self):

        super().__init__()


        layout = QVBoxLayout()


        self.title = QLabel(
            "Asset Metadata"
        )


        self.info = QLabel(
            "No asset selected"
        )


        self.info.setWordWrap(
            True
        )


        layout.addWidget(
            self.title
        )


        layout.addWidget(
            self.info
        )


        self.setLayout(
            layout
        )



    def show_asset(
        self,
        asset
    ):

        if not asset:

            self.info.setText(
                "No asset selected"
            )

            return



        path = asset["path"]


        text = f"""
File:
{Path(path).name}


Type:
{asset["type"]}


Location:
{path}


Exists:
{asset["exists"]}


Scene:
{asset["scene_id"]}
"""


        self.info.setText(
            text
        )
