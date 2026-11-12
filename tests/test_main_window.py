import tkinter as tk

import pytest

from handdraw.ui.main_window import VIDEO_HEIGHT, VIDEO_WIDTH, WINDOW_TITLE, MainWindow


@pytest.fixture
def window():
    try:
        main_window = MainWindow()
    except tk.TclError:
        pytest.skip("no display available")
    yield main_window
    main_window.close()


def test_window_title(window):
    assert window.root.title() == WINDOW_TITLE


def test_video_canvas_size(window):
    assert int(window.video_canvas["width"]) == VIDEO_WIDTH
    assert int(window.video_canvas["height"]) == VIDEO_HEIGHT


def test_video_canvas_shows_a_placeholder(window):
    assert len(window.video_canvas.find_all()) == 1
