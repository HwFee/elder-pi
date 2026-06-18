import os
from app.config import Settings, get_settings


def test_settings_load_from_env(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///./test.db")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000")
    monkeypatch.setenv("PORT", "8000")
    settings = get_settings()
    assert settings.secret_key == "test-secret"
    assert settings.database_url == "sqlite+aiosqlite:///./test.db"
    assert settings.access_token_expire_minutes == 60
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.port == 8000


def test_settings_defaults(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    settings = Settings()
    assert settings.database_url == "sqlite+aiosqlite:///./signaling.db"
    assert settings.access_token_expire_minutes == 1440
    assert settings.cors_origins == ["http://localhost:3000"]
    assert settings.port == 8000
    assert settings.upload_dir == "uploads/avatars"


def test_cors_origins_splits_comma_separated_values(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    settings = Settings()
    assert settings.cors_origins == ["http://localhost:3000", "http://localhost:5173"]
