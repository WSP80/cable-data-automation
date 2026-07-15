from __future__ import annotations

import argparse
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.descriptions import describe_ucm_frame, load_description_dictionary


INPUT_DIR = Path("data/processed")
OUTPUT_PATH = Path("reports/tables/construction_descriptions.csv")


def export_construction_descriptions(
    manufacturers: list[str] | None = None,
    input_dir: Path = INPUT_DIR,
    output_path: Path = OUTPUT_PATH,
) -> tuple[Path, int]:
    dictionary = load_description_dictionary()
    input_paths = _select_input_paths(input_dir, manufacturers)
    frames = []

    for input_path in input_paths:
        manufacturer = input_path.stem.removesuffix("_UCM")
        frame = pd.read_csv(input_path, sep=";", encoding="utf-8-sig")
        described = describe_ucm_frame(frame, dictionary)
        described.insert(0, "source_dataset", input_path.name)
        described.insert(1, "manufacturer", manufacturer)
        frames.append(described)

    if not frames:
        raise FileNotFoundError(f"No UCM files found in {input_dir}")

    result = pd.concat(frames, ignore_index=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    return output_path, len(result)


def _select_input_paths(
    input_dir: Path,
    manufacturers: list[str] | None,
) -> list[Path]:
    if manufacturers:
        return [
            input_dir / f"{manufacturer}_UCM.csv"
            for manufacturer in manufacturers
        ]

    return sorted(input_dir.glob("*_UCM.csv"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export construction descriptions from UCM CSV files."
    )
    parser.add_argument(
        "manufacturers",
        nargs="*",
        help="Manufacturer names without _UCM.csv. Default: every UCM CSV.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path, row_count = export_construction_descriptions(
        args.manufacturers or None
    )
    print(f"{row_count} construction descriptions -> {output_path}")


if __name__ == "__main__":
    main()
