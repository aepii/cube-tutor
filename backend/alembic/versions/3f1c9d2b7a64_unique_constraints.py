"""unique constraints on algorithmcase, algorithmsolution, useralgorithm

4f: the schema, not lookups, rules out duplicate cases, solutions and per-user
link rows. `PUT /v1/algs/{id}/favorite|learn` upserts on
`uq_useralgorithm_user_algorithm`.

No dedupe step: if duplicates exist, the upgrade fails loudly instead of
silently choosing which row to keep.

Revision ID: 3f1c9d2b7a64
Revises: ed0be7ac838e
Create Date: 2026-11-21 18:00:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f1c9d2b7a64"
down_revision: str | Sequence[str] | None = "ed0be7ac838e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add the three named unique constraints."""
    op.create_unique_constraint(
        "uq_algorithmcase_subset_name_subgroup",
        "algorithmcase",
        ["subset", "name", "subgroup"],
    )
    op.create_unique_constraint(
        "uq_algorithmsolution_case_solution",
        "algorithmsolution",
        ["case_id", "solution"],
    )
    op.create_unique_constraint(
        "uq_useralgorithm_user_algorithm",
        "useralgorithm",
        ["user_id", "algorithm_id"],
    )


def downgrade() -> None:
    """Drop the three constraints (data is untouched)."""
    op.drop_constraint(
        "uq_useralgorithm_user_algorithm", "useralgorithm", type_="unique"
    )
    op.drop_constraint(
        "uq_algorithmsolution_case_solution", "algorithmsolution", type_="unique"
    )
    op.drop_constraint(
        "uq_algorithmcase_subset_name_subgroup", "algorithmcase", type_="unique"
    )
