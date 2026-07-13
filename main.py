import logging

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

import threading
import uvicorn
import yt_dlp

from config import settings
from api.routes import app, queue_manager, audio_player, broadcast_state

logger = logging.getLogger("JukeboxMain")

def seed_fallback_playlist():
    """Fetches tracks from the default YouTube playlist URL and seeds the QueueManager. Falls back to search query if failing."""
    url = settings.DEFAULT_PLAYLIST_URL
    try:
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'list' in query_params:
            playlist_id = query_params['list'][0]
            url = f"https://www.youtube.com/playlist?list={playlist_id}"
            logger.info(f"Normalized playlist URL to: {url}")
    except Exception as parse_err:
        logger.warning(f"Failed to normalize playlist URL: {parse_err}")

    logger.info(f"Fetching default playlist tracks: {url}")
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    tracks = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            tracks.append({
                                "title": entry.get("title") or "YouTube Track",
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "duration": int(entry.get("duration") or 0),
                                "thumbnail": f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                            })
                elif info.get("id"):
                    tracks.append({
                        "title": info.get("title") or "YouTube Track",
                        "url": f"https://www.youtube.com/watch?v={info.get('id')}",
                        "duration": int(info.get("duration") or 0),
                        "thumbnail": info.get("thumbnail") or f"https://img.youtube.com/vi/{info.get('id')}/mqdefault.jpg",
                    })
    except Exception as e:
        logger.warning(f"Failed to load fallback playlist via URL: {e}. Trying search fallback...")

    # If playlist was empty or failed, fetch a fallback list via search
    if not tracks:
        fallback_query = "ytsearch10:lofi study beats"
        logger.info(f"Seeding fallback playlist via search query: {fallback_query}")
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(fallback_query, download=False)
                if info and 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            tracks.append({
                                "title": entry.get("title") or "YouTube Track",
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "duration": int(entry.get("duration") or 0),
                                "thumbnail": f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                            })
        except Exception as search_err:
            logger.error(f"Error seeding fallback playlist via search: {search_err}")

    if tracks:
        queue_manager.set_fallback_playlist(tracks)
        logger.info(f"Successfully loaded fallback queue with {len(tracks)} tracks.")
        broadcast_state()
    else:
        logger.warning("No playable entries found for fallback playlist.")

@app.on_event("startup")
def on_startup():
    """Startup initialization: start playback thread and fetch fallback seeds."""
    logger.info("Initializing playback engine...")
    audio_player.start()
    
    # Run playlist fetching in a background thread to prevent startup block
    seeding_thread = threading.Thread(target=seed_fallback_playlist, daemon=True)
    seeding_thread.start()

@app.on_event("shutdown")
def on_shutdown():
    """Shutdown cleanup: terminate player engine gracefully."""
    logger.info("Halting playback engine...")
    audio_player.stop()

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(app, host=settings.HOST, port=settings.PORT, reload=False)
