"""add audit history tables

Revision ID: 9b3f1c2d4e6a
Revises: 6df106850af3
Create Date: 2026-01-07

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9b3f1c2d4e6a"
down_revision: str | None = "6df106850af3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_revision",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("actor_type", sa.String(), nullable=True),
        sa.Column("actor_id", sa.String(), nullable=True),
        sa.Column("source", sa.String(), nullable=True),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_revision_created_at"),
        "audit_revision",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_revision_entity_id"),
        "audit_revision",
        ["entity_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_revision_entity_type"),
        "audit_revision",
        ["entity_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_revision_event_type"),
        "audit_revision",
        ["event_type"],
        unique=False,
    )
    op.create_index(
        op.f("ix_audit_revision_id"), "audit_revision", ["id"], unique=False
    )

    op.create_table(
        "audit_change",
        sa.Column("id", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("revision_id", sa.String(length=32), nullable=False),
        sa.Column("field", sa.String(), nullable=False),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["revision_id"], ["audit_revision.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_audit_change_created_at"), "audit_change", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_audit_change_field"), "audit_change", ["field"], unique=False
    )
    op.create_index(op.f("ix_audit_change_id"), "audit_change", ["id"], unique=False)
    op.create_index(
        op.f("ix_audit_change_revision_id"),
        "audit_change",
        ["revision_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_change_revision_id"), table_name="audit_change")
    op.drop_index(op.f("ix_audit_change_id"), table_name="audit_change")
    op.drop_index(op.f("ix_audit_change_field"), table_name="audit_change")
    op.drop_index(op.f("ix_audit_change_created_at"), table_name="audit_change")
    op.drop_table("audit_change")

    op.drop_index(op.f("ix_audit_revision_id"), table_name="audit_revision")
    op.drop_index(op.f("ix_audit_revision_event_type"), table_name="audit_revision")
    op.drop_index(op.f("ix_audit_revision_entity_type"), table_name="audit_revision")
    op.drop_index(op.f("ix_audit_revision_entity_id"), table_name="audit_revision")
    op.drop_index(op.f("ix_audit_revision_created_at"), table_name="audit_revision")
    op.drop_table("audit_revision")
