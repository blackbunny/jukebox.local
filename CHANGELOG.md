# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-08-18

### Fixed
- **YouTube 403 Forbidden & Rapid Skip Issue (`core/audio_player.py`):**
  - Added `extractor_args={'youtube': {'player_client': ['android', 'ios']}}` to `yt-dlp` in `resolve_stream_url`. This resolves YouTube's stream URL access block (HTTP 403) when played back via VLC.
  - Added loop throttling and safety delay to prevent rapid-fire track skipping during transient stream extraction/playback errors.

### Added
- **Default Playlist Shuffle Mode (`core/queue_manager.py`):**
  - Fallback/default playlist is now randomly shuffled upon initial load and refresh.
  - The fallback playlist is automatically re-shuffled after cycling through all tracks to ensure varied playback order without repeating the same sequence.
