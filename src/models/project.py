from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    name = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(30), default="planning")  # planning, in_progress, delayed, completed, cancelled
    start_date = Column(Date)
    end_date = Column(Date)
    manager_id = Column(Integer, ForeignKey("employees.id"))
    department_id = Column(Integer, ForeignKey("departments.id"))
    budget = Column(Float)
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    manager = relationship("Employee", foreign_keys=[manager_id])
    tasks = relationship("Task", back_populates="project")


class Task(Base, TimestampMixin):
    __tablename__ = "tasks"

    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(String(30), default="todo")  # todo, in_progress, review, done, blocked
    priority = Column(String(20), default="medium")
    project_id = Column(Integer, ForeignKey("projects.id"))
    assignee_id = Column(Integer, ForeignKey("employees.id"))
    due_date = Column(Date)
    estimated_hours = Column(Float)
    actual_hours = Column(Float)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Employee", foreign_keys=[assignee_id])
