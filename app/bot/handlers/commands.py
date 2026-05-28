# app/bot/handlers/commands.py
from telegram import Update
from telegram.ext import ContextTypes
from app.database import SessionLocal
from app.services.ledger import get_entries
from app.services.pdf import generate_proof_pdf
import os

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to *VoiceLedger*.\n\n"
        "Send me a *voice note* describing your work — employer, wage, dates — "
        "and I'll build your financial identity.\n\n"
        "Commands:\n"
        "/ledger — view all your entries\n"
        "/proof  — download your income proof PDF",
        parse_mode="Markdown",
    )

async def cmd_ledger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    db = SessionLocal()
    try:
        entries = get_entries(db, user_id)
    finally:
        db.close()

    if not entries:
        await update.message.reply_text("No entries yet. Send a voice note to get started.")
        return

    lines = [f"📒 *Your ledger — {len(entries)} entries*\n"]
    for i, e in enumerate(entries, 1):
        lines.append(
            f"*{i}.* {e.employer or '?'} | {e.role or '?'} | {e.wage or '?'}\n"
            f"    {e.start_date or '?'} → {e.end_date or '?'}"
        )
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def cmd_proof(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id  = update.effective_user.id
    tg_user  = update.effective_user
    db = SessionLocal()
    try:
        from app.models.user import TelegramUser
        user    = db.get(TelegramUser, user_id)
        entries = get_entries(db, user_id)
    finally:
        db.close()

    if not entries:
        await update.message.reply_text("No entries to generate proof for. Send a voice note first.")
        return

    status = await update.message.reply_text("⏳ Generating your income proof PDF…")
    pdf_path = generate_proof_pdf(user, entries)
    try:
        with open(pdf_path, "rb") as f:
            await context.bot.send_document(
                chat_id=update.effective_chat.id,
                document=f,
                filename="voiceledger_proof.pdf",
                caption="📄 Your VoiceLedger income proof",
            )
        await status.delete()
    finally:
        os.unlink(pdf_path)