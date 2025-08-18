FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY core/ ./core/
COPY ingest/ ./ingest/
COPY convert/ ./convert/
COPY indexing/ ./indexing/
COPY api/ ./api/
COPY ops/ ./ops/
COPY storage/ ./storage/

# Set Python path
ENV PYTHONPATH=/app

# Default command (no-op for development)
CMD ["python", "-c", "print('🏉 Rugby pipeline container ready'); exit(0)"]