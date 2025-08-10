# RRD Graph Project

This project contains a loadgen application that generates social media content using AI models.

## Project Structure

```
rrd-graph/
├── libs/
│   └── rrd_shared/          # Shared utilities and database connections
├── apps/
│   ├── loadgen/             # Load generation application
│   ├── console/             # Gradio-based console application
│   ├── analysis/            # FastAPI-based analysis service
│   └── scraping-job/        # Web scraping and social media scraping job
├── pyproject.toml           # Root project configuration
└── requirements.txt          # Root project dependencies
```

## Running the Applications

### From Project Root (Recommended)

Use the wrapper scripts for consistent execution:

```bash
# Loadgen app
uv run python run_loadgen.py

# Console app  
uv run python run_console.py

# Analysis app
uv run python run_analysis.py

# Scraping-job app
uv run python run_scraping_job.py

# Nexus app
uv run python run_nexus.py
```

### From Individual App Directories

Each app can also be run from its own directory:

```bash
# Loadgen
cd apps/loadgen
uv run python main.py

# Console
cd apps/console  
uv run python main.py

# Analysis
cd apps/analysis
uv run python main.py

# Scraping-job
cd apps/scraping-job
uv run python main.py

# Nexus
cd apps/nexus
uv run uvicorn main:fapp --host 0.0.0.0 --port 8000
```

## Import Issues and Solutions

### Common Import Issues

1. **`ModuleNotFoundError: No module named 'rrd_shared'`**
   - **Cause**: Python can't find the shared library
   - **Solution**: Use the wrapper scripts (`run_*.py`) or ensure `libs_path` is set correctly

2. **`ModuleNotFoundError: No module named 'apps'`**
   - **Cause**: Running from app directory with absolute imports
   - **Solution**: Use relative imports or run from project root

3. **`ImportError: cannot import name 'language_v2' from 'google.cloud'`**
   - **Cause**: Missing `google-cloud-language` dependency
   - **Solution**: Run `uv sync` to install all dependencies

### Dual-Import Strategy

All apps now support running from both project root and their own directories using a try-except pattern:

```python
try:
    from apps.app_name.module import Class
except ImportError:
    from module import Class  # Fallback for app directory
```

## App Details

### Loadgen App
- **Purpose**: Generate social media content based on policies
- **Features**: Policy-based content generation, Google Cloud Storage integration
- **Access**: Command-line interface

### Console App  
- **Purpose**: Web-based management interface for threads and policies
- **Features**: Gradio web UI, sentiment analysis, database operations
- **Access**: http://0.0.0.0:7860

### Analysis App
- **Purpose**: FastAPI web service for sentiment analysis and playbook generation
- **Features**: NLP integration, Google Cloud services, batch processing
- **Access**: http://0.0.0.0:8000

### Scraping-Job App
- **Purpose**: Web scraping and social media data collection
- **Features**: Google Search/News scraping, Twitter API integration, HTML parsing
- **Access**: Command-line interface, triggered by Cloud Scheduler

### Nexus App
- **Purpose**: Job management and orchestration service for Cloud Run
- **Features**: Cloud Run job creation, Cloud Scheduler integration, job status monitoring
- **Access**: http://0.0.0.0:8000

## Package Management with UV

This project uses `uv` for package management. Key commands:

- `uv sync` - Install all dependencies
- `uv sync --dev` - Install development dependencies  
- `uv run python script.py` - Run Python scripts in the virtual environment
- `uv pip install package` - Install additional packages

## Building with Skaffold

### Analysis App

The analysis app can be built using Skaffold with buildpacks from the project root:

```bash
cd rrd-graph
skaffold build --profile analysis-only
```

**Key Features:**
- **Buildpacks**: Uses Cloud Native Buildpacks for automatic Python detection
- **Shared Library**: Includes `rrd_shared` library from the project root
- **Context**: Builds from project root to access shared dependencies
- **Dockerignore**: Excludes unnecessary files while keeping essential ones

**Build Context:**
- Builds from project root (`rrd-graph/`)
- Includes `apps/analysis/` and `libs/rrd_shared/`
- Excludes other apps and unnecessary files via `.dockerignore`

### Development Workflow

```bash
# Build analysis app
skaffold build --profile analysis-only

# Deploy analysis app
skaffold deploy --profile analysis-only

# Development mode
skaffold dev --profile analysis-only
```

## Troubleshooting

### ModuleNotFoundError: No module named 'rrd_shared'
This error occurs when the Python path doesn't include the `rrd_shared` library. Solutions:

1. Use the wrapper script: `uv run python run_*.py`
2. Run from the root directory: `cd rrd-graph && uv run python apps/app_name/main.py`
3. Set PYTHONPATH: `export PYTHONPATH=/path/to/rrd-graph/libs:$PYTHONPATH`

### Import Issues with UV
UV doesn't automatically handle editable installs the same way as pip. The path-based import approach is more reliable for this project structure.

## Notes

- The `rrd_shared` library directory was renamed from `rrd-shared` (with hyphens) to `rrd_shared` (with underscores) to follow Python package naming conventions
- The project uses a workspace structure with `pyproject.toml` files in each subdirectory
- All apps support running from both project root and their own directories
- The scraping-job app integrates with Google Cloud Scheduler for automated execution