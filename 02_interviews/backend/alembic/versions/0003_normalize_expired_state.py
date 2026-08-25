"""normalize the pre-release expired session value"""
from alembic import op
import sqlalchemy as sa

revision = "0003_normalize_expired_state"
down_revision = "0002_federated_identity"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        bind.execute(sa.text("ALTER TYPE sessionstate RENAME TO sessionstate_legacy"))
        bind.execute(sa.text(
            "CREATE TYPE sessionstate AS ENUM "
            "('scheduled', 'active', 'expired-pending-facilitator-action', 'completed')"
        ))
        bind.execute(sa.text(
            "ALTER TABLE interview_sessions ALTER COLUMN state TYPE sessionstate "
            "USING (CASE state::text WHEN 'expired' "
            "THEN 'expired-pending-facilitator-action' ELSE state::text END)::sessionstate"
        ))
        bind.execute(sa.text("DROP TYPE sessionstate_legacy"))
    else:
        bind.execute(sa.text(
            "UPDATE interview_sessions SET state = "
            "'expired-pending-facilitator-action' WHERE state = 'expired'"
        ))


def downgrade():
    pass
