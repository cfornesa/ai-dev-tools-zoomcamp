import os

from sqlalchemy import create_engine, pool
from alembic import context
from app.db import Base
from app import models
config=context.config
target_metadata=Base.metadata
database_url=os.getenv("DATABASE_URL") or config.get_main_option("sqlalchemy.url")
def run_migrations_offline():
    context.configure(url=database_url,target_metadata=target_metadata,literal_binds=True,compare_type=True); context.run_migrations()
def run_migrations_online():
    connectable=create_engine(database_url,poolclass=pool.NullPool)
    with connectable.begin() as connection:
        context.configure(connection=connection,target_metadata=target_metadata,compare_type=True); context.run_migrations()
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()
