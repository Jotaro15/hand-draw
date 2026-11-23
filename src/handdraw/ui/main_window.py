"""Main window of the application."""

import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from handdraw.camera import FRAME_HEIGHT, FRAME_WIDTH, Camera, CameraError

WINDOW_TITLE = "hand-draw"
VIDEO_WIDTH = FRAME_WIDTH
VIDEO_HEIGHT = FRAME_HEIGHT
REFRESH_DELAY_MS = 33  # about 30 frames per second
WAITING_MESSAGE = "Waiting for the camera..."


class MainWindow:
    """Top-level window with a toolbar on top and the video area below."""

    def __init__(self, camera: Camera | None = None) -> None:
        self.camera = camera

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
        self._image_item = self.video_canvas.create_image(0, 0, anchor=tk.NW)
        self._text_item = self.video_canvas.create_text(
            VIDEO_WIDTH // 2,
            VIDEO_HEIGHT // 2,
            fill="white",
            font=("Arial", 16),
            justify=tk.CENTER,
            width=VIDEO_WIDTH - 40,
        )
        self._photo = None  # Tk forgets an image if Python does not keep a reference to it

        self.show_message(WAITING_MESSAGE)
        self._refresh_job = None

    @property
    def message(self) -> str:
        """Text currently displayed instead of the video (empty when a frame is shown)."""
        return self.video_canvas.itemcget(self._text_item, "text")

    @property
    def is_showing_frame(self) -> bool:
        return self._photo is not None

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

    def show_message(self, text: str) -> None:
        """Hide the video and display a text message instead."""
        self._photo = None
        self.video_canvas.itemconfigure(self._image_item, image="")
        self.video_canvas.itemconfigure(self._text_item, text=text)

    def show_frame(self, frame: np.ndarray) -> None:
        """Display a BGR frame, as returned by the camera, in the video area."""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(rgb_frame)
        if image.size != (VIDEO_WIDTH, VIDEO_HEIGHT):
            image = image.resize((VIDEO_WIDTH, VIDEO_HEIGHT))
        self._photo = ImageTk.PhotoImage(image, master=self.root)
        self.video_canvas.itemconfigure(self._image_item, image=self._photo)
        self.video_canvas.itemconfigure(self._text_item, text="")

    def update_frame(self) -> None:
        """Read one frame from the camera and display it."""
        if self.camera is None or not self.camera.is_open:
            return
        try:
            frame = self.camera.read()
        except CameraError as error:
            self.show_message(str(error))
        else:
            self.show_frame(frame)

    def _refresh(self) -> None:
        """Called every REFRESH_DELAY_MS to show the latest camera frame."""
        self.update_frame()
        self._refresh_job = self.root.after(REFRESH_DELAY_MS, self._refresh)
