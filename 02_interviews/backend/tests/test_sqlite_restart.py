from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import AdminUser


def test_sqlite_profile_retains_data_after_engine_restart(tmp_path):
    database = tmp_path / "restart.db"
    url = f"sqlite:///{database}"
    first = create_engine(url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(first)
    Session = sessionmaker(bind=first)
    with Session.begin() as db:
        db.add(AdminUser(email="restart@example.test", password_hash="hash"))
    first.dispose()

    second = create_engine(url, connect_args={"check_same_thread": False})
    with sessionmaker(bind=second)() as db:
        assert db.query(AdminUser).filter_by(email="restart@example.test").one().email == "restart@example.test"
    assert "admin_users" in inspect(second).get_table_names()
    second.dispose()
