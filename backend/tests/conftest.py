import os

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-readysafe-123456789"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import User
from app.security import hash_password


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def _drop_all_for_sqlite():
    with engine.connect() as connection:
        connection.exec_driver_sql("PRAGMA foreign_keys=OFF")
        Base.metadata.drop_all(bind=connection)
        connection.exec_driver_sql("PRAGMA foreign_keys=ON")


@pytest.fixture(autouse=True)
def reset_database():
    _drop_all_for_sqlite()
    Base.metadata.create_all(bind=engine)
    yield
    _drop_all_for_sqlite()


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user():
    with SessionLocal() as db:
        user = User(
            name="Admin User",
            email="admin@example.com",
            password_hash=hash_password("AdminPass123!"),
            is_admin=True,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


@pytest.fixture
def normal_user():
    with SessionLocal() as db:
        user = User(
            name="Shopper User",
            email="shopper@example.com",
            password_hash=hash_password("ShopperPass123!"),
            is_admin=False,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user.id


def login(client, email: str, password: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def admin_headers(client, admin_user):
    return login(client, "admin@example.com", "AdminPass123!")


@pytest.fixture
def normal_headers(client, normal_user):
    return login(client, "shopper@example.com", "ShopperPass123!")
