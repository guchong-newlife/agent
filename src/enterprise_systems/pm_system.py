from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database.session import SessionLocal
from ..models.project import Project, Task
from ..models.employee import Employee


class PMSystem:
    def search_projects(self, name: str = "", status: str = "", top_k: int = 10) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Project)
            if name:
                q = q.filter(Project.name.contains(name))
            if status:
                q = q.filter(Project.status == status)
            rows = q.limit(top_k).all()
            result = []
            for r in rows:
                manager = db.query(Employee).filter(Employee.id == r.manager_id).first()
                task_count = db.query(Task).filter(Task.project_id == r.id).count()
                result.append({
                    "id": r.id, "name": r.name, "description": r.description,
                    "status": r.status, "priority": r.priority,
                    "start_date": str(r.start_date), "end_date": str(r.end_date),
                    "budget": r.budget,
                    "manager": manager.name if manager else None,
                    "task_count": task_count,
                })
            return result
        finally:
            db.close()

    def get_project_tasks(self, project_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.project_id == project_id).all()
            result = []
            for t in tasks:
                assignee = db.query(Employee).filter(Employee.id == t.assignee_id).first()
                result.append({
                    "id": t.id, "title": t.title, "description": t.description,
                    "status": t.status, "priority": t.priority,
                    "assignee": assignee.name if assignee else None,
                    "due_date": str(t.due_date),
                    "estimated_hours": t.estimated_hours,
                    "actual_hours": t.actual_hours,
                })
            return result
        finally:
            db.close()

    def get_team_workload(self, department_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            tasks = (
                db.query(Task)
                .join(Employee, Task.assignee_id == Employee.id)
                .filter(Employee.department_id == department_id, Task.status.in_(["todo", "in_progress"]))
                .all()
            )
            workload = {}
            for t in tasks:
                name = db.query(Employee).filter(Employee.id == t.assignee_id).first().name
                if name not in workload:
                    workload[name] = {"task_count": 0, "total_estimated_hours": 0}
                workload[name]["task_count"] += 1
                workload[name]["total_estimated_hours"] += t.estimated_hours or 0
            return [{"name": k, **v} for k, v in workload.items()]
        finally:
            db.close()


pm_system = PMSystem()
