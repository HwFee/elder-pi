from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./voice-assistant.db"
    
    # CORS
    cors_origins: List[str] = ["*"]
    
    # API Keys
    stt_api_key: str = ""
    llm_api_key: str = ""
    tts_api_key: str = ""
    
    # Signaling Server
    signaling_server_url: str = "http://localhost:8000"
    signaling_api_key: str = ""
    
    # Audio
    upload_dir: str = "./uploads"
    max_audio_size_mb: int = 10
    
    # LLM
    llm_model: str = "qwen-turbo"  # 通义千问
    llm_temperature: float = 0.3
    
    class Config:
        env_file = ".env"


settings = Settings()
