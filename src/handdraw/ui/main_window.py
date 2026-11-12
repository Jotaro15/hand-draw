"""Main window of the application."""

import tkinter as tk
from tkinter import ttk

WINDOW_TITLE = "hand-draw"
VIDEO_WIDTH = 640
VIDEO_HEIGHT = 480
REFRESH_DELAY_MS = 33  # about 30 frames per second


class MainWindow:
    """Top-level window with a toolbar on top and the video area below."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.toolbar = ttk.Frame(self.root, padding=5)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        self.video_canvas = tk.Canvas(
            self.root,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
            bg="black",
            highlightthickness=0,
        )
        self.video_canvas.pack(side=tk.TOP)
        self._draw_placeholder()

        self._refresh_job = None

    def run(self) -> None:
        """Start the refresh loop and enter the Tk main loop."""
        self._refresh()
        self.root.mainloop()

    def close(self) -> None:
        """Stop the refresh loop and destroy the window."""
        if self._refresh_job is not None:
            self.root.after_cancel(self._refresh_job)
            self._refresh_job = None
        self.root.destroy()

    def _draw_placeholder(self) -> None:
        self.video_canvas.create_text(
            VIDEO_WIDTH // 2,
            VIDEO_HEIGHT // 2,
            text="No camera yet",
            fill="white",
            font=("Arial", 16),
        )

    def _refresh(self) -> None:
        """Called every REFRESH_DELAY_MS. The camera and drawing updates will plug in here."""
        self._refresh_job = self.root.after(REFRESH_DELAY_MS, self._refresh)
