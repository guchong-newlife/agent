#!/usr/bin/env python3
"""Generates synthetic Git repositories with mock enterprise code."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REPOS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "mock_repos")

MOCK_REPOS = {
    "enterprise-api": {
        "files": {
            "main.py": '''
from fastapi import FastAPI, Depends, HTTPException
from app.auth import authenticate_user, create_token, get_current_user
from app.database import get_db, Session
from app.models import User, Order, Project

app = FastAPI(title="Enterprise API", version="2.1.0")

@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """Get user by ID. Requires authentication."""
    result = db.query(User).filter(User.id == user_id).first()
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result.to_dict()

@app.get("/api/orders")
async def list_orders(status: str = None, db: Session = Depends(get_db)):
    """List orders with optional status filter."""
    query = db.query(Order)
    if status:
        query = query.filter(Order.status == status)
    return [o.to_dict() for o in query.limit(100).all()]

@app.get("/api/projects")
async def list_projects(department: str = None, db: Session = Depends(get_db)):
    """List projects, optionally filtered by department."""
    query = db.query(Project)
    if department:
        query = query.join(Project.department).filter(Project.department.has(name=department))
    return [p.to_dict() for p in query.all()]

@app.post("/api/orders")
async def create_order(order_data: dict, db: Session = Depends(get_db)):
    """Create a new order."""
    order = Order(**order_data)
    db.add(order)
    db.commit()
    return {"id": order.id, "status": "created"}
''',
            "auth.py": '''
import jwt
import hashlib
from datetime import datetime, timedelta
from app.config import SECRET_KEY, TOKEN_EXPIRE_HOURS

def hash_password(password: str) -> str:
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()

def verify_password(password: str, hashed: str) -> bool:
    salt_hex, key_hex = hashed.split(":")
    salt = bytes.fromhex(salt_hex)
    key = bytes.fromhex(key_hex)
    new_key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return new_key.hex() == key_hex

def create_token(user_id: int) -> str:
    payload = {"user_id": user_id, "exp": datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)}
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def authenticate_user(username: str, password: str):
    """Authenticate user and return token."""
    from app.database import get_user_by_username
    user = get_user_by_username(username)
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return create_token(user.id)
''',
            "config.py": '''
import os

SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
TOKEN_EXPIRE_HOURS = int(os.environ.get("TOKEN_EXPIRE_HOURS", "24"))
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///enterprise.db")
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
MAX_ORDER_ITEMS = 100
DEFAULT_PAGE_SIZE = 20
''',
            "models.py": '''
from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100))
    department = Column(String(100))
    role = Column(String(20), default="user")
    password_hash = Column(String(200))

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    customer_name = Column(String(100))
    total_amount = Column(Float)
    status = Column(String(20), default="pending")
    created_by = Column(Integer, ForeignKey("users.id"))

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    name = Column(String(200))
    status = Column(String(20))
    department_id = Column(Integer)
    budget = Column(Float)
''',
        }
    },
    "data-pipeline": {
        "files": {
            "etl_main.py": '''
import logging
from pipeline.extractors import DBExtractor, APIExtractor
from pipeline.transformers import DataCleaner, Aggregator
from pipeline.loaders import DataWarehouseLoader
from pipeline.config import PIPELINE_CONFIG

logger = logging.getLogger("pipeline.etl")

class ETLPipeline:
    def __init__(self, config=PIPELINE_CONFIG):
        self.config = config
        self.extractor = DBExtractor(config["source_db"])
        self.api_extractor = APIExtractor(config["api_endpoints"])
        self.cleaner = DataCleaner()
        self.aggregator = Aggregator()
        self.loader = DataWarehouseLoader(config["target_dw"])

    def run(self):
        logger.info("Starting ETL pipeline...")
        raw_data = self.extractor.extract_all()
        api_data = self.api_extractor.fetch_all()
        combined = raw_data + api_data

        cleaned = self.cleaner.process(combined)
        logger.info(f"Cleaned {len(cleaned)} records")

        aggregated = self.aggregator.aggregate(cleaned, self.config["agg_rules"])
        logger.info(f"Aggregated into {len(aggregated)} groups")

        self.loader.load(aggregated)
        logger.info("ETL pipeline completed successfully")

class DataCleaner:
    def process(self, data):
        return [self.clean_record(r) for r in data if self.is_valid(r)]

    def clean_record(self, record):
        record["name"] = record.get("name", "").strip()
        record["amount"] = float(record.get("amount", 0))
        if record["amount"] < 0:
            logger.warning(f"Negative amount detected: {record['name']}")
            record["amount"] = 0
        return record

    def is_valid(self, record):
        return record.get("id") is not None
''',
            "config.py": '''
PIPELINE_CONFIG = {
    "source_db": {
        "url": "postgresql://localhost:5432/enterprise",
        "tables": ["customers", "orders", "products", "logs"],
        "batch_size": 1000,
        "max_retries": 3,
        "timeout_seconds": 30,
    },
    "api_endpoints": [
        {"url": "https://api.internal/crm/v2/contacts", "method": "GET", "auth": "bearer"},
        {"url": "https://api.internal/erp/v1/inventory", "method": "GET", "auth": "bearer"},
    ],
    "target_dw": {
        "url": "clickhouse://dw.internal:9000/analytics",
        "table_prefix": "etl_",
        "partition_by": "date",
    },
    "agg_rules": {
        "daily_sales": {"group_by": ["date", "product_id"], "agg": {"amount": "sum"}},
        "customer_activity": {"group_by": ["customer_id"], "agg": {"orders": "count"}},
    },
}
''',
        }
    },
}


def build_repos():
    import subprocess
    os.makedirs(REPOS_DIR, exist_ok=True)

    for repo_name, repo_data in MOCK_REPOS.items():
        repo_path = os.path.join(REPOS_DIR, repo_name)
        os.makedirs(repo_path, exist_ok=True)

        # Create file structure
        for file_path, content in repo_data["files"].items():
            full_path = os.path.join(repo_path, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")

        # Initialize git repo
        subprocess.run(["git", "init"], cwd=repo_path, capture_output=True)
        subprocess.run(["git", "add", "-A"], cwd=repo_path, capture_output=True)
        subprocess.run(
            ["git", "-c", "user.name=DevBot", "-c", "user.email=bot@enterprise.local",
             "commit", "-m", "Initial commit: mock enterprise project"],
            cwd=repo_path, capture_output=True,
        )

        print(f"Created mock repo: {repo_name} ({repo_path})")


if __name__ == "__main__":
    build_repos()
    print("\nMock repositories created successfully!")
