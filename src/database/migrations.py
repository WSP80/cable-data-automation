from sqlalchemy import Engine, inspect, text


PREDICTION_COLUMNS = {
    "target_manufacturer": "VARCHAR(100)",
    "prediction_run_id": "VARCHAR(36)",
    "target_cable_family": "VARCHAR(100)",
    "generated_designation": "TEXT",
    "construction_description": "TEXT",
    "construction_compatible": "BOOLEAN",
    "compatibility_differences": "TEXT",
    "effective_target_voltage_v": "INTEGER",
    "voltage_equivalence_applied": "BOOLEAN",
}

SOURCE_OFFER_COLUMNS = {
    "load_run_id": "VARCHAR(36)",
    "is_current_load": "BOOLEAN",
}


def migrate_schema(engine: Engine) -> None:
    inspector = inspect(engine)

    table_names = inspector.get_table_names()

    if "source_offers" in table_names:
        existing_source_offer_columns = {
            column["name"]
            for column in inspector.get_columns("source_offers")
        }

        with engine.begin() as connection:
            for column_name, sql_type in SOURCE_OFFER_COLUMNS.items():
                if column_name in existing_source_offer_columns:
                    continue

                connection.execute(
                    text(
                        f"ALTER TABLE source_offers "
                        f"ADD COLUMN {column_name} {sql_type}"
                    )
                )

            connection.execute(
                text(
                    "UPDATE source_offers "
                    "SET is_current_load = TRUE "
                    "WHERE is_current_load IS NULL"
                )
            )

    if "price_predictions" not in table_names:
        return

    existing_columns = {
        column["name"]
        for column in inspector.get_columns("price_predictions")
    }

    with engine.begin() as connection:
        for column_name, sql_type in PREDICTION_COLUMNS.items():
            if column_name in existing_columns:
                continue

            connection.execute(
                text(
                    f"ALTER TABLE price_predictions "
                    f"ADD COLUMN {column_name} {sql_type}"
                )
            )

        connection.execute(
            text(
                "UPDATE price_predictions "
                "SET prediction_run_id = 'legacy-prediction-run' "
                "WHERE prediction_run_id IS NULL"
            )
        )
