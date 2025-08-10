#!/usr/bin/env python3
"""
Wrapper script to run the console app with proper Python path setup.
This script sets up the Python path to include the rrd_shared library.
"""

import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent / "libs"
sys.path.insert(0, str(libs_path))

# Now run the main console script
if __name__ == "__main__":
    print("Starting console app...")
    print("The console app will launch a Gradio web interface on http://0.0.0.0:7860")
    
    # Import the console app - it will run automatically due to the if __name__ == "__main__" block
    import apps.console.main
