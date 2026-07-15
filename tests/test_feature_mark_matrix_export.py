from pathlib import Path
from zipfile import ZipFile

from scripts.export_feature_mark_matrix import build_feature_mark_matrix
from scripts.export_feature_mark_matrix import export_feature_mark_matrix


def test_feature_mark_matrix_contains_key_designations():
    matrix = build_feature_mark_matrix()
    rows = {row[0]: row for row in matrix[1:]}

    assert matrix[0] == ["Фича", "ATOMKIP-KU", "CONFLEX", "TOFLEX-KU", "MK"]
    assert rows["Индивидуальный экран: медная луженая проволока"][1:] == [
        "Ил",
        "эл",
        "Эл",
        "Э + эмл после сечения",
    ]
    assert rows["Общий экран: алюмополимерная/алюмофольгированная лента"][1:] == [
        "Оф",
        "Эф",
        "Эа",
        "Эф",
    ]
    assert rows["Общий экран: комбинированный"][1:] == [
        "Офл",
        "ЭфЭ",
        "ЭаЭл",
        "ЭфЭмл",
    ]
    assert rows["Луженая медная жила"][1] == "л перед кл"
    assert rows["Низкая токсичность продуктов горения"][1:] == [
        "LTx",
        "LTx",
        "LTx",
        "LTx",
    ]
    assert rows["Класс гибкости жил: 2"][1:] == [
        "кл2",
        "мк после сечения",
        "мк после сечения",
        "мк после сечения",
    ]
    assert rows["Напряжение: 690 В"][1:] == ["690В", "—", "—", "—"]


def test_feature_mark_matrix_export_generates_excel_file(tmp_path: Path):
    output_path = export_feature_mark_matrix(
        tmp_path / "feature_mark_matrix.xlsx"
    )

    assert output_path.exists()

    with ZipFile(output_path) as archive:
        worksheet = archive.read("xl/worksheets/sheet1.xml").decode("utf-8")
        workbook = archive.read("xl/workbook.xml").decode("utf-8")

    assert "Feature matrix" in workbook
    assert "Общий экран: комбинированный" in worksheet
    assert "ЭфЭмл" in worksheet
