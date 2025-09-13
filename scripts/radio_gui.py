#!/usr/bin/env python3
"""Radio Server GUI - Main Entry Point

Launch the GUI interface for the Enhanced Radio Server.
"""

import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.gui.radio_gui import main

if __name__ == "__main__":
    main()