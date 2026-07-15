from pathlib import Path
import sys
from datetime import datetime

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.pricing import (
    PriceModelConfig,
    fit_price_models_from_ucm_dir,
    save_price_model_catalog,
)


INPUT_DIR = Path("data/processed")
OUTPUT_PATH = Path("reports/tables/price_model_readiness.csv")
FEATURE_COVERAGE_OUTPUT_PATH = Path(
    "reports/tables/price_feature_coverage.csv"
)
MODEL_OUTPUT_PATH = Path("artifacts/models/price_model_catalog.joblib")


def build_price_model_reports() -> tuple[pd.DataFrame, pd.DataFrame, object]:
    config = PriceModelConfig()
    catalog = fit_price_models_from_ucm_dir(INPUT_DIR, config=config)
    readiness = catalog.readiness_frame()
    feature_coverage = catalog.feature_coverage_frame()

    if not readiness.empty:
        readiness.insert(0, "input_dir", str(INPUT_DIR))

    return readiness, feature_coverage, catalog


def save_report(report: pd.DataFrame, path: Path) -> Path:
    output_path = path

    try:
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = path.with_name(
            f"{path.stem}_{timestamp}{path.suffix}"
        )
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")

    return output_path


def main() -> None:
    readiness, feature_coverage, catalog = build_price_model_reports()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    readiness_path = save_report(readiness, OUTPUT_PATH)
    coverage_path = save_report(feature_coverage, FEATURE_COVERAGE_OUTPUT_PATH)
    model_path = save_price_model_catalog(catalog, MODEL_OUTPUT_PATH)

    print(readiness.to_string(index=False))
    print(f"readiness_output_file: {readiness_path}")
    print(f"feature_coverage_output_file: {coverage_path}")
    print(f"model_output_file: {model_path}")


if __name__ == "__main__":
    main()
