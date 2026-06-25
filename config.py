import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DEFAULT_PLAYLIST_URL: str = "https://www.youtube.com/playlist?list=PLrKoDCoQ3iH5hV6LgXzPz6v-N5d4n7L1A"
    HOST: str = "0.0.0.0"
    PORT: int = 3030
    VLC_ARGS: str = "--no-video --quiet --no-xlib"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
