"""Initial database schema baseline.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-08
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "spot_prices",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("price_area", sa.Text(), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("price_eur_per_mwh", sa.Numeric(12, 4), nullable=False),
        sa.Column("price_dkk_per_mwh", sa.Numeric(12, 4), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("price_area IN ('DK1', 'DK2')", name="spot_prices_price_area_check"),
        sa.UniqueConstraint("source", "source_record_id", name="spot_prices_unique_source_record"),
        sa.UniqueConstraint(
            "price_area",
            "timestamp_utc",
            "source",
            name="spot_prices_unique_area_timestamp_source",
        ),
        comment="Read-only decision-support storage for DK1/DK2 electricity spot prices.",
    )
    op.create_index("spot_prices_timestamp_utc_idx", "spot_prices", ["timestamp_utc"])
    op.create_index(
        "spot_prices_price_area_timestamp_utc_idx",
        "spot_prices",
        ["price_area", "timestamp_utc"],
    )
    op.create_index("spot_prices_source_idx", "spot_prices", ["source"])
    op.alter_column(
        "spot_prices",
        "price_area",
        comment="Danish bidding zone: DK1 or DK2.",
        existing_type=sa.Text(),
    )
    op.alter_column(
        "spot_prices",
        "timestamp_utc",
        comment="UTC timestamp for the observed market interval.",
        existing_type=sa.DateTime(timezone=True),
    )
    op.alter_column(
        "spot_prices",
        "price_eur_per_mwh",
        comment="Spot price in EUR/MWh using internal MWh-based market units.",
        existing_type=sa.Numeric(12, 4),
    )
    op.alter_column(
        "spot_prices",
        "price_dkk_per_mwh",
        comment="Spot price in DKK/MWh using internal MWh-based market units.",
        existing_type=sa.Numeric(12, 4),
    )

    op.create_table(
        "power_balance",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("price_area", sa.Text(), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("production_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("consumption_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("wind_onshore_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("wind_offshore_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("solar_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("exchange_net_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint("price_area IN ('DK1', 'DK2')", name="power_balance_price_area_check"),
        sa.UniqueConstraint("source", "source_record_id", name="power_balance_unique_source_record"),
        sa.UniqueConstraint(
            "price_area",
            "timestamp_utc",
            "source",
            name="power_balance_unique_area_timestamp_source",
        ),
        comment=(
            "Read-only decision-support storage for production, consumption, exchange, "
            "and generation measurements."
        ),
    )
    op.create_index("power_balance_timestamp_utc_idx", "power_balance", ["timestamp_utc"])
    op.create_index(
        "power_balance_price_area_timestamp_utc_idx",
        "power_balance",
        ["price_area", "timestamp_utc"],
    )
    op.create_index("power_balance_source_idx", "power_balance", ["source"])
    op.alter_column(
        "power_balance",
        "exchange_net_mw",
        comment="Net exchange in MW. Final sign convention is pending dataset mapping.",
        existing_type=sa.Numeric(14, 4),
    )

    op.create_table(
        "weather_observations",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("location_id", sa.Text(), nullable=False),
        sa.Column("timestamp_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wind_speed_mps", sa.Numeric(10, 4), nullable=True),
        sa.Column("wind_direction_deg", sa.Numeric(7, 3), nullable=True),
        sa.Column("temperature_c", sa.Numeric(7, 3), nullable=True),
        sa.Column("cloud_cover_pct", sa.Numeric(7, 3), nullable=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("source_record_id", sa.Text(), nullable=True),
        sa.Column(
            "ingested_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "wind_direction_deg IS NULL OR (wind_direction_deg >= 0 AND wind_direction_deg <= 360)",
            name="weather_observations_wind_direction_deg_check",
        ),
        sa.CheckConstraint(
            "cloud_cover_pct IS NULL OR (cloud_cover_pct >= 0 AND cloud_cover_pct <= 100)",
            name="weather_observations_cloud_cover_pct_check",
        ),
        sa.UniqueConstraint(
            "source",
            "source_record_id",
            name="weather_observations_unique_source_record",
        ),
        sa.UniqueConstraint(
            "location_id",
            "timestamp_utc",
            "source",
            name="weather_observations_unique_location_timestamp_source",
        ),
        comment="Read-only decision-support storage for weather features relevant to forecasting.",
    )
    op.create_index(
        "weather_observations_timestamp_utc_idx",
        "weather_observations",
        ["timestamp_utc"],
    )
    op.create_index(
        "weather_observations_location_timestamp_utc_idx",
        "weather_observations",
        ["location_id", "timestamp_utc"],
    )
    op.create_index("weather_observations_source_idx", "weather_observations", ["source"])
    op.alter_column(
        "weather_observations",
        "location_id",
        comment="Stable identifier for a weather station, grid cell, or mapped forecast location.",
        existing_type=sa.Text(),
    )

    op.create_table(
        "surplus_risk_forecasts",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "price_area",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "forecast_created_at_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("forecast_start_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("forecast_end_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_level", sa.Text(), nullable=False),
        sa.Column("confidence_score", sa.Numeric(5, 4), nullable=False),
        sa.Column("expected_surplus_mw", sa.Numeric(14, 4), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=False),
        sa.Column("economic_potential_dkk", sa.Numeric(14, 2), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=False),
        sa.Column("model_version", sa.Text(), nullable=False),
        sa.Column("explanation_text", sa.Text(), nullable=True),
        sa.Column("input_data_window_start_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("input_data_window_end_utc", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "price_area IN ('DK1', 'DK2')",
            name="surplus_risk_forecasts_price_area_check",
        ),
        sa.CheckConstraint(
            "risk_level IN ('low', 'medium', 'high')",
            name="surplus_risk_forecasts_risk_level_check",
        ),
        sa.CheckConstraint(
            "confidence_score >= 0 AND confidence_score <= 1",
            name="surplus_risk_forecasts_confidence_score_check",
        ),
        sa.CheckConstraint(
            "forecast_start_utc < forecast_end_utc",
            name="surplus_risk_forecasts_window_check",
        ),
        sa.CheckConstraint(
            "input_data_window_start_utc IS NULL OR "
            "input_data_window_end_utc IS NULL OR "
            "input_data_window_start_utc <= input_data_window_end_utc",
            name="surplus_risk_forecasts_input_window_check",
        ),
        comment="Read-only decision-support model outputs for human review; not operational dispatch.",
    )
    op.create_index(
        "surplus_risk_forecasts_created_at_idx",
        "surplus_risk_forecasts",
        ["forecast_created_at_utc"],
    )
    op.create_index(
        "surplus_risk_forecasts_price_area_window_idx",
        "surplus_risk_forecasts",
        ["price_area", "forecast_start_utc", "forecast_end_utc"],
    )
    op.create_index(
        "surplus_risk_forecasts_window_idx",
        "surplus_risk_forecasts",
        ["forecast_start_utc", "forecast_end_utc"],
    )
    op.create_index(
        "surplus_risk_forecasts_model_idx",
        "surplus_risk_forecasts",
        ["model_name", "model_version"],
    )
    op.alter_column(
        "surplus_risk_forecasts",
        "recommended_action",
        comment=(
            "Human-readable recommendation text only. This is not a control command "
            "or activation instruction."
        ),
        existing_type=sa.Text(),
    )
    op.alter_column(
        "surplus_risk_forecasts",
        "explanation_text",
        comment="Optional explanation/reporting text. LLMs may support explanation only, not primary forecasting.",
        existing_type=sa.Text(),
    )

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("dataset_name", sa.Text(), nullable=False),
        sa.Column("started_at_utc", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at_utc", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.Text(), nullable=False),
        sa.Column(
            "records_processed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint("records_processed >= 0", name="ingestion_runs_records_processed_check"),
        sa.CheckConstraint(
            "finished_at_utc IS NULL OR started_at_utc <= finished_at_utc",
            name="ingestion_runs_time_check",
        ),
        comment="Audit trail for ingestion jobs. No ingestion runtime is implemented in v0.1 schema baseline.",
    )
    op.create_index("ingestion_runs_started_at_idx", "ingestion_runs", ["started_at_utc"])
    op.create_index("ingestion_runs_source_idx", "ingestion_runs", ["source"])
    op.create_index(
        "ingestion_runs_source_dataset_idx",
        "ingestion_runs",
        ["source", "dataset_name"],
    )
    op.create_index("ingestion_runs_status_idx", "ingestion_runs", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=True), primary_key=True),
        sa.Column(
            "event_time_utc",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("actor_type", sa.Text(), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=True),
        sa.Column("entity_type", sa.Text(), nullable=True),
        sa.Column("entity_id", sa.Text(), nullable=True),
        sa.Column(
            "details_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.CheckConstraint(
            "jsonb_typeof(details_json) = 'object'",
            name="audit_log_details_json_object_check",
        ),
        comment="Audit trail for user-visible forecasts, explanations, and human review actions in read-only v0.1.",
    )
    op.create_index("audit_log_event_time_idx", "audit_log", ["event_time_utc"])
    op.create_index("audit_log_event_type_idx", "audit_log", ["event_type"])
    op.create_index("audit_log_actor_idx", "audit_log", ["actor_type", "actor_id"])
    op.create_index("audit_log_entity_idx", "audit_log", ["entity_type", "entity_id"])
    op.alter_column(
        "audit_log",
        "details_json",
        comment=(
            "Structured details for traceability. Must not contain control signals, "
            "dispatch instructions, or asset activation data in v0.1."
        ),
        existing_type=postgresql.JSONB(astext_type=sa.Text()),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("ingestion_runs")
    op.drop_table("surplus_risk_forecasts")
    op.drop_table("weather_observations")
    op.drop_table("power_balance")
    op.drop_table("spot_prices")
