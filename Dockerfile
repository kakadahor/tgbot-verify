# Use official Microsoft Playwright Python image
# This image comes pre-installed with all necessary system dependencies and browsers
FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create a non-root user and change ownership for security
RUN useradd -m botuser && chown -R botuser:botuser /app
USER botuser

# Command to run the bot
CMD ["python", "bot.py"]
