# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Install system dependencies: FFmpeg and OpenCV runtime libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and tests
COPY clipforge/ clipforge/
COPY tests/ tests/
COPY pyproject.toml .

# Default entry point
ENTRYPOINT ["python", "-m", "clipforge.cli"]
CMD ["--help"]
