# 🎬 StoryVideo

A desktop application for creating story-based videos from images, video clips, and audio.

**StoryVideo** provides a visual workspace for organizing projects into scenes, importing media, managing audio tracks, previewing content, and rendering the final project as an MP4 video.

Built with **Python** and **PySide6**, StoryVideo is designed as a structured desktop video creation environment.

---

## ✨ Features

### 📁 Project Management

- Create video projects
- Open existing projects
- Save project state
- Close projects
- Manage multiple projects

### 🎞️ Scene Management

- Create scenes
- Organize a project into multiple scenes
- Select scenes from the timeline
- Edit scene duration
- Track media assigned to each scene

### 🖼️ Media Import

Supported visual media includes:

- JPG
- JPEG
- PNG
- WEBP
- MP4
- MKV
- AVI
- MOV

Media can be added by:

- Selecting individual files
- Importing multiple files
- Scanning and importing an entire folder
- Dragging assets into scenes

### 🎵 Audio Support

- Add project audio tracks
- Support for MP3
- Support for WAV
- Support for OGG
- Manage audio tracks within the project

### 🧩 Visual Workspace

The StoryVideo editor includes:

- Timeline
- Scene selection
- Media preview
- Project assets browser
- Asset metadata panel
- Audio tracks panel

### 🖱️ Drag and Drop

Assets can be added directly to scenes through drag-and-drop support.

### 🎥 Video Rendering

Render completed projects as:

- MP4 video

---

## 🖥️ Technology

StoryVideo is built with:

- Python
- PySide6
- Qt
- MoviePy

The application uses a modular architecture with separate areas for:

- Core project management
- Scene management
- Media management
- Audio tracks
- Media importing
- Rendering
- Asset services
- User interface widgets

---

## 📁 Project Structure

A typical StoryVideo project structure may look like:

```text
StoryVideo/
│
├── main.py
│
├── storyvideo/
│   ├── core/
│   │   ├── project.py
│   │   ├── scene.py
│   │   └── media.py
│   │
│   ├── audio/
│   │   └── tracks.py
│   │
│   ├── importer/
│   │   ├── folder_importer.py
│   │   └── import_service.py
│   │
│   ├── renderer/
│   │   └── moviepy_renderer.py
│   │
│   ├── media/
│   │   ├── asset_service.py
│   │   └── drop_service.py
│   │
│   └── ui/
│       └── widgets/
│           ├── timeline.py
│           ├── preview.py
│           ├── audio_tracks.py
│           ├── assets.py
│           └── asset_metadata.py
│
├── requirements.txt
├── README.md
└── .gitignore
```

---

## 🚀 Installation

Clone the repository:

```bash
git clone git@github.com:Fanu2/StoryVideo.git
cd StoryVideo
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ Running StoryVideo

Run the application:

```bash
python main.py
```

---

## 🎬 Basic Workflow

1. Create a new project.
2. Add one or more scenes.
3. Import images or video files.
4. Import an entire media folder if needed.
5. Add media to scenes.
6. Adjust scene durations.
7. Add background music or other audio tracks.
8. Review the project using the preview panel.
9. Organize assets through the project workspace.
10. Render the completed project as an MP4 video.

---

## 🧠 Architecture

StoryVideo follows a modular design where the user interface is separated from core application services.

The main areas include:

- **Core** — Projects, scenes, and media data
- **Importer** — File and folder media importing
- **Media** — Asset handling and drag-and-drop services
- **Audio** — Project audio tracks
- **Renderer** — Video rendering
- **UI** — Timeline, preview, asset browser, metadata, and audio widgets

This structure allows the application to grow without placing all functionality in a single file.

---

## 🛠️ Requirements

The project requires Python and the libraries listed in:

```text
requirements.txt
```

Typical dependencies may include:

```text
PySide6
moviepy
```

Additional dependencies should be listed based on the modules used by the complete project.

---

## 🚧 Development Status

StoryVideo is under active development.

Current development focuses on building a structured desktop video editor with project management, scene-based storytelling, media importing, audio support, visual asset management, and MP4 rendering.

Future development may include:

- Improved timeline editing
- Scene reordering
- Video clip editing
- Transitions
- Text overlays
- Subtitles
- Audio controls
- Export settings
- Project templates
- Additional rendering formats
- Improved preview controls

---

## 📄 License

This project is currently intended for personal, educational, and experimental use.

A formal open-source license may be added in the future.

---

## 👤 Author

**Jasvir Singh Sidhu**

GitHub: https://github.com/Fanu2

---

# 🎬 StoryVideo

*Create scenes. Add media. Tell your story.*
