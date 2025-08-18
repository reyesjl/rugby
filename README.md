# Rugby Pipeline

A modern Python monorepo for rugby video analysis and processing.

## Overview

The Rugby Pipeline is a comprehensive system for ingesting, processing, analyzing, and serving rugby video content. It provides tools for video conversion, transcription, indexing, and content generation.

## Architecture

The project is organized as a monorepo with the following packages:

- **`core/`** - Core pipeline functionality and CLI
- **`ingest/`** - Video ingestion and preprocessing  
- **`convert/`** - Video format conversion utilities
- **`indexing/`** - Video indexing and search functionality
- **`api/`** - API endpoints and web interface
- **`ops/`** - Operations and DevOps utilities
- **`storage/`** - Data storage and persistence layer

## Development Setup

1. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Set up pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests:
   ```bash
   pytest
   ```

4. Run the development environment:
   ```bash
   docker compose up
   ```

## Tools and Configuration

- **Ruff** - Fast Python linter and formatter
- **MyPy** - Static type checking
- **pytest** - Testing framework
- **pre-commit** - Git hooks for code quality
- **Docker** - Containerized development environment

## Configuration

The pipeline is configured via `pipeline_config.yaml`. See the file for available options and defaults.

## CLI Usage

```bash
# Show version
rugby-cli version

# Show status
rugby-cli status
```

## Development

This project uses modern Python tooling:

- Type hints throughout
- Automated code formatting with Ruff
- Pre-commit hooks for quality assurance
- Comprehensive testing with pytest
- Docker for consistent development environments

## License

MIT