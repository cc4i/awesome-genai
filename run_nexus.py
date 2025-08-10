#!/usr/bin/env python3
"""
Root-level wrapper script to run the RRD Nexus application.
This script handles the virtual environment and imports from the rrd-graph project.
"""

import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent
rrd_graph_path = project_root / "rrd-graph"

# Add the rrd-graph directory to Python path
sys.path.insert(0, str(rrd_graph_path))

# Add the libs directory to Python path for rrd_shared imports
libs_path = rrd_graph_path / "libs"
sys.path.insert(0, str(libs_path))

# Add the nexus app directory to Python path for utils imports
nexus_path = rrd_graph_path / "apps" / "nexus"
sys.path.insert(0, str(nexus_path))

if __name__ == "__main__":
    try:
        # Import and run the nexus app
        from apps.nexus.main import fapp
        import uvicorn
        
        print("Starting RRD Nexus Service...")
        uvicorn.run(fapp, host="0.0.0.0", port=8000)
        
    except ImportError as e:
        print(f"Error importing nexus application: {e}")
        print("Make sure you're running this from the rrd-graph directory with:")
        print("  cd rrd-graph")
        print("  uv run python run_nexus.py")
        print("")
        print("Or ensure the virtual environment is properly set up.")
        sys.exit(1)
