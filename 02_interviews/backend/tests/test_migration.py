import os
from pathlib import Path
import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

@pytest.mark.skipif(not os.getenv("TEST_DATABASE_URL"), reason="set TEST_DATABASE_URL to run the PostgreSQL migration test")
def test_empty_database_migrates_to_expected_tables(tmp_path):
    url=os.environ["TEST_DATABASE_URL"]
    root=Path(__file__).parents[1]
    cfg=Config(str(root/"alembic.ini")); cfg.set_main_option("script_location",str(root/"alembic")); cfg.set_main_option("sqlalchemy.url",url)
    command.upgrade(cfg,"head")
    names=set(inspect(create_engine(url)).get_table_names())
    assert {"admin_users","interview_sessions","session_invites","session_participants","session_extensions","scorecard_templates","evaluations","evaluation_scores","evaluation_notes","audit_events"} <= names
