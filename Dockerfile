# Use official Python slim image as base
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Singapore

# Set working directory
WORKDIR /app

# Install system dependencies (for PDF to PNG pipeline and general tools)
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    tzdata \
    build-essential \
    python3-dev \
    libcairo2-dev \
    pkg-config \
    libffi-dev \
    libssl-dev \
    libjpeg-dev \
    zlib1g-dev \
    libfreetype6-dev \
    liblcms2-dev \
    libwebp-dev \
    libharfbuzz-dev \
    libfribidi-dev \
    liblzma-dev \
    git \
    ffmpeg \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
COPY requirements.txt .
RUN pip install --verbose --no-cache-dir -r requirements.txt


# Copy the rest of the application
COPY . .

# Create a non-root user and change ownership for security
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Start the bot using dumb-init
ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python", "bot.py"]
