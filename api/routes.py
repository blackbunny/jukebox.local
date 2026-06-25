import asyncio
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import yt_dlp

from core.queue_manager import QueueManager
from core.audio_player import AudioPlayer

logger = logging.getLogger("JukeboxAPI")

# Initialize global Queue Manager
queue_manager = QueueManager()

# WebSocket Connection Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Push initial state upon connection
        await self.send_personal_message(queue_manager.get_state(), websocket)
        logger.info(f"WebSocket client connected. Total clients: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket client disconnected. Total clients: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending direct WebSocket message: {e}")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                # Connection might be stale, skip it; disconnect will cleanup
                pass

manager = ConnectionManager()

# Global event loop reference to broadcast state updates from thread-safe contexts
loop = None

def broadcast_state():
    """Triggers an async broadcast of the current queue state."""
    global loop
    if loop is not None:
        asyncio.run_coroutine_threadsafe(manager.broadcast(queue_manager.get_state()), loop)

# Initialize Audio Player with references to Queue Manager and state broadcaster callback
audio_player = AudioPlayer(queue_manager, broadcast_state)

# API App Instance
app = FastAPI(title="Jukebox-Local")

# Setup Template Engine
templates = Jinja2Templates(directory="templates")

# Request Pydantic models
class AddTrackRequest(BaseModel):
    url: str
    title: str
    duration: int
    play_next: bool = False
    thumbnail: str | None = None

def search_youtube(query: str, max_results: int = 5) -> list[dict]:
    """Uses yt-dlp to search YouTube and return a lightweight list of results."""
    ydl_opts = {
        'default_search': 'ytsearch',
        'max_downloads': 0,
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            results = []
            if info and 'entries' in info:
                for entry in info['entries']:
                    if entry:
                        results.append({
                            "id": entry.get("id"),
                            "title": entry.get("title"),
                            "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                            "duration": int(entry.get("duration") or 0),
                            "thumbnail": f"https://img.youtube.com/vi/{entry.get('id')}/mqdefault.jpg",
                        })
            return results
        except Exception as e:
            logger.error(f"YouTube search failed for '{query}': {e}")
            return []

@app.on_event("startup")
async def startup_event():
    """Saves the running asyncio loop context so background threads can broadcast updates."""
    global loop
    loop = asyncio.get_running_loop()

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Serves the main application SPA dashboard."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    return templates.TemplateResponse(request=request, name="index.html", context={"client_ip": client_ip})

@app.get("/search")
async def search_tracks(q: str = Query(..., min_length=1)):
    """Searches YouTube and returns list of songs."""
    results = search_youtube(q)
    return {"results": results}

@app.post("/queue/add")
async def add_track(payload: AddTrackRequest, request: Request):
    """Adds a track to the active queue."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    track = queue_manager.add_track(
        title=payload.title,
        url=payload.url,
        duration=payload.duration,
        added_by_ip=client_ip,
        play_next=payload.play_next,
        thumbnail=payload.thumbnail
    )
    broadcast_state()
    return {"success": True, "track": track}

@app.delete("/queue/remove/{track_id}")
async def remove_track(track_id: str, request: Request):
    """Removes a track from the queue. Restricts action using requesting client's IP."""
    client_ip = request.client.host if request.client else "127.0.0.1"
    success, message = queue_manager.remove_track(track_id, client_ip)
    if not success:
        raise HTTPException(status_code=403, detail=message)
    broadcast_state()
    return {"success": True, "message": message}

@app.post("/player/skip")
async def skip_track():
    """Triggers skip logic on the audio player."""
    audio_player.skip()
    return {"success": True}

@app.post("/player/toggle")
async def toggle_player():
    """Toggles playback between playing and paused."""
    is_playing = audio_player.toggle_play()
    return {"success": True, "is_playing": is_playing}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket route for real-time queue states synchronization."""
    await manager.connect(websocket)
    try:
        while True:
            # Maintain connection alive, ignore incoming frame payloads
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
