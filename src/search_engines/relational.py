from sqlalchemy import or_
from sqlalchemy.orm import Session
from .base import SearchEngine, SearchResult
from ..database.session import SessionLocal


class RelationalSearchEngine(SearchEngine):
    def __init__(self):
        self._db: Session | None = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def search(self, query: str, top_k: int = 10, **kwargs) -> list[SearchResult]:
        results = []
        results.extend(self._search_employees(query, top_k))
        results.extend(self._search_departments(query, top_k))
        results.extend(self._search_projects(query, top_k))
        results.extend(self._search_customers(query, top_k))
        results.extend(self._search_products(query, top_k))
        results.extend(self._search_documents(query, top_k))
        return results[:top_k]

    def _search_employees(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.employee import Employee
        q = f"%{query}%"
        rows = (
            self.db.query(Employee)
            .filter(
                or_(
                    Employee.name.like(q),
                    Employee.email.like(q),
                    Employee.title.like(q),
                )
            )
            .limit(top_k)
            .all()
        )
        return [
            SearchResult(
                source="relational_db",
                title=f"员工: {r.name}",
                snippet=f"{r.title} | 部门ID:{r.department_id} | 邮箱:{r.email} | 状态:{r.status}",
                score=0.9,
                metadata={"table": "employees", "id": r.id, "name": r.name, "title": r.title, "department_id": r.department_id},
            )
            for r in rows
        ]

    def _search_departments(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.employee import Department
        q = f"%{query}%"
        rows = self.db.query(Department).filter(Department.name.like(q)).limit(top_k).all()
        return [
            SearchResult(
                source="relational_db",
                title=f"部门: {r.name}",
                snippet=r.description or "",
                score=0.85,
                metadata={"table": "departments", "id": r.id, "name": r.name},
            )
            for r in rows
        ]

    def _search_projects(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.project import Project
        q = f"%{query}%"
        rows = (
            self.db.query(Project)
            .filter(or_(Project.name.like(q), Project.description.like(q)))
            .limit(top_k)
            .all()
        )
        return [
            SearchResult(
                source="relational_db",
                title=f"项目: {r.name}",
                snippet=f"状态:{r.status} | 优先级:{r.priority} | 预算:{r.budget}",
                score=0.85,
                metadata={"table": "projects", "id": r.id, "name": r.name, "status": r.status},
            )
            for r in rows
        ]

    def _search_customers(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.customer import Customer
        q = f"%{query}%"
        rows = (
            self.db.query(Customer)
            .filter(or_(Customer.name.like(q), Customer.industry.like(q)))
            .limit(top_k)
            .all()
        )
        return [
            SearchResult(
                source="relational_db",
                title=f"客户: {r.name}",
                snippet=f"行业:{r.industry} | 联系人:{r.contact_person} | 状态:{r.status}",
                score=0.85,
                metadata={"table": "customers", "id": r.id, "name": r.name},
            )
            for r in rows
        ]

    def _search_products(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.customer import Product
        q = f"%{query}%"
        rows = (
            self.db.query(Product)
            .filter(or_(Product.name.like(q), Product.category.like(q)))
            .limit(top_k)
            .all()
        )
        return [
            SearchResult(
                source="relational_db",
                title=f"产品: {r.name}",
                snippet=f"类别:{r.category} | 单价:{r.unit_price} | 库存:{r.stock_quantity}",
                score=0.85,
                metadata={"table": "products", "id": r.id, "name": r.name},
            )
            for r in rows
        ]

    def _search_documents(self, query: str, top_k: int) -> list[SearchResult]:
        from ..models.document import Document
        q = f"%{query}%"
        rows = (
            self.db.query(Document)
            .filter(or_(Document.title.like(q), Document.content.like(q)))
            .limit(top_k)
            .all()
        )
        return [
            SearchResult(
                source="relational_db",
                title=f"文档: {r.title}",
                snippet=(r.content or "")[:200],
                score=0.8,
                metadata={"table": "documents", "id": r.id, "doc_type": r.doc_type},
            )
            for r in rows
        ]


relational_engine = RelationalSearchEngine()
