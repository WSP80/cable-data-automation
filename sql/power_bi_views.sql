DROP VIEW IF EXISTS bi_offer_features CASCADE;
DROP VIEW IF EXISTS bi_offer_features_history CASCADE;
DROP VIEW IF EXISTS bi_model_runs CASCADE;
DROP VIEW IF EXISTS bi_model_runs_history CASCADE;
DROP VIEW IF EXISTS bi_predictions CASCADE;
DROP VIEW IF EXISTS bi_prediction_history CASCADE;


CREATE OR REPLACE VIEW bi_offer_features_history AS
SELECT
    o.id AS offer_id,
    o.dataset_role,
    o.load_run_id,
    COALESCE(o.is_current_load, TRUE) AS is_current_load,
    o.source_dataset,
    o.source_row_number,
    o.source_file,
    o.invoice_number,
    o.invoice_date AS invoice_date_raw,
    CASE
        WHEN BTRIM(o.invoice_date) ~ '^[0-9]+([.][0-9]+)?$'
            THEN DATE '1899-12-30' + BTRIM(o.invoice_date)::NUMERIC::INTEGER
        WHEN BTRIM(o.invoice_date) ~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}'
            THEN LEFT(BTRIM(o.invoice_date), 10)::DATE
        WHEN BTRIM(o.invoice_date) ~ '^[0-9]{2}[.][0-9]{2}[.][0-9]{4}$'
            THEN TO_DATE(BTRIM(o.invoice_date), 'DD.MM.YYYY')
        ELSE NULL
    END AS invoice_date,
    o.product_description,
    o.length_km,
    o.unit_price_excl_vat,
    o.comment,
    o.created_at AS offer_created_at,
    u.id AS ucm_id,
    u.cable_family,
    u.core_groups,
    u.group_type,
    u.cross_section_mm2,
    u.cross_section_designation,
    u.conductor_flexibility_class,
    u.conductor_material,
    u.insulation_material,
    u.mica_tape_layers,
    COALESCE(u.individual_screen, 'None') AS individual_screen,
    u.filler_material,
    u.bedding_under_screen,
    COALESCE(u.overall_screen, 'None') AS overall_screen,
    u.sheath_material,
    COALESCE(u.armor_type, 'None') AS armor_type,
    u.water_blocking,
    u.flame_retardant,
    u.fire_resistant,
    u.low_smoke,
    u.low_toxicity,
    u.halogen_free,
    u.cold_resistant,
    u.uv_resistant,
    u.oil_resistant,
    u.chemical_resistant,
    u.rated_voltage_v,
    u.intrinsically_safe,
    u.explosive_area_application,
    u.sheath_color,
    u.total_conductors,
    u.copper_area_mm2,
    CASE
        WHEN u.copper_area_mm2 > 0
            THEN o.unit_price_excl_vat / u.copper_area_mm2
        ELSE NULL
    END AS price_per_copper_mm2
FROM source_offers AS o
JOIN ucm_features AS u
    ON u.offer_id = o.id;


CREATE OR REPLACE VIEW bi_offer_features AS
SELECT *
FROM bi_offer_features_history
WHERE is_current_load IS TRUE;


CREATE OR REPLACE VIEW bi_model_runs_history AS
SELECT
    mr.id AS model_run_id,
    mr.run_group_id,
    mr.cable_family,
    mr.model_type,
    mr.artifact_path,
    mr.training_rows,
    mr.test_rows,
    mr.mae,
    mr.mape,
    mr.rmse,
    mr.r2,
    mr.is_active,
    mr.trained_at,
    ROW_NUMBER() OVER (
        PARTITION BY mr.cable_family
        ORDER BY mr.trained_at DESC, mr.id DESC
    ) AS family_run_rank
FROM model_runs AS mr;


CREATE OR REPLACE VIEW bi_model_runs AS
SELECT *
FROM bi_model_runs_history
WHERE is_active IS TRUE;


CREATE OR REPLACE VIEW bi_prediction_history AS
WITH latest_prediction_run AS (
    SELECT p_latest.prediction_run_id
    FROM price_predictions AS p_latest
    WHERE p_latest.prediction_run_id IS NOT NULL
    ORDER BY p_latest.created_at DESC, p_latest.id DESC
    LIMIT 1
),
prediction_runs AS (
    SELECT
        grouped_runs.prediction_run_id,
        ROW_NUMBER() OVER (
            ORDER BY grouped_runs.last_prediction_at DESC, grouped_runs.last_prediction_id DESC
        ) AS prediction_run_rank
    FROM (
        SELECT
            prediction_run_id,
            MAX(created_at) AS last_prediction_at,
            MAX(id) AS last_prediction_id
        FROM price_predictions
        WHERE prediction_run_id IS NOT NULL
        GROUP BY prediction_run_id
    ) AS grouped_runs
)
SELECT
    p.id AS prediction_id,
    p.offer_id,
    p.model_run_id,
    p.target_manufacturer,
    COALESCE(
        p.target_cable_family,
        CASE
            WHEN p.target_manufacturer = 'TOFLEX' THEN 'TOFLEX-KU'
            ELSE p.target_manufacturer
        END,
        mr.cable_family
    )::VARCHAR(100) AS target_cable_family,
    p.generated_designation,
    p.construction_compatible,
    p.compatibility_differences,
    p.effective_target_voltage_v,
    p.voltage_equivalence_applied,
    p.predicted_price,
    CASE
        WHEN p.status = 'unsupported_cable_family'
            THEN 'insufficient_model_data'
        ELSE p.status
    END AS prediction_status,
    p.reason AS prediction_reason,
    p.model_type AS prediction_model_type,
    p.comparable_rows,
    p.created_at AS predicted_at,
    o.source_dataset,
    o.source_row_number,
    o.product_description AS source_product_description,
    o.unit_price_excl_vat AS actual_price,
    u.cable_family AS source_cable_family,
    u.core_groups,
    u.group_type,
    u.cross_section_mm2,
    u.total_conductors,
    u.copper_area_mm2,
    u.individual_screen,
    u.overall_screen,
    u.armor_type,
    u.insulation_material,
    u.sheath_material,
    u.fire_resistant,
    u.low_smoke,
    u.low_toxicity,
    u.halogen_free,
    u.cold_resistant,
    u.uv_resistant,
    u.oil_resistant,
    u.rated_voltage_v AS source_rated_voltage_v,
    CASE
        WHEN o.unit_price_excl_vat IS NOT NULL
             AND p.predicted_price IS NOT NULL
            THEN p.predicted_price - o.unit_price_excl_vat
        ELSE NULL
    END AS prediction_error,
    CASE
        WHEN o.unit_price_excl_vat > 0
             AND p.predicted_price IS NOT NULL
            THEN ABS(p.predicted_price - o.unit_price_excl_vat)
                 / o.unit_price_excl_vat
        ELSE NULL
    END AS absolute_percentage_error,
    p.prediction_run_id,
    o.dataset_role AS source_dataset_role,
    o.load_run_id AS source_load_run_id,
    COALESCE(o.is_current_load, TRUE) AS is_current_source_load,
    COALESCE(prediction_runs.prediction_run_rank, 999)::INTEGER
        AS prediction_run_rank,
    (
        p.prediction_run_id IS NOT NULL
        AND p.prediction_run_id = latest_prediction_run.prediction_run_id
    ) AS is_current_prediction_run,
    p.construction_description
FROM price_predictions AS p
JOIN source_offers AS o
    ON o.id = p.offer_id
JOIN ucm_features AS u
    ON u.offer_id = o.id
LEFT JOIN model_runs AS mr
    ON mr.id = p.model_run_id
LEFT JOIN latest_prediction_run
    ON TRUE
LEFT JOIN prediction_runs
    ON prediction_runs.prediction_run_id = p.prediction_run_id;


CREATE OR REPLACE VIEW bi_predictions AS
SELECT *
FROM bi_prediction_history
WHERE is_current_prediction_run IS TRUE;
