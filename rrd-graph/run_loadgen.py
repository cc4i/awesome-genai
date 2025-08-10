#!/usr/bin/env python3
"""
Wrapper script to run the loadgen app with proper Python path setup.
This script sets up the Python path to include the rrd_shared library.
"""

import sys
from pathlib import Path

# Add the libs directory to Python path for rrd_shared imports
libs_path = Path(__file__).parent / "libs"
sys.path.insert(0, str(libs_path))

# Now run the main loadgen script
if __name__ == "__main__":
    # Import and run the main function from loadgen
    from apps.loadgen.main import read_simulating_policies
    import os
    from dotenv import load_dotenv

    # Load environment variables
    load_dotenv()

    # Get configuration from environment
    project_id = os.getenv("PROJECT_ID")
    cr_location = os.getenv("CR_LOCATION")
    model_location = os.getenv("MODEL_LOCATION")
    model_id = os.getenv("MODEL_ID")
    policy_bucket = os.getenv("POLICY_BUCKET") or "simulating_policy_bucket-multi-gke-ops"
    policy_running_folder = os.getenv("SIMULATING_POLICY_FOLDER") or "running_polices"

    print(f"Starting loadgen with project_id={project_id}, model_id={model_id}")

    # Run the main function
    read_simulating_policies(
        project_id=project_id,
        cr_location=cr_location,
        model_location=model_location,
        model_id=model_id,
        bucket=policy_bucket,
        folder=policy_running_folder
    )
