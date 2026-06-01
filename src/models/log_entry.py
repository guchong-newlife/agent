from sqlalchemy import Column, Integer, String, DateTime, Text
from .base import Base, TimestampMixin


class LogEntry(Base, TimestampMixin):
    __tablename__ = "log_entries"

    timestamp = Column(DateTime, nullable=False, index=True)
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger_name = Column(String(100))
    module = Column(String(100))
    function_name = Column(String(100))
    message = Column(Text, nullable=False)
    traceback = Column(Text, nullable=True)
    user_id = Column(Integer, nullable=True)
    request_id = Column(String(64), nullable=True, index=True)
    extra_data = Column(Text)  # JSON string
