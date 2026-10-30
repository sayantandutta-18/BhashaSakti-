# Dockerfile for BhashaSandhi Multilingual Voice Assistant
# Base: Python 3.11 Slim with system audio libraries
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    HF_HOME=/app/cache/huggingface

# Install system dependencies: ffmpeg for audio transcoding and libsndfile1 for audio I/O
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install CPU-only PyTorch first to keep image lightweight (~200MB vs 2GB CUDA)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install remaining Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download Meta MMS-TTS models at build time so runtime cold-starts are instant
RUN python -c "\
from transformers import AutoTokenizer, VitsModel; \
models = ['facebook/mms-tts-hin', 'facebook/mms-tts-ben', 'facebook/mms-tts-ory']; \
print('Pre-caching MMS tokenizers and models...'); \
[AutoTokenizer.from_pretrained(m) for m in models]; \
[VitsModel.from_pretrained(m) for m in models]; \
print('MMS models successfully cached.')"

# Copy source code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose target port
EXPOSE 8080

# Production CMD: Single worker with 4 threads for concurrency and shared in-memory models
CMD exec gunicorn app:app --bind 0.0.0.0:${PORT:-8080} --workers 1 --threads 4 --timeout 120
