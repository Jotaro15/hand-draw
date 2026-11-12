"""Application entry point."""

from handdraw.ui.main_window import MainWindow


def main() -> None:
    window = MainWindow()
    window.run()
