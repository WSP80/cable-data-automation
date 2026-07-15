from __future__ import annotations

import argparse
from dataclasses import replace
from io import StringIO
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from scripts.export_ucm import (
    build_ucm_from_source,
    load_manufacturer_config,
)
from src.descriptions import describe_ucm_features
from src.feature_engineering import FeatureBuilder
from src.feature_engineering.feature_builder import TECHNICAL_COLUMNS
from src.generators.registry import GENERATORS
from src.models.ucm import UCM
from src.parsers.registry import PARSERS
from src.pricing import UCMPriceModelCatalog, load_price_model_catalog


INPUT_DIR = Path("data/prediction_input")
OUTPUT_DIR = Path("data/prediction_output")
MODEL_PATH = Path("artifacts/models/price_model_catalog.joblib")

PREDICTION_COLUMNS = [
    "model_price_excl_vat",
    "prediction_status",
    "prediction_reason",
    "prediction_model_type",
    "prediction_comparable_rows",
]

SEMANTIC_COMPARISON_FEATURES = [
    feature
    for feature in TECHNICAL_COLUMNS
    if feature not in {
        "cable_family",
        "cross_section_designation",
        "mica_tape_layers",
    }
]


def predict_ucm_frame(
    ucm_frame: pd.DataFrame,
    catalog: UCMPriceModelCatalog,
) -> pd.DataFrame:
    result = ucm_frame.copy()
    prediction_rows = []

    for _, row in result.iterrows():
        prediction = catalog.predict(row.to_dict())
        prediction_rows.append(
            {
                "model_price_excl_vat": (
                    round(prediction.predicted_price, 2)
                    if prediction.predicted_price is not None
                    else None
                ),
                "prediction_status": prediction.status,
                "prediction_reason": prediction.reason,
                "prediction_model_type": prediction.model_type,
                "prediction_comparable_rows": prediction.comparable_rows,
            }
        )

    predictions = pd.DataFrame(prediction_rows, columns=PREDICTION_COLUMNS)
    return pd.concat(
        [result.reset_index(drop=True), predictions],
        axis=1,
    )


def predict_ucm_frame_all_models(
    ucm_frame: pd.DataFrame,
    catalog: UCMPriceModelCatalog,
    manufacturer_config: dict[str, dict[str, object]],
) -> pd.DataFrame:
    rows = []
    feature_builder = FeatureBuilder()

    for source_index, (_, source_row) in enumerate(
        ucm_frame.iterrows(),
        start=1,
    ):
        source_features = source_row.to_dict()
        source_ucm = UCM(
            **{
                feature: source_features.get(feature)
                for feature in TECHNICAL_COLUMNS
            }
        )
        source_ucm.finalize_features()

        for target_manufacturer, target_config in manufacturer_config.items():
            target_family = str(
                target_config.get("cable_family", target_manufacturer)
            )
            target_row = {
                **source_features,
                "source_row_number": source_index,
                "target_manufacturer": target_manufacturer,
                "target_cable_family": target_family,
                "generated_designation": None,
                "construction_description": None,
                "construction_compatible": False,
                "compatibility_differences": None,
                "effective_target_voltage_v": None,
                "voltage_equivalence_applied": False,
                "model_price_excl_vat": None,
                "prediction_status": "generation_failed",
                "prediction_reason": "",
                "prediction_model_type": None,
                "prediction_comparable_rows": 0,
            }

            supported_voltages = target_config.get("supported_voltages", [])
            requested_voltage = source_features.get("rated_voltage_v")
            voltage_equivalents = target_config.get("voltage_equivalents", {})
            effective_voltage = voltage_equivalents.get(
                str(requested_voltage),
                requested_voltage,
            )
            target_row["effective_target_voltage_v"] = effective_voltage
            target_row["voltage_equivalence_applied"] = (
                effective_voltage != requested_voltage
            )

            if (
                effective_voltage is not None
                and supported_voltages
                and effective_voltage not in supported_voltages
            ):
                target_row["prediction_status"] = (
                    "incompatible_target_construction"
                )
                target_row["prediction_reason"] = (
                    f"{target_manufacturer} does not support "
                    f"rated_voltage_v={effective_voltage}; supported values: "
                    f"{supported_voltages}"
                )
                rows.append(target_row)
                continue

            try:
                target_source_ucm = replace(
                    source_ucm,
                    rated_voltage_v=effective_voltage,
                )
                generated = GENERATORS[target_config["generator"]].generate(
                    target_source_ucm,
                    alphabet="latin",
                )
                target_ucm = PARSERS[target_config["parser"]].parse(generated)
                target_features = feature_builder.ucm_to_features(target_ucm)
                target_features["product_description"] = generated
                differences = compare_semantic_features(
                    feature_builder.ucm_to_features(target_source_ucm),
                    target_features,
                )
                target_row["generated_designation"] = generated
                target_row["target_cable_family"] = target_features["cable_family"]
                target_row["construction_description"] = describe_ucm_features(
                    target_features
                )
                target_row["compatibility_differences"] = ", ".join(differences)

                if differences:
                    target_row["prediction_status"] = (
                        "incompatible_target_construction"
                    )
                    target_row["prediction_reason"] = (
                        "Target designation changes UCM features: "
                        + ", ".join(differences)
                    )
                else:
                    prediction = catalog.predict(target_features)
                    target_row.update(
                        {
                            "construction_compatible": True,
                            "model_price_excl_vat": (
                                round(prediction.predicted_price, 2)
                                if prediction.predicted_price is not None
                                else None
                            ),
                            "prediction_status": prediction.status,
                            "prediction_reason": prediction.reason,
                            "prediction_model_type": prediction.model_type,
                            "prediction_comparable_rows": (
                                prediction.comparable_rows
                            ),
                        }
                    )
            except (KeyError, TypeError, ValueError) as error:
                target_row["prediction_reason"] = str(error)

            rows.append(target_row)

    return pd.DataFrame(rows)


def compare_semantic_features(
    source: dict[str, object],
    target: dict[str, object],
) -> list[str]:
    differences = []

    for feature in SEMANTIC_COMPARISON_FEATURES:
        source_value = source.get(feature)
        target_value = target.get(feature)

        if values_equal(source_value, target_value):
            continue

        differences.append(
            f"{feature}={source_value!r}->{target_value!r}"
        )

    return differences


def values_equal(left: object, right: object) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True

    if isinstance(left, float) or isinstance(right, float):
        try:
            return abs(float(left) - float(right)) < 1e-9
        except (TypeError, ValueError):
            pass

    return left == right


def predict_file(
    input_path: Path,
    output_dir: Path,
    catalog: UCMPriceModelCatalog,
    manufacturer_config: dict[str, dict[str, object]],
) -> tuple[Path, pd.DataFrame]:
    manufacturer = input_path.stem

    if manufacturer not in manufacturer_config:
        raise ValueError(
            f"File name must match a manufacturer from config: {input_path.name}"
        )

    parser_name = manufacturer_config[manufacturer]["parser"]
    source = load_prediction_source(input_path)
    ucm_frame = build_ucm_from_source(source, PARSERS[parser_name])
    result = predict_ucm_frame_all_models(
        ucm_frame,
        catalog,
        manufacturer_config,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{manufacturer}_PRICED.csv"
    write_prediction_report(result, output_path)

    expected_rows = len(source) * len(manufacturer_config)

    if expected_rows != len(result):
        raise RuntimeError(
            f"Unexpected comparison row count: {expected_rows} -> {len(result)}"
        )

    return output_path, result


def write_prediction_report(
    result: pd.DataFrame,
    output_path: Path,
) -> None:
    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as output_file:
        grouped = list(result.groupby("source_row_number", sort=False))

        for group_index, (_, group) in enumerate(grouped):
            group.to_csv(
                output_file,
                sep=";",
                index=False,
                header=group_index == 0,
                lineterminator="\n",
            )

            if group_index < len(grouped) - 1:
                output_file.write("\n")


def load_prediction_source(input_path: Path) -> pd.DataFrame:
    text = read_prediction_text(input_path)
    source = pd.read_csv(StringIO(text), sep=";")

    if "product_description" in source.columns:
        return source

    descriptions = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not descriptions:
        raise ValueError(f"Prediction file is empty: {input_path}")

    return pd.DataFrame({"product_description": descriptions})


def read_prediction_text(input_path: Path) -> str:
    content = input_path.read_bytes()

    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeError(
        f"Unsupported text encoding in prediction file: {input_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Predict prices for manufacturer CSV files without prices."
    )
    parser.add_argument(
        "manufacturers",
        nargs="*",
        help="Manufacturer file names without .csv. Default: every input CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_manufacturer_config()
    catalog = load_price_model_catalog(MODEL_PATH)
    selected = set(args.manufacturers)
    input_paths = sorted(INPUT_DIR.glob("*.csv"))

    if selected:
        input_paths = [
            path for path in input_paths
            if path.stem in selected
        ]

    if not input_paths:
        raise FileNotFoundError(
            f"No prediction CSV files found in {INPUT_DIR}"
        )

    for input_path in input_paths:
        output_path, result = predict_file(
            input_path,
            OUTPUT_DIR,
            catalog,
            config,
        )
        successful = int(result["model_price_excl_vat"].notna().sum())
        print(
            f"{input_path.name}: {successful}/{len(result)} prices -> "
            f"{output_path}"
        )


if __name__ == "__main__":
    main()
