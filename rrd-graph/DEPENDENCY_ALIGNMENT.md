# Dependency Alignment Documentation

This document shows the alignment between `requirements.txt` and `pyproject.toml` files across the project.

## Project Structure

```
rrd-graph/
├── requirements.txt                    # Root project dependencies
├── pyproject.toml                     # Root project configuration
├── libs/
│   └── rrd_shared/
│       ├── requirements.txt           # rrd_shared library dependencies
│       └── pyproject.toml            # rrd_shared library configuration
└── apps/
    ├── loadgen/
    │   ├── requirements.txt           # Loadgen app dependencies
    │   └── pyproject.toml            # Loadgen app configuration
    └── console/
        ├── requirements.txt           # Console app dependencies
        └── pyproject.toml            # Console app configuration
```

## Dependency Alignment Status

### ✅ Root Project (`rrd-graph/`)
- **Status**: Aligned
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: rrd-shared (local), dotenv, fastapi, google-cloud-*, gradio, langchain-*, pg8000, sqlalchemy, uvicorn

### ✅ Shared Library (`libs/rrd_shared/`)
- **Status**: Aligned and Optimized
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: dotenv, google-cloud-alloydb-connector, google-cloud-run, langchain-google-*, pg8000, sqlalchemy, pytz
- **Optimization**: Removed unnecessary dependencies (fastapi, gradio, uvicorn) based on actual code usage

### ✅ Loadgen App (`apps/loadgen/`)
- **Status**: Aligned
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: dotenv, fastapi, google-cloud-*, gradio, langchain-*, pg8000, sqlalchemy, uvicorn

### ✅ Console App (`apps/console/`)
- **Status**: Aligned
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: dotenv, fastapi, google-cloud-*, gradio, langchain-*, pg8000, sqlalchemy, uvicorn

### ✅ Analysis App (`apps/analysis/`)
- **Status**: Aligned
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: dotenv, fastapi, google-cloud-*, gradio, langchain-*, pg8000, sqlalchemy, uvicorn
- **Special Dependencies**: google-cloud-language (for NLP sentiment analysis)

### ✅ Scraping-Job App (`apps/scraping-job/`)
- **Status**: Aligned
- **Files**: `pyproject.toml` ↔ `requirements.txt`
- **Key Dependencies**: requests, unstructured, tweepy, nltk, numpy, langchain-*, google-cloud-*, dotenv
- **Special Dependencies**: unstructured (for HTML parsing), tweepy (for Twitter API), nltk (for NLP)

## Key Changes Made

1. **Removed Duplicate Dependencies**: Eliminated redundant dependencies that weren't actually used
2. **Version Consistency**: Ensured all version constraints match between requirements.txt and pyproject.toml
3. **Minimal Dependencies**: rrd_shared library now only includes dependencies it actually imports
4. **Standardized Format**: All requirements.txt files now use consistent formatting and version constraints

## Benefits

- **Maintenance**: Easier to maintain dependencies in one place
- **Consistency**: No more version conflicts between requirements.txt and pyproject.toml
- **Clarity**: Clear separation between what's needed vs. what's declared
- **UV Integration**: Better integration with uv package management

## Usage

- **Development**: Use `uv sync` to install dependencies from pyproject.toml
- **Deployment**: Use requirements.txt for traditional pip installations
- **CI/CD**: Both files can be used interchangeably for dependency resolution
