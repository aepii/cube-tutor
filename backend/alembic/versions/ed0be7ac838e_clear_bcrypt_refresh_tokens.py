"""clear bcrypt refresh tokens

Refresh tokens are now stored as sha256(token) instead of a bcrypt hash (4e).
A bcrypt hash can't be converted to sha256, so every existing row is deleted
and users log in again. No schema change: `hashed_token` keeps its name and
its unique index.

Revision ID: ed0be7ac838e
Revises: a92565855791
Create Date: 2026-11-21 15:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ed0be7ac838e"
down_revision: str | Sequence[str] | None = "a92565855791"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Delete every refresh-token row (bcrypt hashes can't be converted)."""
    op.execute("DELETE FROM refreshtoken")


def downgrade() -> None:
    """Leave the data alone: the deleted bcrypt rows can't be restored, and
    sha256 rows simply won't match under the old bcrypt code."""
