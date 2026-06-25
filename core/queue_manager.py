import threading
import uuid

class QueueManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.active_track = None
        self.queue = []  # List of upcoming user-added tracks
        self.fallback_playlist = []  # Fallback playlist loaded from config
        self.fallback_index = 0
        self.is_playing = False
        self.progress = 0  # In seconds
        self.duration = 0  # In seconds

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
        """Pops the next track from the queue or fallback playlist."""
        with self.lock:
            if self.queue:
                self.active_track = self.queue.pop(0)
            elif self.fallback_playlist:
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
            }
