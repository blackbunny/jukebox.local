# Jukebox-Local

A production-ready, standalone network collaborative jukebox featuring a FastAPI backend, real-time WebSocket state synchronization, and a headless audio playback loop using VLC. Designed with a gorgeous, dark "Japanese Ma" minimalist user interface.

---

## Architecture & Features

- **Real-time Queue Synchronization:** Built-in WebSocket connection manager broadcasts state changes instantly across all devices.
- **Client Ownership Control:** Tracks additions by local network IP. Users can only remove tracks they personally queued.
- **Robust Headless Loop:** A background polling loop thread monitors the audio player. When a track completes or fails, it fetches the next track, extracts its direct stream URL dynamically using `yt-dlp`, and resumes playback.
- **Fallback Playlist:** On startup, pulls tracks from a default YouTube playlist to ensure continuous music play even when the user queue is empty.
- **Mock Player Fallback:** Gracefully falls back to a simulated playback loop if `libvlc` or VLC binaries are missing from the host environment, allowing development and testing anywhere.

---

## Directory Structure

```text
/home/m/www/LocalRadio/
├── config.py              # Pydantic Settings management
├── main.py                # App entrypoint and startup seeding
├── requirements.txt       # Python package dependencies
├── Dockerfile             # Docker container definition
├── README.md              # Setup and usage guide
├── core/
│   ├── __init__.py
│   ├── queue_manager.py   # Thread-safe queue logic & ownership checks
│   └── audio_player.py    # VLC / Mock audio playback controller
├── api/
│   ├── __init__.py
│   └── routes.py          # FastAPI REST endpoints & WebSockets
└── templates/
    └── index.html         # Tailwind CSS minimalist SPA UI
```

---

## Configuration

Settings are managed via Environment Variables or a local `.env` file at the root:

| Key | Default | Description |
|---|---|---|
| `DEFAULT_PLAYLIST_URL` | `https://www.youtube.com/playlist?list=PLrKoDCoQ3iH5hV6LgXzPz6v-N5d4n7L1A` | Fallback playlist to seed on startup. |
| `HOST` | `0.0.0.0` | Bind address. `0.0.0.0` allows local network access. |
| `PORT` | `3030` | Port for the web interface. |
| `VLC_ARGS` | `--no-video --quiet --no-xlib` | System command arguments for VLC. |

---

## Installation & Deployment

### Method 1: Native Installation (Recommended for Local Audio Output)

#### 1. Install System Dependencies
Ensure VLC and FFmpeg are installed on your Linux system:
```bash
sudo apt update
sudo apt install -y vlc ffmpeg
```

#### 2. Set Up Virtual Environment & Dependencies
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

#### 3. Run the Jukebox
```bash
python main.py
```
Open a browser and navigate to `http://localhost:3030` or `http://<your-local-ip>:3030` from any device on your local network.

---

### Method 2: Running via Docker

#### 1. Build the Docker Image
```bash
docker build -t jukebox-local .
```

#### 2. Run the Container
To allow VLC to output audio to the host machine's system speakers, run the container with audio device access:
```bash
docker run -d \
  --name jukebox \
  -p 3030:3030 \
  --device /dev/snd \
  --restart unless-stopped \
  jukebox-local
```

If you only want to test the server without routing to physical speaker hardware, you can launch without the `--device` flag, which will trigger the internal **Mock Player** and simulate playback.

---

## Development & Testing

You can use standard tooling for testing:
- Inspect terminal logs to watch background queue seeding and yt-dlp queries.
- Connect multiple browsers to watch the WebSocket synchronizing track lists and progress indicators in real time.
