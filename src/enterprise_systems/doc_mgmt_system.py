from sqlalchemy.orm import Session
from ..database.session import SessionLocal
from ..models.document import Document


class DocMgmtSystem:
    def search_documents(self, title: str = "", doc_type: str = "", department: str = "",
                         top_k: int = 10) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Document)
            if title:
                q = q.filter(Document.title.contains(title))
            if doc_type:
                q = q.filter(Document.doc_type == doc_type)
            if department:
                q = q.filter(Document.department.contains(department))
            rows = q.limit(top_k).all()
            return [{
                "id": r.id, "title": r.title, "doc_type": r.doc_type,
                "department": r.department, "author": r.author,
                "created_date": str(r.created_date), "tags": r.tags,
                "status": r.status, "content": r.content,
            } for r in rows]
        finally:
            db.close()

    def get_documents_by_type(self, doc_type: str) -> list[dict]:
        return self.search_documents(doc_type=doc_type, top_k=50)


doc_mgmt_system = DocMgmtSystem()
