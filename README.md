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

The application opens the default camera and shows a live, mirrored view.
If no camera can be opened, a message is displayed instead.

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
