"""add settings versions and findings generations

Revision ID: 0007_settings_findings_gen
Revises: 0006_add_job_run_controls
Create Date: 2026-03-25
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0007_settings_findings_gen"
down_revision = "0006_add_job_run_controls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "settings_versions",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("fingerprint", sa.Text(), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_settings_versions_created_at",
        "settings_versions",
        ["created_at"],
    )
    op.create_index(
        "idx_settings_versions_fingerprint",
        "settings_versions",
        ["fingerprint"],
    )

    op.create_table(
        "findings_generations",
        sa.Column("id", sa.Text(), nullable=False),
        sa.Column("generation_id", sa.Text(), nullable=False),
        sa.Column("finding_type", sa.Text(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("computed_by_job_id", sa.Text(), nullable=True),
        sa.Column("settings_version_id", sa.Text(), nullable=True),
        sa.Column("settings_fingerprint", sa.Text(), nullable=False),
        sa.Column("detector_code_version", sa.Text(), nullable=False),
        sa.Column("source_click_watermark", sa.DateTime(), nullable=True),
        sa.Column("source_conversion_watermark", sa.DateTime(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=False),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_findings_generations_type_date_current",
        "findings_generations",
        ["finding_type", "target_date", "is_current"],
    )
    op.create_index(
        "idx_findings_generations_generation_id",
        "findings_generations",
        ["generation_id"],
    )
    op.create_index(
        "idx_findings_generations_settings_version",
        "findings_generations",
        ["settings_version_id"],
    )

    op.execute(
        """
        INSERT INTO settings_versions (id, fingerprint, snapshot_json, created_at)
        SELECT
            md5(COALESCE((SELECT jsonb_object_agg(key, value::jsonb ORDER BY key)::text FROM app_settings), '{}')),
            md5(COALESCE((SELECT jsonb_object_agg(key, value::jsonb ORDER BY key)::text FROM app_settings), '{}')),
            COALESCE((SELECT jsonb_object_agg(key, value::jsonb ORDER BY key)::text FROM app_settings), '{}'),
            COALESCE((SELECT MAX(updated_at) FROM app_settings), NOW())
        WHERE EXISTS (SELECT 1 FROM app_settings)
        """
    )

    op.execute(
        """
        INSERT INTO findings_generations (
            id,
            generation_id,
            finding_type,
            target_date,
            computed_by_job_id,
            settings_version_id,
            settings_fingerprint,
            detector_code_version,
            source_click_watermark,
            source_conversion_watermark,
            row_count,
            is_current,
            created_at
        )
        SELECT
            md5('click|' || COALESCE(generation_id, 'legacy-click-' || TO_CHAR(date, 'YYYYMMDD')) || '|' || date::text),
            COALESCE(generation_id, 'legacy-click-' || TO_CHAR(date, 'YYYYMMDD')),
            'click',
            date,
            MAX(computed_by_job_id),
            NULL,
            COALESCE(MAX(rule_version), 'legacy'),
            'legacy',
            MAX(source_click_watermark),
            MAX(source_conversion_watermark),
            COUNT(*),
            TRUE,
            COALESCE(MAX(computed_at), NOW())
        FROM suspicious_click_findings
        WHERE is_current = TRUE
        GROUP BY date, COALESCE(generation_id, 'legacy-click-' || TO_CHAR(date, 'YYYYMMDD'))
        """
    )

    op.execute(
        """
        INSERT INTO findings_generations (
            id,
            generation_id,
            finding_type,
            target_date,
            computed_by_job_id,
            settings_version_id,
            settings_fingerprint,
            detector_code_version,
            source_click_watermark,
            source_conversion_watermark,
            row_count,
            is_current,
            created_at
        )
        SELECT
            md5('conversion|' || COALESCE(generation_id, 'legacy-conversion-' || TO_CHAR(date, 'YYYYMMDD')) || '|' || date::text),
            COALESCE(generation_id, 'legacy-conversion-' || TO_CHAR(date, 'YYYYMMDD')),
            'conversion',
            date,
            MAX(computed_by_job_id),
            NULL,
            COALESCE(MAX(rule_version), 'legacy'),
            'legacy',
            MAX(source_click_watermark),
            MAX(source_conversion_watermark),
            COUNT(*),
            TRUE,
            COALESCE(MAX(computed_at), NOW())
        FROM suspicious_conversion_findings
        WHERE is_current = TRUE
        GROUP BY date, COALESCE(generation_id, 'legacy-conversion-' || TO_CHAR(date, 'YYYYMMDD'))
        """
    )

    op.alter_column("findings_generations", "is_current", server_default=None)


def downgrade() -> None:
    op.drop_index("idx_findings_generations_settings_version", table_name="findings_generations")
    op.drop_index("idx_findings_generations_generation_id", table_name="findings_generations")
    op.drop_index("idx_findings_generations_type_date_current", table_name="findings_generations")
    op.drop_table("findings_generations")
    op.drop_index("idx_settings_versions_fingerprint", table_name="settings_versions")
    op.drop_index("idx_settings_versions_created_at", table_name="settings_versions")
    op.drop_table("settings_versions")
