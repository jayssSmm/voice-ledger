from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from app.bot.handlers.commands import cmd_start, cmd_ledger, cmd_proof
from app.bot.handlers.voice import handle_voice

def build_bot(token: str):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start",  cmd_start))
    app.add_handler(CommandHandler("help",   cmd_start))
    app.add_handler(CommandHandler("ledger", cmd_ledger))
    app.add_handler(CommandHandler("proof",  cmd_proof))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    return app