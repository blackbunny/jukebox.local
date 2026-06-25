FROM python:3.11-slim-bookworm

# Install system dependencies including VLC and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    vlc \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# VLC refuses to run as root for security reasons.
# Create a dedicated non-root user and add it to the audio group to allow playback access.
RUN useradd -m -u 1000 jukebox && usermod -aG audio jukebox

WORKDIR /app

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Set proper ownership for the app directory
RUN chown -R jukebox:jukebox /app

# Switch to the non-root user context
USER jukebox

# Expose ports
EXPOSE 3030

# Run application
CMD ["python", "main.py"]
