from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database.session import SessionLocal
from ..models.employee import Employee, Department


class HRSystem:
    def search_employees(self, name: str = "", department: str = "", title: str = "",
                         email: str = "", top_k: int = 10) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Employee)
            if name:
                q = q.filter(Employee.name.contains(name))
            if title:
                q = q.filter(Employee.title.contains(title))
            if email:
                q = q.filter(Employee.email.contains(email))
            if department:
                q = q.join(Department, Employee.department_id == Department.id).filter(
                    Department.name.contains(department)
                )
            rows = q.limit(top_k).all()
            return [{
                "id": r.id, "name": r.name, "email": r.email, "phone": r.phone,
                "title": r.title, "department_id": r.department_id,
                "manager_id": r.manager_id, "hire_date": str(r.hire_date),
                "salary": r.salary, "status": r.status,
            } for r in rows]
        finally:
            db.close()

    def get_org_chart(self, department_id: int | None = None) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Department)
            if department_id:
                q = q.filter(Department.id == department_id)
            depts = q.all()
            result = []
            for d in depts:
                emp_count = db.query(Employee).filter(Employee.department_id == d.id).count()
                head = db.query(Employee).filter(Employee.id == d.head_id).first()
                result.append({
                    "id": d.id, "name": d.name, "description": d.description,
                    "head_name": head.name if head else None,
                    "employee_count": emp_count, "parent_id": d.parent_id,
                })
            return result
        finally:
            db.close()

    def get_direct_reports(self, manager_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            rows = db.query(Employee).filter(Employee.manager_id == manager_id).all()
            return [{"id": r.id, "name": r.name, "title": r.title, "department_id": r.department_id} for r in rows]
        finally:
            db.close()

    def get_department_employees(self, department_name: str) -> list[dict]:
        db = SessionLocal()
        try:
            rows = (
                db.query(Employee)
                .join(Department, Employee.department_id == Department.id)
                .filter(Department.name.contains(department_name))
                .all()
            )
            return [{"id": r.id, "name": r.name, "title": r.title, "email": r.email, "status": r.status} for r in rows]
        finally:
            db.close()


hr_system = HRSystem()
