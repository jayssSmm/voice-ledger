# app/models/user.py
from sqlalchemy import Column, BigInteger, String, DateTime, func
from app.database import Base

class TelegramUser(Base):
    __tablename__ = "telegram_users"

    id            = Column(BigInteger, primary_key=True)  # telegram user_id
    username      = Column(String(64), nullable=True)
    full_name     = Column(String(128), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())