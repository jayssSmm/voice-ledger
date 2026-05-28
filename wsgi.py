import asyncio, logging
from app import create_app

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(name)s | %(message)s", level=logging.INFO)

if __name__ == "__main__":
    asyncio.set_event_loop(asyncio.new_event_loop())
    app = create_app()
    app.run_polling(drop_pending_updates=True)