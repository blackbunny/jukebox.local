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

from core.playlist_fetcher import fetch_default_playlist

logger = logging.getLogger("JukeboxMain")

def seed_fallback_playlist():
    """Fetches tracks from the default YouTube playlist URL and seeds the QueueManager."""
    tracks = fetch_default_playlist()
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
