import os
import json
import logging
import tempfile

import httpx
from groq import Groq
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading


logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


TELEGRAM_TOKEN    = os.environ["TELEGRAM_BOT_TOKEN"]
GROQ_API_KEY      = os.environ["GROQ_API_KEY"]

WHISPER_MODEL     = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3-turbo")
LLM_MODEL         = os.getenv("GROQ_LLM_MODEL",     "llama-3.3-70b-versatile")

groq = Groq(api_key=GROQ_API_KEY)
logger.info(f"Groq ready | ASR: {WHISPER_MODEL} | LLM: {LLM_MODEL}")

SYSTEM_PROMPT = """\
You are a precise data-extraction assistant.
Given a transcript of someone describing employment details,
extract the following fields and return ONLY valid JSON — no prose, no markdown fences.

Schema:
{
  "employer":       string | null,
  "role":           string | null,
  "wage":           string | null,
  "start_date":     string | null,
  "end_date":       string | null,
  "hours_per_week": number | null,
  "notes":          string | null
}

Rules:
- wage  → include amount + currency + period, e.g. "₹18,000/month" or "$25/hr"
- dates → ISO-8601 if possible, otherwise a plain description; end_date = "present" if still employed
- If a field is not mentioned use null
- Return ONLY the JSON object, nothing else
"""


def transcribe(audio_path: str) -> str:
    """Send audio file to Groq Whisper and return the transcript."""
    with open(audio_path, "rb") as f:
        result = groq.audio.transcriptions.create(
            file=("voice.ogg", f, "audio/ogg"),
            model=WHISPER_MODEL,
            response_format="text",   # plain string, no JSON wrapper
        )
    # response_format="text" → result is already a plain string
    return result.strip() if isinstance(result, str) else result.text.strip()


def extract_employment_data(transcript: str) -> dict:
    """Call Groq LLaMA to extract structured employment info from a transcript."""
    response = groq.chat.completions.create(
        model=LLM_MODEL,
        temperature=0,
        max_tokens=512,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": f"Transcript:\n{transcript}"},
        ],
    )
    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    return json.loads(raw)


def format_reply(transcript: str, data: dict) -> str:
    """Build the human-readable Telegram reply."""
    def v(x):
        return str(x) if x is not None else "—"

    lines = [
        "📋 *Employment Details Extracted*\n",
        f"🏢 *Employer:*      {v(data.get('employer'))}",
        f"💼 *Role:*          {v(data.get('role'))}",
        f"💰 *Wage:*          {v(data.get('wage'))}",
        f"📅 *Start Date:*    {v(data.get('start_date'))}",
        f"📅 *End Date:*      {v(data.get('end_date'))}",
        f"⏱  *Hours/Week:*   {v(data.get('hours_per_week'))}",
    ]
    if data.get("notes"):
        lines.append(f"📝 *Notes:*         {data['notes']}")

    lines += ["", "🎙 *Transcript:*", f"_{transcript}_"]
    return "\n".join(lines)


# Telegram

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Send me a *voice note* describing your employment "
        "(employer, wage, dates) and I'll extract the details instantly.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎙 *How to use:*\n\n"
        "1. Record a voice message describing your job.\n"
        "2. Mention employer name, wage/salary, start/end dates.\n"
        "3. I'll transcribe it and return structured data.\n\n"
        '*Example:* "I worked at Acme Corp as a backend developer '
        'from January 2024 to March 2025, earning ₹80,000 per month."',
        parse_mode="Markdown",
    )


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg  = update.message
    user = msg.from_user
    logger.info(f"Voice note from {user.id} ({user.username})")

    status = await msg.reply_text("⏳ Transcribing…")

    # download
    voice   = msg.voice or msg.audio
    tg_file = await context.bot.get_file(voice.file_id)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        ogg_path = tmp.name

    async with httpx.AsyncClient() as client:
        r = await client.get(tg_file.file_path)
        r.raise_for_status()
        with open(ogg_path, "wb") as f:
            f.write(r.content)

    # transcribe
    try:
        transcript = transcribe(ogg_path)
        logger.info(f"Transcript: {transcript}")
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        await status.edit_text("❌ Transcription failed. Please try again.")
        return
    finally:
        os.unlink(ogg_path)

    if not transcript:
        await status.edit_text("🤔 Couldn't make out any speech. Please try again.")
        return

    await status.edit_text("🔍 Extracting employment details…")

    # extract from llm
    try:
        data = extract_employment_data(transcript)
    except Exception as e:
        logger.error(f"LLM extraction error: {e}")
        await status.edit_text(
            f"✅ Transcribed, but extraction failed.\n\n_{transcript}_",
            parse_mode="Markdown",
        )
        return

    #structuring reply
    await status.edit_text(format_reply(transcript, data), parse_mode="Markdown")
    logger.info(f"Replied to {user.id}: {data}")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send a *voice note* 🎙, not text.",
        parse_mode="Markdown",
    )

#ping

class _PingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
 
    def log_message(self, *args):
        pass  # silence access logs
 
 
def start_ping_server():
    port = int(os.getenv("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), _PingHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info(f"Ping server listening on port {port}")

#Entry point

def main():
    start_ping_server()
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Bot is polling…")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import asyncio
    asyncio.set_event_loop(asyncio.new_event_loop())
    main()