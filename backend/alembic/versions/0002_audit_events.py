"""Add audit-event-v0 persistence foundation.

Revision ID: 0002_audit_events
Revises: 0001_initial_schema
Create Date: 2026-06-15
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0002_audit_events"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("event_id", sa.Text(), primary_key=True),
        sa.Column("event_version", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("occurred_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("resource_id", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("decision_support_only", sa.Boolean(), nullable=False),
        sa.Column("safety_boundary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "decision_support_only IS TRUE",
            name="audit_events_decision_support_only_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(safety_boundary) = 'object'",
            name="audit_events_safety_boundary_object_check",
        ),
        sa.CheckConstraint(
            "jsonb_typeof(metadata) = 'object'",
            name="audit_events_metadata_object_check",
        ),
        comment=(
            "Read-only decision-support audit-event-v0 persistence foundation. "
            "No automatic logging, dispatch, activation, or operational control."
        ),
    )
    op.create_index(
        "audit_events_occurred_at_utc_idx",
        "audit_events",
        ["occurred_at_utc"],
    )
    op.create_index("audit_events_event_type_idx", "audit_events", ["event_type"])
    op.create_index(
        "audit_events_resource_idx",
        "audit_events",
        ["resource_type", "resource_id"],
    )
    op.create_index(
        "audit_events_actor_idx",
        "audit_events",
        ["actor_type", "actor_id"],
    )


def downgrade() -> None:
    op.drop_table("audit_events")
