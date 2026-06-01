from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Department(Base, TimestampMixin):
    __tablename__ = "departments"

    name = Column(String(100), nullable=False)
    parent_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    head_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    description = Column(Text)

    parent = relationship("Department", remote_side="Department.id", backref="children")
    employees = relationship("Employee", back_populates="department", foreign_keys="Employee.department_id")


class Employee(Base, TimestampMixin):
    __tablename__ = "employees"

    name = Column(String(50), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    title = Column(String(100))
    department_id = Column(Integer, ForeignKey("departments.id"))
    manager_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    hire_date = Column(Date)
    salary = Column(Float)
    status = Column(String(20), default="active")  # active, inactive, on_leave

    department = relationship("Department", back_populates="employees", foreign_keys=[department_id])
    manager = relationship("Employee", remote_side="Employee.id", backref="direct_reports")
