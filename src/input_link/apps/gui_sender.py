"""GUI Sender application entry point."""

import sys

from input_link.gui.application import run_gui_application


def main():
    """Main entry point for GUI sender."""
    return run_gui_application()


if __name__ == "__main__":
    # To run this script directly, use:
    # python -m src.input_link.apps.gui_sender
    sys.exit(main())
