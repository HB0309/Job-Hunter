"""Initial schema: sources, raw_jobs, job_evaluations, jobs, user_feedback

Revision ID: 001
Revises: None
Create Date: 2026-04-09
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Sources
    op.create_table(
        "sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("config", sa.String(1024), server_default=""),
        sa.Column("enabled", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_fetched_at", sa.DateTime(timezone=True), nullable=True),
    )

    # Raw jobs queue
    op.create_table(
        "raw_jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("sources.id"), nullable=False),
        sa.Column("external_id", sa.String(512), nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(512), server_default=""),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("description_raw", sa.Text(), server_default=""),
        sa.Column("metadata_json", sa.Text(), server_default="{}"),
        sa.Column("processing_status", sa.String(32), server_default="queued"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_raw_jobs_dedup", "raw_jobs", ["source_id", "external_id"], unique=True)
    op.create_index("ix_raw_jobs_status", "raw_jobs", ["processing_status"])

    # Job evaluations (Claude scoring output)
    op.create_table(
        "job_evaluations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_job_id", sa.Integer(), sa.ForeignKey("raw_jobs.id"), unique=True, nullable=False),
        sa.Column("role_family", sa.String(128), server_default=""),
        sa.Column("seniority", sa.String(64), server_default=""),
        sa.Column("early_talent", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("fit_score", sa.Float(), server_default="0"),
        sa.Column("fit_label", sa.String(32), server_default=""),
        sa.Column("keep_in_db", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("needs_user_feedback", sa.Boolean(), server_default=sa.text("false")),
        sa.Column("ats_keywords_json", sa.Text(), server_default="[]"),
        sa.Column("matched_skills_json", sa.Text(), server_default="[]"),
        sa.Column("missing_skills_json", sa.Text(), server_default="[]"),
        sa.Column("reasoning_summary", sa.Text(), server_default=""),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Canonical jobs
    op.create_table(
        "jobs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_job_id", sa.Integer(), sa.ForeignKey("raw_jobs.id"), unique=True, nullable=False),
        sa.Column("evaluation_id", sa.Integer(), sa.ForeignKey("job_evaluations.id"), nullable=True),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("company", sa.String(255), nullable=False),
        sa.Column("location", sa.String(512), server_default=""),
        sa.Column("url", sa.String(1024), nullable=False),
        sa.Column("description", sa.Text(), server_default=""),
        sa.Column("role_family", sa.String(128), server_default=""),
        sa.Column("seniority", sa.String(64), server_default=""),
        sa.Column("fit_score", sa.Float(), server_default="0"),
        sa.Column("status", sa.String(32), server_default="new"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_jobs_status", "jobs", ["status"])

    # User feedback
    op.create_table(
        "user_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("raw_job_id", sa.Integer(), sa.ForeignKey("raw_jobs.id"), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("notes", sa.Text(), server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("user_feedback")
    op.drop_table("jobs")
    op.drop_table("job_evaluations")
    op.drop_table("raw_jobs")
    op.drop_table("sources")
