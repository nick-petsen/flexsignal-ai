-- FlexSignal AI v0.1 PostgreSQL/TimescaleDB schema baseline.
--
-- v0.1 is read-only decision support. This schema stores source data,
-- model outputs, and audit events for human review. It does not store
-- control signals, dispatch instructions, asset activation data, or
-- closed-loop control state.
--
-- TODO: Add Alembic migrations before applying this schema in an environment.
-- TODO: Evaluate TimescaleDB hypertables for timestamped tables after local
--       database setup and retention requirements are defined.

CREATE TABLE spot_prices (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price_area TEXT NOT NULL CHECK (price_area IN ('DK1', 'DK2')),
    timestamp_utc TIMESTAMPTZ NOT NULL,
    price_eur_per_mwh NUMERIC(12, 4) NOT NULL,
    price_dkk_per_kwh NUMERIC(12, 6) NOT NULL,
    source TEXT NOT NULL,
    source_record_id TEXT,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT spot_prices_unique_source_record UNIQUE (source, source_record_id),
    CONSTRAINT spot_prices_unique_area_timestamp_source UNIQUE (price_area, timestamp_utc, source)
);

COMMENT ON TABLE spot_prices IS
    'Read-only decision-support storage for DK1/DK2 electricity spot prices.';
COMMENT ON COLUMN spot_prices.price_area IS 'Danish bidding zone: DK1 or DK2.';
COMMENT ON COLUMN spot_prices.timestamp_utc IS 'UTC timestamp for the observed market interval.';

CREATE INDEX spot_prices_timestamp_utc_idx
    ON spot_prices (timestamp_utc);
CREATE INDEX spot_prices_price_area_timestamp_utc_idx
    ON spot_prices (price_area, timestamp_utc);
CREATE INDEX spot_prices_source_idx
    ON spot_prices (source);

-- TODO: Consider converting spot_prices to a TimescaleDB hypertable on
--       timestamp_utc once TimescaleDB extension management is defined.

CREATE TABLE power_balance (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price_area TEXT NOT NULL CHECK (price_area IN ('DK1', 'DK2')),
    timestamp_utc TIMESTAMPTZ NOT NULL,
    production_mw NUMERIC(14, 4),
    consumption_mw NUMERIC(14, 4),
    wind_onshore_mw NUMERIC(14, 4),
    wind_offshore_mw NUMERIC(14, 4),
    solar_mw NUMERIC(14, 4),
    exchange_net_mw NUMERIC(14, 4),
    source TEXT NOT NULL,
    source_record_id TEXT,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT power_balance_unique_source_record UNIQUE (source, source_record_id),
    CONSTRAINT power_balance_unique_area_timestamp_source UNIQUE (price_area, timestamp_utc, source)
);

COMMENT ON TABLE power_balance IS
    'Read-only decision-support storage for production, consumption, exchange, and generation measurements.';
COMMENT ON COLUMN power_balance.exchange_net_mw IS
    'Net exchange in MW. Final sign convention is pending dataset mapping.';

CREATE INDEX power_balance_timestamp_utc_idx
    ON power_balance (timestamp_utc);
CREATE INDEX power_balance_price_area_timestamp_utc_idx
    ON power_balance (price_area, timestamp_utc);
CREATE INDEX power_balance_source_idx
    ON power_balance (source);

-- TODO: Consider converting power_balance to a TimescaleDB hypertable on
--       timestamp_utc once TimescaleDB extension management is defined.

CREATE TABLE weather_observations (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    location_id TEXT NOT NULL,
    timestamp_utc TIMESTAMPTZ NOT NULL,
    wind_speed_mps NUMERIC(10, 4),
    wind_direction_deg NUMERIC(7, 3)
        CHECK (wind_direction_deg IS NULL OR (wind_direction_deg >= 0 AND wind_direction_deg <= 360)),
    temperature_c NUMERIC(7, 3),
    cloud_cover_pct NUMERIC(7, 3)
        CHECK (cloud_cover_pct IS NULL OR (cloud_cover_pct >= 0 AND cloud_cover_pct <= 100)),
    source TEXT NOT NULL,
    source_record_id TEXT,
    ingested_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT weather_observations_unique_source_record UNIQUE (source, source_record_id),
    CONSTRAINT weather_observations_unique_location_timestamp_source UNIQUE (location_id, timestamp_utc, source)
);

COMMENT ON TABLE weather_observations IS
    'Read-only decision-support storage for weather features relevant to forecasting.';
COMMENT ON COLUMN weather_observations.location_id IS
    'Stable identifier for a weather station, grid cell, or mapped forecast location.';

CREATE INDEX weather_observations_timestamp_utc_idx
    ON weather_observations (timestamp_utc);
CREATE INDEX weather_observations_location_timestamp_utc_idx
    ON weather_observations (location_id, timestamp_utc);
CREATE INDEX weather_observations_source_idx
    ON weather_observations (source);

-- TODO: Consider converting weather_observations to a TimescaleDB hypertable
--       on timestamp_utc once TimescaleDB extension management is defined.

CREATE TABLE surplus_risk_forecasts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    price_area TEXT NOT NULL CHECK (price_area IN ('DK1', 'DK2')),
    forecast_created_at_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    forecast_start_utc TIMESTAMPTZ NOT NULL,
    forecast_end_utc TIMESTAMPTZ NOT NULL,
    risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
    confidence_score NUMERIC(5, 4) NOT NULL
        CHECK (confidence_score >= 0 AND confidence_score <= 1),
    expected_surplus_mw NUMERIC(14, 4),
    recommended_action TEXT NOT NULL,
    economic_potential_dkk NUMERIC(14, 2),
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    explanation_text TEXT,
    input_data_window_start_utc TIMESTAMPTZ,
    input_data_window_end_utc TIMESTAMPTZ,
    CONSTRAINT surplus_risk_forecasts_window_check CHECK (forecast_start_utc < forecast_end_utc),
    CONSTRAINT surplus_risk_forecasts_input_window_check CHECK (
        input_data_window_start_utc IS NULL
        OR input_data_window_end_utc IS NULL
        OR input_data_window_start_utc <= input_data_window_end_utc
    )
);

COMMENT ON TABLE surplus_risk_forecasts IS
    'Read-only decision-support model outputs for human review; not operational dispatch.';
COMMENT ON COLUMN surplus_risk_forecasts.recommended_action IS
    'Human-readable recommendation text only. This is not a control command or activation instruction.';
COMMENT ON COLUMN surplus_risk_forecasts.explanation_text IS
    'Optional explanation/reporting text. LLMs may support explanation only, not primary forecasting.';

CREATE INDEX surplus_risk_forecasts_created_at_idx
    ON surplus_risk_forecasts (forecast_created_at_utc);
CREATE INDEX surplus_risk_forecasts_price_area_window_idx
    ON surplus_risk_forecasts (price_area, forecast_start_utc, forecast_end_utc);
CREATE INDEX surplus_risk_forecasts_window_idx
    ON surplus_risk_forecasts (forecast_start_utc, forecast_end_utc);
CREATE INDEX surplus_risk_forecasts_model_idx
    ON surplus_risk_forecasts (model_name, model_version);

-- TODO: Consider converting surplus_risk_forecasts to a TimescaleDB hypertable
--       on forecast_created_at_utc if forecast volume justifies it.

CREATE TABLE ingestion_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source TEXT NOT NULL,
    dataset_name TEXT NOT NULL,
    started_at_utc TIMESTAMPTZ NOT NULL,
    finished_at_utc TIMESTAMPTZ,
    status TEXT NOT NULL,
    records_processed INTEGER NOT NULL DEFAULT 0 CHECK (records_processed >= 0),
    error_message TEXT,
    CONSTRAINT ingestion_runs_time_check CHECK (
        finished_at_utc IS NULL OR started_at_utc <= finished_at_utc
    )
);

COMMENT ON TABLE ingestion_runs IS
    'Audit trail for ingestion jobs. No ingestion runtime is implemented in v0.1 schema baseline.';

CREATE INDEX ingestion_runs_started_at_idx
    ON ingestion_runs (started_at_utc);
CREATE INDEX ingestion_runs_source_idx
    ON ingestion_runs (source);
CREATE INDEX ingestion_runs_source_dataset_idx
    ON ingestion_runs (source, dataset_name);
CREATE INDEX ingestion_runs_status_idx
    ON ingestion_runs (status);

CREATE TABLE audit_log (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_time_utc TIMESTAMPTZ NOT NULL DEFAULT now(),
    event_type TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    entity_type TEXT,
    entity_id TEXT,
    details_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT audit_log_details_json_object_check CHECK (jsonb_typeof(details_json) = 'object')
);

COMMENT ON TABLE audit_log IS
    'Audit trail for user-visible forecasts, explanations, and human review actions in read-only v0.1.';
COMMENT ON COLUMN audit_log.details_json IS
    'Structured details for traceability. Must not contain control signals, dispatch instructions, or asset activation data in v0.1.';

CREATE INDEX audit_log_event_time_idx
    ON audit_log (event_time_utc);
CREATE INDEX audit_log_event_type_idx
    ON audit_log (event_type);
CREATE INDEX audit_log_actor_idx
    ON audit_log (actor_type, actor_id);
CREATE INDEX audit_log_entity_idx
    ON audit_log (entity_type, entity_id);
