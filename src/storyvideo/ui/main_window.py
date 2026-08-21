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

from storyvideo.renderer.moviepy_renderer import (
    render_project,
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


        # Preview

        self.preview = PreviewWidget()


        # Project Audio

        self.audio_tracks = AudioTracksWidget()


        # Project Assets Browser

        self.assets = AssetsWidget()


        splitter = QSplitter(
            Qt.Vertical
        )


        splitter.addWidget(
            self.timeline
        )

        splitter.addWidget(
            self.preview
        )

        splitter.addWidget(
            self.assets
        )


        splitter.addWidget(
            self.audio_tracks
        )


        splitter.setSizes(
            [
                220,
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

        self.timeline.list.clear()

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


            add_media(
                self.current_scene,
                file,
                kind
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

                add_media(
                    self.current_scene,
                    file,
                    kind
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



            render_project(
                self.current_project,
                output_file
            )

    def select_scene(self, item):

        scene_id = (
            item.text()
            .split("|")[0]
            .strip()
        )


        for media in get_media(scene_id):

            if media[2] == "image":

                self.preview.show_image(
                    media[1]
                )

                break



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



    def refresh(self):

        if self.current_project:

            self.timeline.load_scenes(
                get_scenes(
                    self.current_project
                )
            )


            self.assets.load_assets(
                get_project_media(
                    self.current_project
                )
            )


            self.audio_tracks.load_tracks(
                get_audio_tracks(
                    self.current_project
                )
            )
