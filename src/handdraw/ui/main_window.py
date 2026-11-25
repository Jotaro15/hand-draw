"""Main window of the application."""

import tkinter as tk
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from handdraw.camera import FRAME_HEIGHT, FRAME_WIDTH, Camera, CameraError
from handdraw.fingers import DEFAULT_FINGER, Finger
from handdraw.hand_overlay import draw_hand
from handdraw.hand_tracker import HandTracker

WINDOW_TITLE = "hand-draw"
VIDEO_WIDTH = FRAME_WIDTH
VIDEO_HEIGHT = FRAME_HEIGHT
REFRESH_DELAY_MS = 33  # about 30 frames per second
WAITING_MESSAGE = "Waiting for the camera..."
NO_CAMERA_TEXT = "No camera found"
TRACKING_ON_TEXT = "Hand tracking: on"
TRACKING_OFF_TEXT = "Hand tracking: off"


class MainWindow:
    """Top-level window with a toolbar on top and the video area below."""

    def __init__(
        self,
        camera: Camera | None = None,
        hand_tracker: HandTracker | None = None,
    ) -> None:
        self.camera = camera
        self.hand_tracker = hand_tracker
        self._camera_indexes: list[int] = []
        self.selected_finger = DEFAULT_FINGER

        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.resizable(False, False)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

        self.toolbar = ttk.Frame(self.root, padding=5)
        self.toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Label(self.toolbar, text="Camera:").pack(side=tk.LEFT)
        self.camera_selector = ttk.Combobox(self.toolbar, width=16, state="disabled")
        self.camera_selector.set(NO_CAMERA_TEXT)
        self.camera_selector.pack(side=tk.LEFT, padx=5)
        self.camera_selector.bind("<<ComboboxSelected>>", self._on_camera_selected)
        ttk.Label(self.toolbar, text="Finger:").pack(side=tk.LEFT, padx=(10, 0))
        self.finger_selector = ttk.Combobox(
            self.toolbar,
            width=10,
            state="readonly",
            values=[finger.label for finger in Finger],
        )
        self.finger_selector.current(list(Finger).index(self.selected_finger))
        self.finger_selector.pack(side=tk.LEFT, padx=5)
        self.finger_selector.bind("<<ComboboxSelected>>", self._on_finger_selected)
        tracking_text = TRACKING_ON_TEXT if hand_tracker is not None else TRACKING_OFF_TEXT
        self._tracking_label = ttk.Label(self.toolbar, text=tracking_text)
        self._tracking_label.pack(side=tk.RIGHT)

        self.video_canvas = tk.Canvas(
            self.root,
            width=VIDEO_WIDTH,
            height=VIDEO_HEIGHT,
            bg="black",
            highlightthickness=0,
        )
        self.video_canvas.pack(side=tk.TOP)

        self.status_bar = ttk.Frame(self.root, padding=(5, 2))
        self.status_bar.pack(side=tk.TOP, fill=tk.X)
        self._status_label = ttk.Label(self.status_bar)
        self._status_label.pack(side=tk.LEFT)

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
    def status(self) -> str:
        """Text currently displayed in the toolbar status area."""
        return str(self._status_label.cget("text"))

    @property
    def tracking_status(self) -> str:
        """Text telling whether hand tracking is on, displayed in the toolbar."""
        return str(self._tracking_label.cget("text"))

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

    def set_status(self, text: str) -> None:
        """Display a short text in the toolbar, for example an error."""
        self._status_label.configure(text=text)

    def set_available_cameras(self, indexes: list[int]) -> None:
        """Fill the camera drop-down list with the given camera indexes."""
        self._camera_indexes = list(indexes)
        if not indexes:
            self.camera_selector["values"] = ()
            self.camera_selector.set(NO_CAMERA_TEXT)
            self.camera_selector.configure(state="disabled")
            return
        self.camera_selector["values"] = [f"Camera {index}" for index in indexes]
        self.camera_selector.configure(state="readonly")
        self._select_current_camera()

    def select_camera(self, index: int) -> None:
        """Switch to the camera with the given index.

        If it cannot be opened, the current camera is kept and an error is
        displayed in the toolbar.
        """
        if self.camera is None:
            return
        try:
            self.camera.switch(index)
        except CameraError as error:
            if self.camera.is_open:
                self.set_status(f"{error} Still using camera {self.camera.index}.")
            else:
                self.set_status(str(error))
        else:
            self.set_status("")
        self._select_current_camera()

    def select_finger(self, finger: Finger) -> None:
        """Choose the finger that will draw."""
        self.selected_finger = finger
        self.finger_selector.current(list(Finger).index(finger))

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
            self._draw_hand(frame)
            self.show_frame(frame)

    def _draw_hand(self, frame: np.ndarray) -> None:
        """Find the hand in the frame and draw its landmarks on it."""
        if self.hand_tracker is None:
            return
        landmarks = self.hand_tracker.detect(frame)
        if landmarks is not None:
            draw_hand(frame, landmarks, self.selected_finger.tip_index)

    def _select_current_camera(self) -> None:
        """Make the drop-down list show the camera that is really in use."""
        if self.camera is not None and self.camera.index in self._camera_indexes:
            self.camera_selector.current(self._camera_indexes.index(self.camera.index))
        else:
            self.camera_selector.set("")

    def _on_camera_selected(self, _event: tk.Event) -> None:
        position = self.camera_selector.current()
        if position >= 0:
            self.select_camera(self._camera_indexes[position])

    def _on_finger_selected(self, _event: tk.Event) -> None:
        self.select_finger(list(Finger)[self.finger_selector.current()])

    def _refresh(self) -> None:
        """Called every REFRESH_DELAY_MS to show the latest camera frame."""
        self.update_frame()
        self._refresh_job = self.root.after(REFRESH_DELAY_MS, self._refresh)
