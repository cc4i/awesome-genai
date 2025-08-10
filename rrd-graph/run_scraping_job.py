#!/usr/bin/env python3
"""
Wrapper script to run the scraping-job app from the project root.
This script sets up the Python path and runs the scraping-job app.
"""

import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent / "libs"
sys.path.insert(0, str(libs_path))

# Add the scraping-job app directory to Python path
scraping_job_path = Path(__file__).parent / "apps" / "scraping-job"
sys.path.insert(0, str(scraping_job_path))

if __name__ == "__main__":
    # Import and run the scraping-job app
    from apps.scraping_job.main import main
    
    print("Starting Scraping Job...")
    main()
