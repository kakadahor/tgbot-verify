# --- Stage 1: Builder ---
FROM python:3.11-slim as builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Optimization: Install CPU-only PyTorch first to avoid CUDA bloat (Saves ~4GB)
RUN pip install --no-cache-dir torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install the rest of the dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Stage 2: Final ---
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Singapore

WORKDIR /app

# Install ONLY necessary runtime libraries (No dev tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    libcairo2 \
    ffmpeg \
    dumb-init \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed python packages from the builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Security: Run as non-root user
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

ENTRYPOINT ["/usr/bin/dumb-init", "--"]
CMD ["python", "bot.py"]
