"""durable federated identities and application sessions"""
from alembic import op
import sqlalchemy as sa
revision="0002_federated_identity"; down_revision="0001_initial"; branch_labels=None; depends_on=None
def upgrade():
    op.create_table("application_users",sa.Column("id",sa.String(36),primary_key=True),sa.Column("email",sa.String(320),nullable=False,unique=True),sa.Column("email_verified",sa.Boolean(),nullable=False),sa.Column("role",sa.String(32),nullable=False),sa.Column("status",sa.String(32),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("updated_at",sa.DateTime(timezone=True),nullable=False))
    op.create_table("external_identities",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("application_users.id"),nullable=False),sa.Column("provider",sa.String(32),nullable=False),sa.Column("provider_subject",sa.String(255),nullable=False),sa.Column("provider_email",sa.String(320)),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("last_login_at",sa.DateTime(timezone=True)))
    op.create_index("uq_external_provider_subject","external_identities",["provider","provider_subject"],unique=True)
    op.create_table("application_sessions",sa.Column("id",sa.String(36),primary_key=True),sa.Column("user_id",sa.String(36),sa.ForeignKey("application_users.id"),nullable=False),sa.Column("token_hash",sa.String(64),nullable=False,unique=True),sa.Column("csrf_hash",sa.String(64),nullable=False),sa.Column("created_at",sa.DateTime(timezone=True),nullable=False),sa.Column("expires_at",sa.DateTime(timezone=True),nullable=False),sa.Column("revoked_at",sa.DateTime(timezone=True)),sa.Column("rotated_from",sa.String(36),sa.ForeignKey("application_sessions.id")))
def downgrade():
    op.drop_table("application_sessions");op.drop_index("uq_external_provider_subject",table_name="external_identities");op.drop_table("external_identities");op.drop_table("application_users")
