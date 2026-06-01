from sqlalchemy import Column, Integer, String, DateTime, Text, func
from ..models.base import Base


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    track_name = Column(String(32), nullable=False, index=True)
    fingerprint_id = Column(String(128), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    page_url = Column(String(2048))
    page_title = Column(String(512))
    timestamp = Column(DateTime, nullable=False, index=True)
    payload = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())


class TrackingSession(Base):
    __tablename__ = "tracking_sessions"

    session_id = Column(String(64), primary_key=True)
    fingerprint_id = Column(String(128), nullable=False, index=True)
    first_page_url = Column(String(2048))
    referrer = Column(String(2048))
    user_agent = Column(String(512))
    browser_info = Column(Text)
    screen_info = Column(Text)
    started_at = Column(DateTime, nullable=False)
    ended_at = Column(DateTime)
    event_count = Column(Integer, default=0)
