"""Main GUI application entry point for Input Link."""

import sys
from pathlib import Path

# Add src to path if needed
src_path = Path(__file__).parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from input_link.gui.application import run_gui_application

def main():
    """Main entry point for Input Link GUI application."""
    return run_gui_application()

if __name__ == "__main__":
    sys.exit(main())