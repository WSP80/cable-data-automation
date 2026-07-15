from pathlib import Path
import sys
from uuid import uuid4

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.export_ucm import build_ucm_from_source, load_manufacturer_config
from scripts.predict_prices import (
    INPUT_DIR,
    MODEL_PATH,
    OUTPUT_DIR,
    load_prediction_source,
    predict_ucm_frame_all_models,
    write_prediction_report,
)
from src.database import CableRepository, create_database_engine
from src.parsers.registry import PARSERS
from src.pricing import load_price_model_catalog


def main() -> None:
    repository = CableRepository(create_database_engine())
    repository.create_schema()
    catalog = load_price_model_catalog(MODEL_PATH)
    config = load_manufacturer_config()
    input_paths = sorted(INPUT_DIR.glob("*.csv"))

    if not input_paths:
        raise FileNotFoundError(f"No prediction CSV files found in {INPUT_DIR}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    prediction_run_id = str(uuid4())
    repository.start_current_load("prediction")

    for input_path in input_paths:
        manufacturer = input_path.stem

        if manufacturer not in config:
            raise ValueError(
                f"File name must match a configured manufacturer: {input_path.name}"
            )

        parser_name = config[manufacturer]["parser"]
        source = load_prediction_source(input_path)
        ucm_frame = build_ucm_from_source(source, PARSERS[parser_name])
        result = predict_ucm_frame_all_models(
            ucm_frame,
            catalog,
            config,
        )
        offer_ids, inserted = repository.store_ucm_frame(
            ucm_frame,
            dataset_role="prediction",
            source_dataset=input_path.name,
            load_run_id=prediction_run_id,
        )
        prediction_offer_ids = [
            offer_ids[int(row_number) - 1]
            for row_number in result["source_row_number"]
        ]
        stored_predictions = repository.record_predictions(
            prediction_offer_ids,
            result,
            prediction_run_id=prediction_run_id,
        )
        output_path = OUTPUT_DIR / f"{manufacturer}_PRICED.csv"
        write_prediction_report(result, output_path)
        successful = int(result["model_price_excl_vat"].notna().sum())
        print(
            f"{input_path.name}: {inserted} UCM rows inserted, "
            f"{stored_predictions} predictions stored, "
            f"{successful}/{len(result)} prices, "
            f"prediction_run_id={prediction_run_id} -> {output_path}"
        )


if __name__ == "__main__":
    main()
