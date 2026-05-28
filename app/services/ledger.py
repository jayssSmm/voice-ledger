from sqlalchemy.orm import Session
from app.models.user import TelegramUser
from app.models.entry import LedgerEntry

def upsert_user(db: Session, user_id: int, username: str, full_name: str) -> TelegramUser:
    user = db.get(TelegramUser, user_id)
    if not user:
        user = TelegramUser(id=user_id, username=username, full_name=full_name)
        db.add(user)
        db.commit()
    return user

def save_entry(db: Session, user_id: int, data: dict, transcript: str) -> LedgerEntry:
    entry = LedgerEntry(
        user_id        = user_id,
        employer       = data.get("employer"),
        role           = data.get("role"),
        wage           = data.get("wage"),
        start_date     = data.get("start_date"),
        end_date       = data.get("end_date"),
        hours_per_week = data.get("hours_per_week"),
        notes          = data.get("notes"),
        raw_transcript = transcript,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def get_entries(db: Session, user_id: int) -> list[LedgerEntry]:
    return (
        db.query(LedgerEntry)
        .filter(LedgerEntry.user_id == user_id)
        .order_by(LedgerEntry.created_at.desc())
        .all()
    )