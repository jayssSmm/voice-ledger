from app.config import get_config
from app.database import init_db
from app.bot.builder import build_bot
from app.server import start_ping_server

def create_app():

    cfg = get_config()
    init_db(cfg.DATABASE_URL)
    start_ping_server(cfg.PORT)
    return build_bot(cfg.TELEGRAM_TOKEN)