from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.feature_engineering import FeatureBuilder
from src.models.cable import Cable
from src.parsers.registry import PARSERS


INPUT_DIR = Path("data/processed")
CONFIG_PATH = Path("config/manufacturers.json")


def clean_cell(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def cable_from_row(row: pd.Series, parser: Any) -> Cable:
    product_description = str(clean_cell(row.get("product_description")) or "").strip()
    comment = clean_cell(row.get("comment"))
    ucm = parser.parse(product_description, comment=comment)

    return Cable(
        source_file=clean_cell(row.get("source_file")),
        invoice_number=clean_cell(row.get("invoice_number")),
        invoice_date=clean_cell(row.get("invoice_date")),
        product_description=product_description,
        cable_family=ucm.cable_family,
        length_km=clean_cell(row.get("length_km")),
        unit_price_excl_vat=clean_cell(row.get("unit_price_excl_vat")),
        comment=comment,
        ucm=ucm,
    )


def load_manufacturer_config(path: Path = CONFIG_PATH) -> dict[str, dict[str, Any]]:
    with path.open(encoding="utf-8") as config_file:
        return json.load(config_file)


def build_ucm_dataframe(input_path: Path, parser: Any) -> pd.DataFrame:
    source = pd.read_csv(input_path, sep=";", encoding="utf-8-sig")
    return build_ucm_from_source(source, parser)


def build_ucm_from_source(source: pd.DataFrame, parser: Any) -> pd.DataFrame:
    cables = [
        cable_from_row(row, parser)
        for _, row in source.iterrows()
    ]
    return FeatureBuilder().build_dataframe(cables)


def export_manufacturer_ucm(
    manufacturer: str,
    parser_name: str,
    input_dir: Path = INPUT_DIR,
) -> tuple[Path, int] | None:
    input_path = input_dir / f"{manufacturer}.csv"
    output_path = input_dir / f"{manufacturer}_UCM.csv"

    if not input_path.exists():
        return None
    if parser_name not in PARSERS:
        raise ValueError(f"Parser is not registered: {parser_name}")

    features = build_ucm_dataframe(input_path, PARSERS[parser_name])
    features.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    return output_path, len(features)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert manufacturer CSV files into UCM feature tables."
    )
    parser.add_argument(
        "manufacturers",
        nargs="*",
        help="Manufacturer names from config/manufacturers.json. Default: all.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_manufacturer_config()
    selected = args.manufacturers or list(config)
    exported_count = 0

    for manufacturer in selected:
        if manufacturer not in config:
            raise ValueError(f"Unknown manufacturer: {manufacturer}")

        result = export_manufacturer_ucm(
            manufacturer,
            config[manufacturer]["parser"],
        )

        if result is None:
            input_path = INPUT_DIR / f"{manufacturer}.csv"
            print(f"{manufacturer}: skipped, input file not found: {input_path}")
            continue

        output_path, row_count = result
        exported_count += 1
        print(f"{manufacturer}: {row_count} rows -> {output_path}")

    if exported_count == 0:
        raise FileNotFoundError(
            f"No manufacturer input CSV files found in {INPUT_DIR}"
        )


if __name__ == "__main__":
    main()
