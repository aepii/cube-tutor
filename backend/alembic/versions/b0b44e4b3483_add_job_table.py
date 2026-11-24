"""job table

24a: the `job` table, source of truth for background jobs (ADR 0008).
A new table only, so the code before it keeps working (expand step).
`status` is VARCHAR + the named check `ck_job_status`, not a Postgres ENUM.
`ix_job_status_updated_at` serves the stale-pending sweeper.

Revision ID: b0b44e4b3483
Revises: 3f1c9d2b7a64
Create Date: 2026-11-22 17:26:09.955925

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "b0b44e4b3483"
down_revision: str | Sequence[str] | None = "3f1c9d2b7a64"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create `job` with its status check and the two indexes."""
    op.create_table(
        "job",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("type", sqlmodel.sql.sqltypes.AutoString(length=100), nullable=False),
        sa.Column(
            "status", sqlmodel.sql.sqltypes.AutoString(length=20), nullable=False
        ),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("finished_at", sa.DateTime(), nullable=True),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'done', 'failed')", name="ck_job_status"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_job_status_updated_at", "job", ["status", "updated_at"], unique=False
    )
    op.create_index(op.f("ix_job_user_id"), "job", ["user_id"], unique=False)


def downgrade() -> None:
    """Drop `job` (and its jobs: nothing else references it)."""
    op.drop_index(op.f("ix_job_user_id"), table_name="job")
    op.drop_index("ix_job_status_updated_at", table_name="job")
    op.drop_table("job")
