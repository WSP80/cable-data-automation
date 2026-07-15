from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import math
import re
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

from src.generators.atomkip.rules import transliterate_atomkip_mark
from src.generators.conflex.rules import transliterate_conflex_mark
from src.generators.mk.rules import transliterate_mk_mark
from src.generators.toflex.rules import transliterate_toflex_mark
from src.models.ucm import UCM


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DICTIONARY_PATH = (
    PROJECT_ROOT / "config" / "construction_description_dictionary.xlsx"
)

_XLSX_NS = {
    "a": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
_EMPTY_STRINGS = {"", "none", "nan", "null"}
_TRUE_STRINGS = {"true", "yes", "1"}
_FALSE_STRINGS = {"false", "no", "0"}
_TRANSLITERATORS = {
    "ATOMKIP-KU": transliterate_atomkip_mark,
    "CONFLEX": transliterate_conflex_mark,
    "MK": transliterate_mk_mark,
    "TOFLEX": transliterate_toflex_mark,
    "TOFLEX-KU": transliterate_toflex_mark,
}


@dataclass(frozen=True)
class DescriptionRule:
    feature_name: str
    label: str


def load_description_dictionary(
    path: Path = DEFAULT_DICTIONARY_PATH,
    sheet_name: str | None = None,
) -> list[DescriptionRule]:
    rows = _read_xlsx_rows(path, sheet_name)
    rules = []

    for row in rows:
        if len(row) < 2:
            continue

        feature_name = row[0].strip()
        label = row[1].strip()

        if not feature_name or not label:
            continue

        rules.append(DescriptionRule(feature_name=feature_name, label=label))

    return rules


def describe_ucm(
    ucm: UCM,
    dictionary: Iterable[DescriptionRule] | None = None,
) -> str:
    ucm.finalize_features()
    return describe_ucm_features(asdict(ucm), dictionary)


def describe_ucm_features(
    features: Mapping[str, Any],
    dictionary: Iterable[DescriptionRule] | None = None,
) -> str:
    rules = list(dictionary or load_description_dictionary())
    lines = _designation_lines(features)

    for rule in rules:
        if rule.feature_name not in features:
            continue

        value = features[rule.feature_name]
        boolean_value = _coerce_boolean(value)

        if boolean_value is True:
            lines.append(rule.label)
            continue

        if boolean_value is False or _is_empty_value(value):
            continue

        lines.append(f"{rule.label}: {_format_value(value)}")

    return "\n".join(lines)


def transliterate_designation(
    designation: Any,
    cable_family: Any = None,
) -> str:
    if _is_empty_value(designation):
        return ""

    mark = str(designation).strip()
    family = "" if _is_empty_value(cable_family) else str(cable_family).strip()
    transliterator = _TRANSLITERATORS.get(family)

    if transliterator is None:
        return mark

    return transliterator(mark)


def describe_ucm_frame(
    frame: pd.DataFrame,
    dictionary: Iterable[DescriptionRule] | None = None,
    description_column: str = "construction_description",
) -> pd.DataFrame:
    rules = list(dictionary or load_description_dictionary())
    result = frame.copy()
    result[description_column] = [
        describe_ucm_features(row.to_dict(), rules)
        for _, row in result.iterrows()
    ]
    return result


def _read_xlsx_rows(
    path: Path,
    sheet_name: str | None,
) -> list[list[str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings = _read_shared_strings(archive)
        sheet_path = _resolve_sheet_path(archive, sheet_name)
        worksheet = ET.fromstring(archive.read(sheet_path))

        rows = []
        for row in worksheet.findall("a:sheetData/a:row", _XLSX_NS):
            values_by_column = {}

            for cell in row.findall("a:c", _XLSX_NS):
                column_index = _cell_column_index(cell.attrib.get("r", ""))
                values_by_column[column_index] = _cell_value(cell, shared_strings)

            if values_by_column:
                max_column = max(values_by_column)
                rows.append(
                    [
                        values_by_column.get(column_index, "")
                        for column_index in range(1, max_column + 1)
                    ]
                )

        return rows


def _read_shared_strings(archive: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []

    root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
    return [
        "".join(text.text or "" for text in item.findall(".//a:t", _XLSX_NS))
        for item in root.findall("a:si", _XLSX_NS)
    ]


def _resolve_sheet_path(
    archive: zipfile.ZipFile,
    sheet_name: str | None,
) -> str:
    workbook = ET.fromstring(archive.read("xl/workbook.xml"))
    relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
    relationship_targets = {
        relationship.attrib["Id"]: relationship.attrib["Target"]
        for relationship in relationships
    }

    for sheet in workbook.findall("a:sheets/a:sheet", _XLSX_NS):
        if sheet_name is not None and sheet.attrib["name"] != sheet_name:
            continue

        relationship_id = sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        target = relationship_targets[relationship_id].lstrip("/")
        return target if target.startswith("xl/") else f"xl/{target}"

    if sheet_name is None:
        raise ValueError(f"Workbook contains no sheets: {archive.filename}")

    raise ValueError(f"Sheet not found in {archive.filename}: {sheet_name}")


def _cell_value(cell: ET.Element, shared_strings: list[str]) -> str:
    value = cell.find("a:v", _XLSX_NS)

    if value is None:
        inline_text = cell.find(".//a:t", _XLSX_NS)
        return inline_text.text or "" if inline_text is not None else ""

    text = value.text or ""

    if cell.attrib.get("t") == "s":
        return shared_strings[int(text)]

    return text


def _cell_column_index(cell_reference: str) -> int:
    letters = re.match(r"([A-Z]+)", cell_reference.upper())

    if letters is None:
        return 1

    index = 0
    for letter in letters.group(1):
        index = index * 26 + ord(letter) - ord("A") + 1
    return index


def _coerce_boolean(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()

        if normalized in _TRUE_STRINGS:
            return True

        if normalized in _FALSE_STRINGS:
            return False

    return None


def _is_empty_value(value: Any) -> bool:
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    if pd.isna(value):
        return True

    if isinstance(value, str):
        return value.strip().lower() in _EMPTY_STRINGS

    if isinstance(value, int | float) and value == 0:
        return True

    return False


def _format_value(value: Any) -> str:
    if isinstance(value, str):
        return value.strip()

    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        return f"{value:g}"

    return str(value)


def _designation_lines(features: Mapping[str, Any]) -> list[str]:
    designation = features.get("product_description")
    transliterated = transliterate_designation(
        designation,
        features.get("cable_family"),
    )

    return [transliterated] if transliterated else []
