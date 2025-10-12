"""Main entry point for the Foxhole Stockpiles Client application."""

from foxhole_stockpiles.ui.app import App


def main() -> None:
    """Launch the Foxhole Stockpiles Client application."""
    window = App(title="Foxhole stockpiles v0.5", width=700, height=400)
    window.mainloop()


if __name__ == "__main__":
    main()
