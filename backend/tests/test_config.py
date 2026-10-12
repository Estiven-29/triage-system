import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_defaults(monkeypatch):
    for var in ("DATABASE_URL", "ALLOWED_ORIGINS", "CHAT_SESSION_TTL_MINUTES"):
        monkeypatch.delenv(var, raising=False)
    settings = Settings(_env_file=None)
    assert settings.DATABASE_URL == "sqlite:///./triage.db"
    assert settings.ALLOWED_ORIGINS == ["http://localhost:3000"]
    assert settings.CHAT_SESSION_TTL_MINUTES == 120


def test_reads_and_parses_environment(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@db:5432/triage")
    monkeypatch.setenv("ALLOWED_ORIGINS", "http://a.com, https://b.com ,")
    monkeypatch.setenv("CHAT_SESSION_TTL_MINUTES", "30")
    settings = Settings(_env_file=None)
    assert settings.DATABASE_URL == "postgresql+psycopg://u:p@db:5432/triage"
    assert settings.ALLOWED_ORIGINS == ["http://a.com", "https://b.com"]
    assert settings.CHAT_SESSION_TTL_MINUTES == 30


@pytest.mark.parametrize("value", ["abc", "0"])
def test_invalid_ttl_fails_fast(monkeypatch, value):
    monkeypatch.setenv("CHAT_SESSION_TTL_MINUTES", value)
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_reads_dotenv_file(tmp_path, monkeypatch):
    monkeypatch.delenv("CHAT_SESSION_TTL_MINUTES", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("CHAT_SESSION_TTL_MINUTES=45\n")
    assert Settings(_env_file=env_file).CHAT_SESSION_TTL_MINUTES == 45
