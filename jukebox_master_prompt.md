# AGENT INSTRUCTION: Initialize and Execute Standalone "Jukebox-Local" Web Application
# SYSTEM TARGET: Linux (Ubuntu/Debian), Headless Audio Output (PulseAudio/ALSA)

You are tasked with building a complete, production-ready, standalone local network jukebox web application called "Jukebox-Local". This is a completely independent project (NOT a skill/plugin). It must include a backend server, a headless audio playback loop, and an embedded minimalist web UI. You must generate all necessary files, configurations, and a clean project structure without placeholders.

## 1. Project Specifications & Tech Stack
- **Backend:** Python 3.11+ using FastAPI and Uvicorn.
- **Real-Time Layer:** WebSockets for instant queue synchronization across all connected local network devices.
- **Audio & Stream Engine:** `yt-dlp` for YouTube searching and audio stream extraction, combined with `python-vlc` or `mpv-python` for headless audio playback via system speakers.
- **Frontend:** Single-page application (SPA) served directly by FastAPI, styled with Tailwind CSS via CDN. Design philosophy must strictly follow "Japanese Ma" (minimalist, high contrast, generous whitespace, mobile-first, completely clean).

## 2. Core Feature Requirements & Logic
- **Playlist Initialization:** On startup, the server must parse a default YouTube Playlist URL (defined in config), fetch its tracks using `yt-dlp`, and seed the initial fallback queue so music plays immediately.
- **Dynamic Queue Management:** - Any user on the local network (e.g., accessing `http://192.168.1.X:3030`) can search YouTube videos.
  - Users can click a search result to "Add as Next Track" (inserted at index 1) or append to the end.
  - Every single queue modification (add, remove, track finish) must broadcast a WebSocket update to all connected clients instantly.
- **Client Ownership (IP-Based):** Capture the client's local IP (`request.client.host`) on every action. A user can ONLY remove tracks from the queue that they personally added. Default playlist tracks or tracks added by other local IPs must not show a "Delete" option or must reject the delete request.
- **Robust Audio Loop:** Implement a background thread/task that continuously monitors the audio player status. When a track ends, it must automatically:
  1. Pop the next track from the dynamic queue.
  2. If the queue is empty, pull a random/sequential track from the default backup playlist.
  3. Fetch the fresh raw audio stream URL via `yt-dlp` and pass it to the headless player.
  4. Broadcast the "Now Playing" update to all WebSockets.
  5. If a stream fails, log the error, gracefully skip to the next, and notify clients.

## 3. Required File Deliverables & Architecture
You must generate the complete implementation across these specific files:
1. `config.py`: Configuration management using Pydantic or basic Python class (Default playlist URL, Port, Host, Player arguments).
2. `core/queue_manager.py`: Thread-safe, in-memory queue manager handling additions, active track state, and IP-based ownership validation.
3. `core/audio_player.py`: Headless media player wrapper handling the audio stream playback loop, pause/skip commands, and "on_track_end" event hooks.
4. `api/routes.py`: FastAPI application setup including `/search`, `/queue/add`, `/queue/remove` endpoints, and the `/ws` WebSocket connection manager.
5. `templates/index.html`: The minimalist Tailwind CSS UI. Layout: Large "Now Playing" area with absolute clarity, a clean interactive search bar that displays real-time results, and an elegant, spacious upcoming queue list.
6. `requirements.txt`: All necessary Python dependencies pinned (`fastapi`, `uvicorn`, `yt-dlp`, `python-vlc`, etc.).
7. `Dockerfile`: A multi-stage or clean Debian/Ubuntu-based Dockerfile that installs `vlc` or `mpv` system dependencies (headless) alongside Python packages, exposing port 8000.
8. `README.md`: Clear setup guide for local deployment (both via native Python and via Docker).

## 4. Operational Constraints
- No external databases (PostgreSQL/Redis) allowed. Keep everything in-memory for zero-infra portable deployment.
- Ensure the audio player configuration explicitly disables video output (`--no-video` or equivalent flags) to prevent crashes on headless servers.
- Absolutely NO code placeholders or "TODO" comments. Write the full production-ready logic.

Please execute the generation sequence now, laying out the directory structure first, then writing each file completely.