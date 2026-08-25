import os
os.environ["DATABASE_URL"] = "sqlite:///./test-interviews.db"
from app.db import Base, engine, SessionLocal
from app.models import AdminUser
from app.security import hash_password
import pytest
from fastapi.testclient import TestClient
from app.main import app, login_attempts, invite_attempts

@pytest.fixture()
def client():
    login_attempts.clear()
    invite_attempts.clear()
    Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
    db=SessionLocal(); db.add(AdminUser(email="admin@example.test",password_hash=hash_password("correct-horse"))); db.commit(); db.close()
    with TestClient(app) as value: yield value
    Base.metadata.drop_all(engine)
