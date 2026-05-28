from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.services.transcription import download_and_transcribe
from app.services.extraction import extract_employment_data
from app.services.ledger import upsert_user, save_entry
import logging

logger = logging.getLogger(__name__)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg     = update.message
    tg_user = msg.from_user
    status  = await msg.reply_text("⏳ Transcribing…")

    voice   = msg.voice or msg.audio
    tg_file = await context.bot.get_file(voice.file_id)

    try:
        transcript = await download_and_transcribe(tg_file.file_path)
    except Exception as e:
        logger.error(f"Transcription error: {e}")
        await status.edit_text("❌ Transcription failed. Please try again.")
        return

    if not transcript:
        await status.edit_text("🤔 Couldn't make out any speech. Please try again.")
        return

    await status.edit_text("🔍 Extracting employment details…")

    try:
        data = extract_employment_data(transcript)
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        await status.edit_text(f"✅ Transcribed, but extraction failed.\n\n_{transcript}_", parse_mode="Markdown")
        return

    # Persist to ledger
    db = SessionLocal()
    try:
        upsert_user(db, tg_user.id, tg_user.username, tg_user.full_name)
        entry = save_entry(db, tg_user.id, data, transcript)
    finally:
        db.close()

    def v(x): return str(x) if x is not None else "—"

    reply = (
        "✅ *Saved to your ledger!*\n\n"
        f"🏢 *Employer:*   {v(data.get('employer'))}\n"
        f"💼 *Role:*       {v(data.get('role'))}\n"
        f"💰 *Wage:*       {v(data.get('wage'))}\n"
        f"📅 *Start:*      {v(data.get('start_date'))}\n"
        f"📅 *End:*        {v(data.get('end_date'))}\n\n"
        f"Use /ledger to see all entries or /proof to get your income PDF."
    )
    await status.edit_text(reply, parse_mode="Markdown")
    logger.info(f"Saved entry {entry.id} for user {tg_user.id}")