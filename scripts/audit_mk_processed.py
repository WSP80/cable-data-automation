from collections import Counter
from datetime import datetime
from pathlib import Path
import re
import sys

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.feature_engineering.feature_builder import TECHNICAL_COLUMNS
from src.generators.registry import GENERATORS
from src.parsers.mk.parser import MKParser


INPUT_PATH = Path("data/processed/MK.csv")
OUTPUT_PATH = Path("reports/tables/mk_parse_audit.csv")


def normalize_mk_source(mark: str) -> str:
    normalized = mark
    normalized = re.sub(r"\s+\u041e\u041f(?=[-\s])", " ", normalized)
    normalized = normalized.replace("\u041e\u041f-", "")
    normalized = normalized.replace("\u042d\u0444\u042d\u043c\u0428", "\u042d\u0444\u042d\u043c\u043b\u0428")
    normalized = normalized.replace("\u042d\u0444\u042d\u043c\u041a", "\u042d\u0444\u042d\u043c\u043b\u041a")
    normalized = normalized.replace("\u042d\u0444\u042d\u043c\u0411", "\u042d\u0444\u042d\u043c\u043b\u0411")
    normalized = re.sub(r"(\u0423\u0424|UF)(\u043a|K)", r"\1-\2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)\s*\u0447-\u043a\s*(\d{3})", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)(\u0441\u0435\u0440|\u0441\u0435\u0440\u044b\u0439|SER|SERYY)", r"\1-серый", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)(\d{3})", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\))(\u0425\u041b|HL)", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\))(\u0425\u041b|HL)", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)\s+\u043a\s+(\d{3})", r"\1-к \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)\s+\u043a(\d{3})", r"\1-к \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)\s+\u0441(\d{3})", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(\u0423\u0424|UF)\s+\u043e\s+(\d{3})", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"(Ex-i .*)\s+\u0441\s+(\d{3})", r"\1 \2", normalized, flags=re.IGNORECASE)

    if normalized.count("(") > normalized.count(")"):
        normalized = close_missing_construction_parenthesis(normalized)

    normalized = re.sub(r"(\))(\u0425\u041b|HL)", r"\1 \2", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace(") -", ") ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    return normalized


def close_missing_construction_parenthesis(mark: str) -> str:
    match = re.search(
        r"(\([^\s]*(?:\u044d\u0444\u044d\u043c\u043b|\u044d\u043c\u0444|\u044d\u043c\u043b|\u044d\u0444|\u044d\u043c|\u044d|efeml|emf|eml|ef|em|e))",
        mark,
        flags=re.IGNORECASE,
    )

    if match:
        return f"{mark[:match.end()]}){mark[match.end():]}"

    return mark


def main() -> None:
    df = pd.read_csv(INPUT_PATH, sep=";", encoding="utf-8-sig")
    parser = MKParser()
    generator = GENERATORS["mk"]
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
            normalized_source = normalize_mk_source(mark)
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
