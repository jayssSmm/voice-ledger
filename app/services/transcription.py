import os, tempfile, httpx
from groq import Groq
from app.config import get_config

_cfg = get_config()
_groq = Groq(api_key=_cfg.GROQ_API_KEY)

async def download_and_transcribe(file_path: str) -> str:
    async with httpx.AsyncClient() as client:
        r = await client.get(file_path)
        r.raise_for_status()

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp.write(r.content)
        ogg_path = tmp.name

    try:
        with open(ogg_path, "rb") as f:
            result = _groq.audio.transcriptions.create(
                file=("voice.ogg", f, "audio/ogg"),
                model=_cfg.WHISPER_MODEL,
                response_format="text",
            )
        return result.strip() if isinstance(result, str) else result.text.strip()
    finally:
        os.unlink(ogg_path)