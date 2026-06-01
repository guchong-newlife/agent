from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from .base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    name = Column(String(200), nullable=False)
    industry = Column(String(100))
    contact_person = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    customer_since = Column(Date)
    annual_revenue_range = Column(String(50))
    status = Column(String(20), default="active")

    orders = relationship("Order", back_populates="customer")


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True)
    category = Column(String(100))
    unit_price = Column(Float)
    cost = Column(Float)
    stock_quantity = Column(Integer, default=0)
    description = Column(Text)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    customer_id = Column(Integer, ForeignKey("customers.id"))
    order_date = Column(Date)
    status = Column(String(30), default="pending")  # pending, confirmed, shipped, delivered, cancelled
    total_amount = Column(Float)
    sales_rep_id = Column(Integer, ForeignKey("employees.id"))
    payment_status = Column(String(30), default="unpaid")
    shipping_address = Column(Text)

    customer = relationship("Customer", back_populates="orders")
    sales_rep = relationship("Employee", foreign_keys=[sales_rep_id])
    items = relationship("OrderItem", back_populates="order")


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"

    order_id = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Integer, default=1)
    unit_price = Column(Float)
    discount = Column(Float, default=0.0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")
