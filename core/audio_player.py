import logging
import threading
import time
import yt_dlp

logger = logging.getLogger("JukeboxAudioPlayer")

# Attempt VLC import and initialization
try:
    import vlc
    VLC_AVAILABLE = True
except ImportError:
    VLC_AVAILABLE = False
    logger.warning("python-vlc not installed. Falling back to Mock audio player.")

class MockVLCPlayer:
    """Mock VLC player to simulate playback when VLC is missing or headless system lacks libvlc."""
    def __init__(self):
        import collections
        # Simulate vlc State enums
        VlcState = collections.namedtuple('VlcState', ['NothingSpecial', 'Playing', 'Paused', 'Stopped', 'Ended', 'Error'])
        self.State = VlcState(0, 3, 4, 5, 6, 7)
        self._state = self.State.Stopped
        self.duration = 0
        self.start_time = 0
        self.paused_elapsed = 0

    def get_state(self):
        if self._state == self.State.Playing:
            elapsed = time.time() - self.start_time
            if elapsed >= self.duration:
                self._state = self.State.Ended
                return self.State.Ended
            return self.State.Playing
        return self._state

    def stop(self):
        self._state = self.State.Stopped

    def set_media(self, media):
        pass

    def play(self):
        if self._state == self.State.Paused:
            self.start_time = time.time() - self.paused_elapsed
        else:
            self.start_time = time.time()
            self.paused_elapsed = 0
        self._state = self.State.Playing

    def pause(self):
        if self._state == self.State.Playing:
            self.paused_elapsed = time.time() - self.start_time
            self._state = self.State.Paused

    def get_time(self):
        if self._state == self.State.Playing:
            return int((time.time() - self.start_time) * 1000)
        elif self._state == self.State.Paused:
            return int(self.paused_elapsed * 1000)
        return 0


class AudioPlayer:
    def __init__(self, queue_manager, broadcast_callback):
        self.queue_manager = queue_manager
        self.broadcast_callback = broadcast_callback
        self.running = False
        self.thread = None
        self.skip_requested = False
        self.vlc_instance = None
        self.player = None
        self.is_mock = False

        # Try to initialize system VLC
        if VLC_AVAILABLE:
            try:
                from config import settings
                vlc_args = settings.VLC_ARGS.split()
                self.vlc_instance = vlc.Instance(*vlc_args)
                self.player = self.vlc_instance.media_player_new()
                logger.info("VLC successfully initialized.")
            except Exception as e:
                logger.error(f"Failed to initialize VLC instance: {e}. Falling back to Mock player.")
                self.is_mock = True
        else:
            self.is_mock = True

        if self.is_mock:
            self.player = MockVLCPlayer()
            # If Mock, define the State enum mapping locally
            self.vlc_state = self.player.State
            logger.info("Mock player initialized.")
        else:
            self.vlc_state = vlc.State

    def resolve_stream_url(self, youtube_url: str) -> str | None:
        """Fetches the raw streaming audio URL using yt-dlp."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(youtube_url, download=False)
                if 'url' in info:
                    return info['url']
                elif 'formats' in info:
                    audio_formats = [f for f in info['formats'] if f.get('vcodec') == 'none']
                    if audio_formats:
                        return audio_formats[-1]['url']
                    return info['formats'][-1]['url']
        except Exception as e:
            logger.error(f"Failed to resolve streaming URL for {youtube_url}: {e}")
        return None

    def start(self):
        """Starts the background playback loop thread."""
        self.running = True
        self.thread = threading.Thread(target=self._playback_loop, daemon=True)
        self.thread.start()
        logger.info("Audio player loop thread started.")

    def stop(self):
        """Stops the audio player thread and VLC playback."""
        self.running = False
        if self.player:
            self.player.stop()
        logger.info("Audio player stopped.")

    def _playback_loop(self):
        last_broadcast_time = 0
        while self.running:
            try:
                state = self.player.get_state()

                # Determine if current track ended or skip was requested
                has_ended = state in (
                    self.vlc_state.Ended,
                    self.vlc_state.Error,
                    self.vlc_state.Stopped,
                )
                
                # Check for uninitialized/idle states if there is upcoming queue
                is_idle = state == (
                    self.vlc_state.NothingSpecial if hasattr(self.vlc_state, 'NothingSpecial') else 0
                )

                if has_ended or is_idle or self.skip_requested:
                    if self.skip_requested:
                        logger.info("Playback skip triggered.")
                        self.player.stop()
                        self.skip_requested = False

                    # Retrieve next track from the queue manager
                    next_track = self.queue_manager.get_next_track()
                    if next_track:
                        logger.info(f"Loading track: {next_track['title']}")
                        self.broadcast_callback()

                        # In Mock mode, skip yt-dlp lookup to be fast/offline friendly
                        if self.is_mock:
                            self.player.duration = next_track.get("duration") or 180
                            self.player.play()
                            self.queue_manager.set_playing_state(True)
                            logger.info(f"Mocking playback of: {next_track['title']}")
                            self.broadcast_callback()
                        else:
                            stream_url = self.resolve_stream_url(next_track['url'])
                            if not stream_url:
                                logger.error(f"Skipping track {next_track['title']} due to stream resolution failure.")
                                continue
                            
                            media = self.vlc_instance.media_new(stream_url)
                            self.player.set_media(media)
                            self.player.play()
                            self.queue_manager.set_playing_state(True)
                            logger.info(f"Started streaming: {next_track['title']}")
                            self.broadcast_callback()
                    else:
                        # Reset play state when queue is fully empty
                        if self.queue_manager.active_track is not None:
                            self.queue_manager.active_track = None
                            self.queue_manager.set_playing_state(False)
                            self.broadcast_callback()

                # If playing, keep track of progress and periodically notify clients
                if state == self.vlc_state.Playing:
                    time_ms = self.player.get_time()
                    if time_ms > 0:
                        progress = int(time_ms / 1000)
                        self.queue_manager.update_progress(progress)
                        
                        # Correct client drift by broadcasting progress every 2 seconds
                        now = time.time()
                        if now - last_broadcast_time >= 2.0:
                            self.broadcast_callback()
                            last_broadcast_time = now

            except Exception as e:
                logger.error(f"Error in playback loop: {e}", exc_info=True)

            time.sleep(0.5)

    def toggle_play(self) -> bool:
        """Toggles playback between play and pause. Returns the playing status."""
        state = self.player.get_state()
        if state == self.vlc_state.Playing:
            self.player.pause()
            self.queue_manager.set_playing_state(False)
            self.broadcast_callback()
            return False
        elif state == self.vlc_state.Paused:
            self.player.play()
            self.queue_manager.set_playing_state(True)
            self.broadcast_callback()
            return True
        else:
            # Force start if we have a track
            if self.queue_manager.active_track:
                self.player.play()
                self.queue_manager.set_playing_state(True)
                self.broadcast_callback()
                return True
            return False

    def skip(self):
        """Signals the loop thread to skip the current track."""
        self.skip_requested = True
