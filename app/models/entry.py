# app/models/entry.py
from sqlalchemy import Column, Integer, BigInteger, String, Numeric, DateTime, ForeignKey, func
from app.database import Base

class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(BigInteger, ForeignKey("telegram_users.id"), nullable=False, index=True)
    employer       = Column(String(256), nullable=True)
    role           = Column(String(128), nullable=True)
    wage           = Column(String(64),  nullable=True)
    start_date     = Column(String(32),  nullable=True)
    end_date       = Column(String(32),  nullable=True)
    hours_per_week = Column(Numeric(5,2), nullable=True)
    notes          = Column(String(512), nullable=True)
    raw_transcript = Column(String(2048), nullable=False)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())