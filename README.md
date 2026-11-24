# hand-draw

[![CI](https://github.com/Jotaro15/hand-draw/actions/workflows/ci.yml/badge.svg)](https://github.com/Jotaro15/hand-draw/actions/workflows/ci.yml)

Draw in the air with your hand and a webcam.

`hand-draw` tracks your hand through your camera, follows the finger you choose
and turns its movement into strokes on a small drawing app.

> **Status:** work in progress.

## Planned features

- Camera selection (built-in and external cameras)
- Hand tracking with 21 landmarks per hand
- Choice of the drawing finger
- Color palette, undo and redo
- Smoothing of the strokes
- Export of the drawing as a PNG image

## Usage

```bash
python -m handdraw
```

The application opens the first camera it finds and shows a live, mirrored view.
Use the drop-down list in the toolbar to switch to another camera.
If no camera can be opened, a message is displayed instead.

Cameras are detected when the application starts, so plug them in before launching it.

When a hand is visible, its 21 landmarks are drawn on the video. The first launch
downloads the MediaPipe hand landmark model (a few megabytes), so an internet
connection is needed once. The model is stored in `src/handdraw/models/` and is not
committed to the repository. If the download fails, the application still shows the
camera, and you can download the `hand_landmarker.task` file yourself (the link is
printed in the terminal) and save it in that folder.

## Development setup

Requires Python 3.10 to 3.12.

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate      # Linux / macOS
pip install -e ".[dev]"
```

Run the tests and the linter:

```bash
pytest
ruff check .
```

## License

Released under the [MIT License](LICENSE).
