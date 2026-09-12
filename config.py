import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
CHROMA_DIR = str(PROJECT_ROOT / "chroma_db")
FACULTY_JSON = PROJECT_ROOT / "data" / "faculty_profiles" / "faculty.json"

load_dotenv(PROJECT_ROOT / ".env")


def _secret(key: str) -> str | None:
    return os.getenv(key)


def get_google_api_key() -> str | None:
    return _secret("GOOGLE_API_KEY") or _secret("GEMINI_API_KEY")


def get_tavily_api_key() -> str | None:
    return _secret("TAVILY_API_KEY")
