"""Main entry point for the Foxhole Stockpiles Client application."""

from foxhole_stockpiles import __version__
from foxhole_stockpiles.ui.app import App


def main() -> None:
    """Launch the Foxhole Stockpiles Client application."""
    window = App(title=f"Foxhole Stockpiles v{__version__}", width=700, height=400)
    window.mainloop()


if __name__ == "__main__":
    main()
