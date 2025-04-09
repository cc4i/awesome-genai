# --- Stage 1: Build Dependencies ---
# Use a specific Python version matching your development environment
# Using a full image here can help if dependencies need compilation
FROM python:3.11 as builder

# Set the working directory inside the container
WORKDIR /opt/venv

# Create a virtual environment to isolate dependencies
RUN python -m venv .

# Activate the virtual environment for subsequent commands in this stage
# Note: ENV PATH is only effective for RUN commands within this stage
ENV PATH="/opt/venv/bin:$PATH"

# Copy only the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies into the virtual environment
# --no-cache-dir prevents caching roues downloaded wheels/packages
# --upgrade pip ensures we have the latest pip
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Runtime Image ---
# Use a slim image for a smaller final image size
FROM python:3.11-slim

# << --- ADDED --- >>
# Install system dependencies: ffmpeg (includes ffprobe)
# Run as root before creating/switching to the non-root user
# - apt-get update: Refresh package lists
# - apt-get install -y: Install package(s) without interactive prompts
# - --no-install-recommends: Avoid installing optional dependencies to save space
# - apt-get clean && rm -rf /var/lib/apt/lists/*: Clean up apt cache to reduce image size
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
# << --- END ADDED --- >>

# Set the working directory for the application
WORKDIR /app

# Copy the virtual environment with installed dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy the application code into the working directory
# Adjust this if your code is in a subdirectory (e.g., COPY ./src .)
COPY . .

# Set the PATH environment variable to include the venv's bin directory
# This ensures that 'uvicorn' and other installed binaries are found
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user and group
# Running as non-root is a security best practice
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Change ownership of the app directory and venv to the non-root user
# Ensure the user can read the application files and execute from the venv
RUN chown -R appuser:appgroup /app && \
    chown -R appuser:appgroup /opt/venv

# Switch to the non-root user
USER appuser

# Expose the port Uvicorn will run on (adjust if needed)
# This informs Docker that the container listens on this port
EXPOSE 8000

# Command to run the application using Uvicorn
# Replace 'main:app' with '<your_entrypoint_file>:<your_app_instance>'
# --host 0.0.0.0 makes the server accessible from outside the container
# --port 8000 matches the EXPOSE instruction
# Add --reload flag for development if needed, but remove for production
CMD ["python", "main.py"]