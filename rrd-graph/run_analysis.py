#!/usr/bin/env python3
"""
Wrapper script to run the analysis app from the project root.
This script sets up the Python path and runs the analysis app.
"""

import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent / "libs"
sys.path.insert(0, str(libs_path))

# Add the analysis app directory to Python path for utiles imports
analysis_path = Path(__file__).parent / "apps" / "analysis"
sys.path.insert(0, str(analysis_path))

if __name__ == "__main__":
    # Import and run the analysis app
    from apps.analysis.main import fapp
    import uvicorn
    
    print("Starting Analysis Service...")
    uvicorn.run(fapp, host="0.0.0.0", port=8000)
