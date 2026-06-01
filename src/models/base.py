from datetime import datetime
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
