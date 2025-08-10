#!/usr/bin/env python3
"""
Wrapper script to run the nexus app from the project root.
This script sets up the Python path and runs the nexus app.
"""

import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent / "libs"
sys.path.insert(0, str(libs_path))

# Add the nexus app directory to Python path for utils imports
nexus_path = Path(__file__).parent / "apps" / "nexus"
sys.path.insert(0, str(nexus_path))

if __name__ == "__main__":
    # Import and run the nexus app
    from apps.nexus.main import fapp
    import uvicorn
    
    print("Starting RRD Nexus Service...")
    uvicorn.run(fapp, host="0.0.0.0", port=8000)
