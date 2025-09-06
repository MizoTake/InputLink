"""Main GUI application entry point for Input Link."""

import sys

from input_link.gui.application import run_gui_application


def main():
    """Main entry point for Input Link GUI application."""
    return run_gui_application()


if __name__ == "__main__":
    # To run this script directly, use:
    # python -m src.input_link.apps.gui_main
    sys.exit(main())
