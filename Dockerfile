# Use official Microsoft Playwright Python image as base
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Singapore

# Set working directory
WORKDIR /app

# Install system build tools and graphics headers
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    tzdata \
    build-essential \
    python3-all-dev \
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

# 2. System dependencies (including dumb-init and wget)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    dumb-init \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# 3. Install Google Chrome Stable
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and build tools
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install core pure-python packages first (unlikely to fail)
RUN pip install --no-cache-dir python-telegram-bot httpx python-dotenv pymysql

# Install packages that usually require compilation (granular & verbose)
# 1. Image and PDF tools
RUN pip install --verbose --no-cache-dir Pillow reportlab xhtml2pdf

# 2. Database and Systems
RUN pip install --verbose --no-cache-dir google-cloud-firestore psutil

# 3. Playwright (already in image, but ensuring requirements met)
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
