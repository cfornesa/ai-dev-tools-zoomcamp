import os
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

EXPECTED_TABLES = {
    "admin_users",
    "interview_sessions",
    "session_invites",
    "session_participants",
    "session_extensions",
    "scorecard_templates",
    "evaluations",
    "evaluation_scores",
    "evaluation_notes",
    "audit_events",
    "application_users",
    "external_identities",
    "application_sessions",
}

def upgrade_database(url, root):
    cfg=Config(str(root/"alembic.ini")); cfg.set_main_option("script_location",str(root/"alembic")); cfg.set_main_option("sqlalchemy.url",url)
    command.upgrade(cfg,"head")
    return set(inspect(create_engine(url)).get_table_names())

def test_empty_sqlite_database_migrates_to_expected_tables(tmp_path, monkeypatch):
    root=Path(__file__).parents[1]
    monkeypatch.delenv("DATABASE_URL", raising=False)
    names=upgrade_database(f"sqlite:///{tmp_path/'migration.db'}",root)
    assert EXPECTED_TABLES <= names

@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="set TEST_DATABASE_URL to run the PostgreSQL migration test")
def test_empty_database_migrates_to_expected_tables(tmp_path, monkeypatch):
    url=os.environ["TEST_DATABASE_URL"]
    monkeypatch.setenv("DATABASE_URL",url)
    root=Path(__file__).parents[1]
    names=upgrade_database(url,root)
    assert EXPECTED_TABLES <= names
