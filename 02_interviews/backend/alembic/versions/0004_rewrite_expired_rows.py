"""rewrite rows using the canonical expired session value"""
from alembic import op
import sqlalchemy as sa

revision = "0004_rewrite_expired_rows"
down_revision = "0003_normalize_expired_state"
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
