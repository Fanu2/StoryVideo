from pathlib import Path

from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QInputDialog,
    QFileDialog,
    QSplitter,
    QMessageBox,
)

from PySide6.QtCore import Qt


# Core
from storyvideo.core.project import (
    create_project,
    get_projects,
)

from storyvideo.core.scene import (
    create_scene,
    get_scenes,
    update_scene_duration,
)

from storyvideo.core.media import (
    add_media,
    get_media,
    get_project_media,
)

from storyvideo.audio.tracks import (
    add_audio_track,
    get_audio_tracks,
)

from storyvideo.importer.folder_importer import (
    scan_folder,
)


from storyvideo.importer.import_service import (
    import_file,
    import_files,
)

from storyvideo.renderer.moviepy_renderer import (
    render_project,
)


from storyvideo.media.drop_service import (
    MediaDropService,
)


# Widgets
from storyvideo.ui.widgets.timeline import (
    TimelineWidget,
)

from storyvideo.ui.widgets.preview import (
    PreviewWidget,
)

from storyvideo.ui.widgets.audio_tracks import (
    AudioTracksWidget,
)


from storyvideo.ui.widgets.assets import (
    AssetsWidget,
)


from storyvideo.ui.widgets.asset_metadata import (
    AssetMetadataWidget,
)


from storyvideo.media.asset_service import (
    get_project_assets,
)


from storyvideo.ui.widgets.assets import (
    AssetsWidget,
)


from storyvideo.ui.widgets.asset_metadata import (
    AssetMetadataWidget,
)


class MainWindow(QMainWindow):

    """
    Main StoryVideo editor window.
    """


    def __init__(self):

        super().__init__()

        self.setWindowTitle(
            "StoryVideo"
        )

        self.resize(
            1200,
            850
        )


        self.current_project = None
        self.current_scene = None


        self.drop_service = MediaDropService()

        self.project_modified = False
        self.project_name = None


        container = QWidget()

        layout = QVBoxLayout()


        # Timeline

        self.timeline = TimelineWidget()

        self.timeline.list.itemClicked.connect(
            self.select_scene
        )

        self.timeline.edit_button.clicked.connect(
            self.edit_duration
        )


        self.timeline.asset_dropped.connect(
            self.handle_asset_drop
        )


        # Preview

        self.preview = PreviewWidget()

        self.preview.media_remove_requested.connect(
            self.remove_scene_media
        )


        # Project Audio

        self.audio_tracks = AudioTracksWidget()


        # Project Assets Browser

        self.assets = AssetsWidget()


        self.metadata = AssetMetadataWidget()


        self.assets.asset_selected.connect(
            self.metadata.show_asset
        )


        # Main editor splitter

        splitter = QSplitter(
            Qt.Vertical
        )


        # Timeline

        splitter.addWidget(
            self.timeline
        )


        # Preview + Assets workspace

        workspace = QSplitter(
            Qt.Horizontal
        )


        workspace.addWidget(
            self.preview
        )


        workspace.addWidget(
            self.assets
        )


        workspace.addWidget(
            self.metadata
        )


        workspace.setSizes(
            [
                650,
                300,
                220
            ]
        )


        splitter.addWidget(
            workspace
        )


        # Audio tracks

        splitter.addWidget(
            self.audio_tracks
        )


        splitter.setSizes(
            [
                200,
                450,
                180
            ]
        )


        # Toolbar

        toolbar = QHBoxLayout()


        buttons = [
            (
                "Create Project",
                self.new_project
            ),
            (
                "Add Scene",
                self.new_scene
            ),
            (
                "Add Media Files",
                self.import_files
            ),
            (
                "Import Folder",
                self.import_folder
            ),
            (
                "Add Project Audio",
                self.add_project_audio
            ),
            (
                "Render MP4",
                self.render_video
            ),
        ]


        for text, action in buttons:

            btn = QPushButton(
                text
            )

            btn.clicked.connect(
                action
            )

            toolbar.addWidget(
                btn
            )


        layout.addWidget(
            splitter
        )

        layout.addLayout(
            toolbar
        )


        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )

        self.create_menu()

        self.statusBar().showMessage(
            "No project loaded"
        )



    def create_menu(self):

        menu = self.menuBar()


        file_menu = menu.addMenu(
            "File"
        )


        file_menu.addAction(
            "New Project",
            self.new_project
        )


        file_menu.addAction(
            "Open Project",
            self.open_project
        )


        file_menu.addAction(
            "Save Project",
            self.save_project
        )


        file_menu.addAction(
            "Close Project",
            self.close_project
        )


        file_menu.addAction(
            "Exit",
            self.close
        )


        media_menu = menu.addMenu(
            "Media"
        )


        media_menu.addAction(
            "Add Media Files",
            self.import_files
        )


        media_menu.addAction(
            "Import Media Folder",
            self.import_folder
        )


        media_menu.addAction(
            "Add Project Audio",
            self.add_project_audio
        )



    def open_project(self):

        projects = get_projects()


        if not projects:

            QMessageBox.information(
                self,
                "Open Project",
                "No projects found"
            )

            return


        choices = []


        for project in projects:

            pid = project[0]
            name = project[1]


            media_count = len(
                get_project_media(pid)
            )


            choices.append(
                f"{pid} - {name} ({media_count} assets)"
            )



        choice, ok = QInputDialog.getItem(
            self,
            "Open Project",
            "Select Project:",
            choices,
            0,
            False
        )


        if ok:

            index = choices.index(
                choice
            )


            self.current_project = (
                projects[index][0]
            )


            self.current_scene = None


            self.project_modified = False


            self.refresh()


            self.statusBar().showMessage(
                f"Opened {choice}"
            )


    def save_project(self):

        self.project_modified = False

        self.statusBar().showMessage(
            "Project saved"
        )


    def close_project(self):

        if self.project_modified:

            answer = QMessageBox.question(
                self,
                "Close Project",
                "Save changes before closing?"
            )

            if answer == QMessageBox.Cancel:
                return


        self.current_project = None
        self.current_scene = None




        # Clear timeline

        self.timeline.list.clear()


        # Clear assets

        self.assets.list.clear()

        self.assets.assets = []


        # Clear metadata

        self.metadata.show_asset(
            None
        )


        # Clear preview

        self.preview.label.clear()

        self.preview.label.setText(
            "Preview"
        )


        # Clear audio

        self.audio_tracks.list.clear()


        self.statusBar().showMessage(
            "No project loaded"
        )


    def new_project(self):

        name, ok = QInputDialog.getText(
            self,
            "Project",
            "Name:"
        )


        if ok and name:

            create_project(
                name
            )

            self.current_project = (
                get_projects()[-1][0]
            )

            self.refresh()



    def new_scene(self):

        if not self.current_project:
            return


        title, ok = QInputDialog.getText(
            self,
            "Scene",
            "Title:"
        )


        if ok and title:

            create_scene(
                self.current_project,
                title
            )

            scenes = get_scenes(
                self.current_project
            )

            self.current_scene = scenes[-1][0]

            self.refresh()



    def import_files(self):

        if not self.current_scene:
            return


        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Media"
        )


        for file in files:

            ext = Path(file).suffix.lower()


            if ext in [
                ".jpg",
                ".jpeg",
                ".png",
                ".webp"
            ]:

                kind = "image"


            elif ext in [
                ".mp4",
                ".mkv",
                ".avi",
                ".mov"
            ]:

                kind = "video"


            else:

                continue


            import_file(
                self.current_project,
                self.current_scene,
                file
            )


        self.refresh()



    def import_folder(self):

        if not self.current_scene:
            return


        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Media Folder",
            str(Path.home() / "Downloads")
        )


        if folder:

            for file, kind in scan_folder(folder):

                import_file(
                    self.current_project,
                    self.current_scene,
                    file
                )


        self.refresh()



    def add_project_audio(self):

        if not self.current_project:
            return


        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Audio",
            "",
            "Audio (*.mp3 *.wav *.ogg)"
        )


        for file in files:

            add_audio_track(
                self.current_project,
                file,
                "music",
                1.0
            )


        self.refresh()



    # -----------------------------
    # Render video
    # -----------------------------

    def render_video(self):

        if not self.current_project:

            return


        output_file, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video",
            "video.mp4",
            "MP4 Video (*.mp4)"
        )


        if output_file:


            if not output_file.endswith(
                ".mp4"
            ):

                output_file += ".mp4"



            try:

                render_project(
                    self.current_project,
                    output_file
                )


            except Exception as e:

                QMessageBox.critical(
                    self,
                    "Render Error",
                    str(e)
                )

    def select_scene(
        self,
        item
    ):

        """
        Handle timeline scene selection.

        Loads all images attached to
        the selected scene into preview.

        Preview receives:
        - image paths
        - database media ids
        """


        scene_id = (
            item.text()
            .split("|")[0]
            .strip()
        )


        media_items = get_media(
            scene_id
        )



        # Extract image paths

        images = [
            media[1]
            for media in media_items
            if media[2] == "image"
        ]



        # Extract matching database ids

        media_ids = [
            media[0]
            for media in media_items
            if media[2] == "image"
        ]



        # Update preview information

        self.preview.show_scene_info(
            len(images)
        )



        # Load images and ids

        self.preview.set_images(
            images,
            media_ids
        )


    def remove_scene_media(
        self,
        media_id
    ):

        """
        Remove media assignment.

        Does not delete file.
        Only removes scene link.
        """


        from storyvideo.core.media import (
            remove_media,
        )


        remove_media(
            media_id
        )


        self.refresh()

    def edit_duration(self):

        scene_id = (
            self.timeline.selected_scene()
        )


        if scene_id:

            value, ok = QInputDialog.getInt(
                self,
                "Duration",
                "Seconds:",
                5
            )


            if ok:

                update_scene_duration(
                    scene_id,
                    value
                )

                self.refresh()



    def preview_asset(
        self,
        asset
    ):

        """
        Preview selected asset.
        """


        if asset["type"] == "image":

            self.preview.show_image(
                asset["path"]
            )


    def handle_asset_drop(
        self,
        scene_id,
        path
    ):

        asset = {
            "path": path,
            "type": Path(path).suffix.lower().replace(".", "")
        }


        if asset["type"] in [
            "jpg",
            "jpeg",
            "png",
            "webp"
        ]:

            asset["type"] = "image"


        elif asset["type"] in [
            "mp4",
            "mkv",
            "mov"
        ]:

            asset["type"] = "video"


        else:

            asset["type"] = "audio"



        # Save dropped asset through service layer

        self.drop_service.add_asset_to_scene(
            scene_id,
            asset
        )


        # Refresh UI to show updated project state

        self.refresh()


        # User feedback

        self.statusBar().showMessage(
            f"Added {asset['type']} to scene {scene_id}"
        )



    def refresh(self):

        if self.current_project:

            # Load project scenes

            scenes = get_scenes(
                self.current_project
            )


            # Build simple media visibility map

            media_counts = {}


            for scene in scenes:

                media_counts[scene[0]] = len(
                    get_media(
                        scene[0]
                    )
                )


            # Display scenes with media count

            self.timeline.load_scenes(
                scenes,
                media_counts
            )


            self.audio_tracks.load_tracks(
                get_audio_tracks(
                    self.current_project
                )
            )


            self.assets.load_assets(
                get_project_assets(
                    self.current_project
                )
            )
