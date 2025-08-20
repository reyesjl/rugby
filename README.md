# Rugby Pipeline

A comprehensive Python-based video processing system designed for rugby video analysis and content management.
The pipeline provides end-to-end capabilities for video ingestion, format conversion, AI-powered transcription and indexing, and searchable content generation.

---

## Features

- **Video Ingestion**
  Automated discovery of video files from multiple source types (Linux desktop, Windows desktop, network hosts).
  _Source: `pipeline_models.py:44-49`_

- **Format Conversion**
  Standardization to MP4 format using FFmpeg with configurable quality settings.
  _Source: `pipeline_models.py:112-141`_

- **AI-Powered Indexing**
  Content analysis using OpenAI models for searchable metadata generation.
  _Source: `pipeline_models.py:169-178`_

- **Type-Safe Configuration**
  YAML-based pipeline configuration with Python model validation.
  _Source: `pipeline_models.py:220-234`_

---

## Quick Start

### Installation
```bash
pip install -e .
```

### Basic Usage
Create a pipeline configuration file (e.g., `pipeline.yaml`):

```yaml
video_processing:
  sources:
    - type: "linux_desktop"
      path: "/path/to/videos"
      watch_patterns: ["mp4", "mpg"]
  conversion:
    ffmpeg:
      video_codec: "libx264"
      crf: 23
      preset: "fast"
    parallel_workers: 1
  indexing:
    ai_provider: "openai"
    model: "gpt-4o-mini"
    batch_size: 10
```

Run the pipeline:

```bash
rugby-cli --config pipeline.yaml
```

---

## CLI Commands

- `rugby-cli --config <path>` → Execute a configured video processing pipeline (`cli.py:19-23`)
- `rugby-cli --version` → Display version information (`cli.py:24-28`)
- `rugby-cli --status` → Show pipeline status and readiness (`cli.py:29-33`)

---

## Architecture

The system follows a modular architecture with clear separation of concerns:

```
rugby/
├── core/           # Core pipeline logic and CLI
├── ingest/         # Video file discovery
├── convert/        # Video conversion utilities
├── indexing/       # Video indexing and search
├── api/            # API endpoints and web interface
├── ops/            # Operations and DevOps utilities
└── storage/        # Data storage and persistence
```

---

## Configuration

The pipeline uses type-safe configuration models that support:

- **Video Sources**
  Multiple source types with configurable watch patterns
  _(`pipeline_models.py:52-80`)_

- **Conversion Settings**
  FFmpeg parameters and parallel processing options
  _(`pipeline_models.py:143-164`)_

- **AI Indexing**
  Provider settings, model selection, and prompt configuration
  _(`pipeline_models.py:169-215`)_

---

## Development

### Requirements
- Python 3.9+ (`pyproject.toml:10`)
- FFmpeg (for video conversion)
- OpenAI API key (for indexing)

### Setup
```bash
# Install with development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Code formatting and linting
ruff check .
ruff format .
mypy .
```

### Development Tools
Defined in `pyproject.toml:30-36`:

- **pytest** → Testing framework
- **ruff** → Code formatting and linting
- **mypy** → Static type checking
- **pre-commit** → Git hooks for code quality

---

## Project History

This project evolved from a collection of shell scripts and Python utilities in the `/scripts` directory that handled video ingestion, conversion, and indexing tasks.

The current implementation provides a **unified, type-safe pipeline** with proper configuration management and a CLI interface—replacing the previous ad-hoc script-based approach while maintaining compatibility with existing video processing workflows.

---

## License
This software is proprietary and the sole property of Biasware LLC.
Copyright (c) 2025 Biasware LLC. All rights reserved.

Use of this software is governed by the Biasware LLC Proprietary License.
Unauthorized copying, modification, distribution, or reverse engineering is strictly prohibited.

For licensing inquiries, contact: contact@biasware.com
