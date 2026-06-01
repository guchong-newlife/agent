from sqlalchemy.orm import Session
from sqlalchemy import or_
from ..database.session import SessionLocal
from ..models.customer import Customer, Product, Order, OrderItem
from ..models.employee import Employee


class CRMSystem:
    def search_customers(self, name: str = "", industry: str = "", top_k: int = 10) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Customer)
            if name:
                q = q.filter(Customer.name.contains(name))
            if industry:
                q = q.filter(Customer.industry.contains(industry))
            rows = q.limit(top_k).all()
            return [{
                "id": r.id, "name": r.name, "industry": r.industry,
                "contact_person": r.contact_person, "phone": r.phone,
                "email": r.email, "status": r.status,
                "customer_since": str(r.customer_since),
            } for r in rows]
        finally:
            db.close()

    def get_customer_orders(self, customer_id: int) -> list[dict]:
        db = SessionLocal()
        try:
            orders = db.query(Order).filter(Order.customer_id == customer_id).all()
            result = []
            for o in orders:
                sales_rep = db.query(Employee).filter(Employee.id == o.sales_rep_id).first()
                items = db.query(OrderItem).filter(OrderItem.order_id == o.id).all()
                result.append({
                    "id": o.id, "order_date": str(o.order_date), "status": o.status,
                    "total_amount": o.total_amount, "payment_status": o.payment_status,
                    "sales_rep": sales_rep.name if sales_rep else None,
                    "item_count": len(items),
                })
            return result
        finally:
            db.close()

    def search_products(self, name: str = "", category: str = "", top_k: int = 10) -> list[dict]:
        db = SessionLocal()
        try:
            q = db.query(Product)
            if name:
                q = q.filter(Product.name.contains(name))
            if category:
                q = q.filter(Product.category.contains(category))
            rows = q.limit(top_k).all()
            return [{
                "id": r.id, "name": r.name, "sku": r.sku, "category": r.category,
                "unit_price": r.unit_price, "stock_quantity": r.stock_quantity,
            } for r in rows]
        finally:
            db.close()

    def get_sales_rep_performance(self, rep_id: int) -> dict:
        db = SessionLocal()
        try:
            orders = db.query(Order).filter(Order.sales_rep_id == rep_id).all()
            total_sales = sum(o.total_amount for o in orders if o.status != "cancelled")
            return {
                "rep_id": rep_id,
                "total_orders": len(orders),
                "total_sales": round(total_sales, 2),
                "completed_orders": sum(1 for o in orders if o.status == "delivered"),
            }
        finally:
            db.close()


crm_system = CRMSystem()
