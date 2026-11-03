from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "subscribers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_number", sa.Text(), nullable=False),
        sa.Column("document_type", sa.Text(), nullable=False),
        sa.Column("first_name", sa.Text(), nullable=False),
        sa.Column("last_name", sa.Text(), nullable=False),
        sa.Column("date_of_birth", sa.Date(), nullable=False),
        sa.Column("citizenship", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "document_type IN ('NATIONAL_ID', 'PASSPORT')",
            name="ck_subscribers_document_type",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscribers"),
        sa.UniqueConstraint(
            "document_type",
            "document_number",
            name="uq_subscribers_document_identity",
        ),
    )
    op.create_table(
        "subscriber_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscriber_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("subscriber_code", sa.Text(), nullable=False),
        sa.Column("service_address_id", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("terminated_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'TERMINATED')",
            name="ck_subscriber_accounts_status",
        ),
        sa.CheckConstraint(
            "(status = 'ACTIVE' AND terminated_at IS NULL) OR "
            "(status = 'TERMINATED' AND terminated_at IS NOT NULL)",
            name="ck_subscriber_accounts_termination_state",
        ),
        sa.ForeignKeyConstraint(
            ["subscriber_id"],
            ["subscribers.id"],
            name="fk_subscriber_accounts_subscriber_id_subscribers",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_subscriber_accounts"),
        sa.UniqueConstraint(
            "subscriber_code",
            name="uq_subscriber_accounts_subscriber_code",
        ),
    )
    op.create_index(
        "ix_subscriber_accounts_subscriber_id",
        "subscriber_accounts",
        ["subscriber_id"],
        unique=False,
    )
    op.create_index(
        "uq_subscriber_accounts_active_service_address",
        "subscriber_accounts",
        ["service_address_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_subscriber_accounts_active_service_address",
        table_name="subscriber_accounts",
    )
    op.drop_index(
        "ix_subscriber_accounts_subscriber_id",
        table_name="subscriber_accounts",
    )
    op.drop_table("subscriber_accounts")
    op.drop_table("subscribers")

