import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DEFAULT_PLAYLIST_URL: str = "https://www.youtube.com/watch?v=xgJWXFW1vVc&list=PLVFU_4LbUwis"
    HOST: str = "0.0.0.0"
    PORT: int = 3030
    VLC_ARGS: str = "--no-video --quiet --no-xlib"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
