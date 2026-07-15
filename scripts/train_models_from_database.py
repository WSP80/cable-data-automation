from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.audit_price_models import (
    FEATURE_COVERAGE_OUTPUT_PATH,
    MODEL_OUTPUT_PATH,
    OUTPUT_PATH,
    save_report,
)
from src.database import CableRepository, create_database_engine
from src.pricing import (
    PriceModelConfig,
    UCMPriceModelCatalog,
    fit_price_models_by_family,
    save_price_model_catalog,
)


def main() -> None:
    repository = CableRepository(create_database_engine())
    repository.create_schema()
    training_frame = repository.load_training_frame()

    if training_frame.empty:
        raise ValueError(
            "No priced training rows found in the database. "
            "Run scripts/import_ucm_to_database.py first."
        )

    catalog = UCMPriceModelCatalog(
        fit_price_models_by_family(
            [training_frame],
            config=PriceModelConfig(),
        )
    )
    readiness = catalog.readiness_frame()
    feature_coverage = catalog.feature_coverage_frame()
    model_path = save_price_model_catalog(catalog, MODEL_OUTPUT_PATH)
    model_run_ids = repository.record_model_runs(catalog, model_path)
    readiness_path = save_report(readiness, OUTPUT_PATH)
    coverage_path = save_report(
        feature_coverage,
        FEATURE_COVERAGE_OUTPUT_PATH,
    )

    print(readiness.to_string(index=False))
    print(f"model_runs_recorded: {model_run_ids}")
    print(f"model_output_file: {model_path}")
    print(f"readiness_output_file: {readiness_path}")
    print(f"feature_coverage_output_file: {coverage_path}")


if __name__ == "__main__":
    main()
