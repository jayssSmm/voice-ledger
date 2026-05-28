# app/config.py
import os
from dataclasses import dataclass

@dataclass
class Config:
    TELEGRAM_TOKEN:  str
    GROQ_API_KEY:    str
    DATABASE_URL:    str
    WHISPER_MODEL:   str = "whisper-large-v3-turbo"
    LLM_MODEL:       str = "llama-3.3-70b-versatile"
    PORT:            int = 8080

def get_config() -> Config:
    return Config(
        TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"],
        GROQ_API_KEY   = os.environ["GROQ_API_KEY"],
        DATABASE_URL   = os.environ["DATABASE_URL"],
        WHISPER_MODEL  = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo"),
        LLM_MODEL      = os.getenv("GROQ_LLM_MODEL",    "llama-3.3-70b-versatile"),
        PORT           = int(os.getenv("PORT", 8080)),
    )