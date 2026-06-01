from sqlalchemy import Column, Integer, String, Date, Text
from .base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    __tablename__ = "documents"

    title = Column(String(300), nullable=False)
    doc_type = Column(String(50))  # policy, manual, report, spec, meeting_notes
    department = Column(String(100))
    author = Column(String(50))
    created_date = Column(Date)
    tags = Column(String(500))  # JSON string of tags
    file_path = Column(String(500))
    source_system = Column(String(50))
    chunk_count = Column(Integer, default=0)
    status = Column(String(30), default="published")
    content = Column(Text)  # Full document text
