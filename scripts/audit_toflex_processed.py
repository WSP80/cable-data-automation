from collections import Counter
from datetime import datetime
from pathlib import Path
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.feature_engineering.feature_builder import TECHNICAL_COLUMNS
from src.generators.registry import GENERATORS
from src.parsers.toflex.parser import ToflexParser


INPUT_PATH = Path("data/processed/TOFLEX.csv")
OUTPUT_PATH = Path("reports/tables/toflex_parse_audit.csv")


def normalize_redundant_blue_sheath_marker(mark: str) -> str:
    if "-i" not in mark:
        return mark

    return mark.replace(" \u0441 - ", " - ")


def main() -> None:
    df = pd.read_csv(INPUT_PATH, sep=";", encoding="utf-8-sig")
    parser = ToflexParser()
    generator = GENERATORS["toflex"]
    rows = []
    errors = []
    missing_counter = Counter()
    mismatch_counter = Counter()
    normalized_mismatch_counter = Counter()

    for index, row in df.iterrows():
        mark = str(row.get("product_description") or "").strip()
        comment = row.get("comment")

        if pd.isna(comment):
            comment = None

        try:
            ucm = parser.parse(mark, comment=comment)
            generated = generator.generate(ucm)
            missing = [
                name
                for name in TECHNICAL_COLUMNS
                if getattr(ucm, name) is None
            ]

            for name in missing:
                missing_counter[name] += 1

            roundtrip_match = mark == generated
            normalized_source = normalize_redundant_blue_sheath_marker(mark)
            normalized_match = normalized_source == generated

            if not roundtrip_match:
                mismatch_counter[(mark, generated)] += 1

            if not normalized_match:
                normalized_mismatch_counter[(normalized_source, generated)] += 1

            rows.append(
                {
                    "row": index,
                    "source_file": row.get("source_file"),
                    "product_description": mark,
                    "normalized_source": normalized_source,
                    "generated": generated,
                    "roundtrip_match": roundtrip_match,
                    "normalized_match": normalized_match,
                    "missing_features": ",".join(missing),
                    "error": "",
                }
            )
        except Exception as error:
            errors.append((index, mark, type(error).__name__, str(error)))
            rows.append(
                {
                    "row": index,
                    "source_file": row.get("source_file"),
                    "product_description": mark,
                    "normalized_source": "",
                    "generated": "",
                    "roundtrip_match": False,
                    "normalized_match": False,
                    "missing_features": "",
                    "error": f"{type(error).__name__}: {error}",
                }
            )

    report = pd.DataFrame(rows)
    output_path = OUTPUT_PATH
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    try:
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_PATH.with_name(
            f"{OUTPUT_PATH.stem}_{timestamp}{OUTPUT_PATH.suffix}"
        )
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")

    print(f"rows: {len(df)}")
    print(f"parsed: {len(df) - len(errors)}")
    print(f"errors: {len(errors)}")
    print(f"roundtrip_matches: {int(report['roundtrip_match'].sum())}")
    print(
        "roundtrip_mismatches: "
        f"{int((~report['roundtrip_match']).sum()) - len(errors)}"
    )
    print(f"normalized_matches: {int(report['normalized_match'].sum())}")
    print(
        "normalized_mismatches: "
        f"{int((~report['normalized_match']).sum()) - len(errors)}"
    )
    print(
        "rows_with_missing_features: "
        f"{int((report['missing_features'] != '').sum())}"
    )
    print(f"missing_counter: {dict(missing_counter.most_common())}")
    print(f"audit_file: {output_path}")

    print("top_errors:")
    for item in errors[:10]:
        print(item)

    print("top_mismatches:")
    for (mark, generated), count in mismatch_counter.most_common(20):
        print(f"{count} | INPUT={mark} | GENERATED={generated}")

    print("top_normalized_mismatches:")
    for (normalized_source, generated), count in normalized_mismatch_counter.most_common(20):
        print(f"{count} | NORMALIZED={normalized_source} | GENERATED={generated}")


if __name__ == "__main__":
    main()
