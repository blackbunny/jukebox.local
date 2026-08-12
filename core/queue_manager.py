import threading
import uuid

from core.playlist_fetcher import fetch_default_playlist

class QueueManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_track = None
        self.queue = []  # List of upcoming user-added tracks
        self.fallback_playlist = []  # Fallback playlist loaded from config
        self.fallback_index = 0
        self.last_track_source = None  # Track whether last played track was from 'queue' or 'fallback'
        self.is_playing = False
        self.progress = 0  # In seconds
        self.duration = 0  # In seconds
        self.volume = 70  # Default volume level (0-100)

    def set_fallback_playlist(self, tracks: list[dict]):
        """Sets the fallback playlist tracks fetched at startup."""
        with self.lock:
            self.fallback_playlist = tracks
            self.fallback_index = 0

    def add_track(self, title: str, url: str, duration: int, added_by_ip: str, play_next: bool = False, thumbnail: str = None) -> dict:
        """Adds a track to the dynamic queue."""
        track = {
            "id": uuid.uuid4().hex,
            "title": title,
            "url": url,
            "duration": duration,
            "added_by_ip": added_by_ip,
            "thumbnail": thumbnail,
        }
        with self.lock:
            if play_next:
                # Insert at the beginning of the upcoming queue
                self.queue.insert(0, track)
            else:
                self.queue.append(track)
        return track

    def remove_track(self, track_id: str, client_ip: str) -> tuple[bool, str]:
        """
        Removes a track from the queue, verifying ownership by IP address.
        Allow localhost (127.0.0.1) full administrative control.
        """
        with self.lock:
            for idx, track in enumerate(self.queue):
                if track["id"] == track_id:
                    # Validate ownership
                    if track["added_by_ip"] == client_ip or client_ip in ("127.0.0.1", "::1"):
                        self.queue.pop(idx)
                        return True, "Track removed from queue."
                    else:
                        return False, "Permission denied: You did not add this track."
            return False, "Track not found in queue."

    def get_next_track(self) -> dict | None:
        """
        Pops the next track from the queue or fallback playlist.
        Before starting/restarting the fallback playlist (e.g. after user queue finishes,
        when default list loops back to index 0, or if fallback list is empty),
        re-fetches the default playlist from YouTube.
        """
        needs_refresh = False

        with self.lock:
            if self.queue:
                self.active_track = self.queue.pop(0)
                self.last_track_source = "queue"
                self.progress = 0
                self.duration = self.active_track.get("duration", 0)
                return self.active_track

            # User queue is empty. Re-fetch default playlist if:
            # 1. We reached the end of the fallback playlist (fallback_index >= len(fallback_playlist))
            # 2. Fallback playlist is empty
            if (
                not self.fallback_playlist
                or self.fallback_index >= len(self.fallback_playlist)
            ):
                needs_refresh = True

        # Fetch playlist outside lock to avoid blocking API requests during network call
        if needs_refresh:
            new_tracks = fetch_default_playlist()
            if new_tracks:
                with self.lock:
                    self.fallback_playlist = new_tracks
                    if self.fallback_index >= len(new_tracks):
                        self.fallback_index = 0

        with self.lock:
            # Check user queue again in case a new track was added while fetching
            if self.queue:
                self.active_track = self.queue.pop(0)
                self.last_track_source = "queue"
            elif self.fallback_playlist:
                if self.fallback_index >= len(self.fallback_playlist):
                    self.fallback_index = 0
                track = self.fallback_playlist[self.fallback_index]
                self.fallback_index = (self.fallback_index + 1) % len(self.fallback_playlist)
                self.active_track = {
                    "id": f"fallback-{uuid.uuid4().hex[:8]}",
                    "title": track["title"],
                    "url": track["url"],
                    "duration": track.get("duration", 0),
                    "added_by_ip": "system",
                    "thumbnail": track.get("thumbnail"),
                }
                self.last_track_source = "fallback"
            else:
                self.active_track = None

            if self.active_track:
                self.progress = 0
                self.duration = self.active_track.get("duration", 0)
            return self.active_track

    def update_progress(self, progress: int):
        """Updates the current track playback progress."""
        with self.lock:
            self.progress = progress

    def set_playing_state(self, is_playing: bool):
        """Sets whether the player is active or paused."""
        with self.lock:
            self.is_playing = is_playing

    def set_volume(self, volume: int):
        """Updates the player volume."""
        with self.lock:
            self.volume = volume

    def get_state(self) -> dict:
        """Returns the complete serialized state of the queue and player."""
        with self.lock:
            return {
                "active_track": self.active_track,
                "queue": self.queue,
                "is_playing": self.is_playing,
                "progress": self.progress,
                "duration": self.duration,
                "fallback_count": len(self.fallback_playlist),
                "fallback_playlist": self.fallback_playlist,
                "fallback_index": self.fallback_index,
                "volume": self.volume,
            }
