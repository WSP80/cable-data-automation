from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile


OUTPUT_PATH = Path("reports/tables/feature_mark_matrix.xlsx")


@dataclass(frozen=True)
class FeatureMarkRow:
    feature: str
    atomkip: str
    conflex: str
    toflex: str
    mk: str


HEADERS = ["Фича", "ATOMKIP-KU", "CONFLEX", "TOFLEX-KU", "MK"]


def build_feature_mark_rows() -> list[FeatureMarkRow]:
    return [
        FeatureMarkRow("Базовая марка", "АТОМКИП-КУ", "CONFLEX МК", "ТОФЛЕКС КУ", "МК"),
        FeatureMarkRow("Индивидуальный экран: медная проволока", "Им", "э", "Э", "Э + э/эм после сечения"),
        FeatureMarkRow("Индивидуальный экран: медная луженая проволока", "Ил", "эл", "Эл", "Э + эмл после сечения"),
        FeatureMarkRow("Индивидуальный экран: алюмополимерная/алюмофольгированная лента", "Иф", "эф", "Эа", "Э + эф после сечения"),
        FeatureMarkRow("Индивидуальный экран: меднофольгированная лента", "Имф", "эмф", "Эм", "Э + эмф после сечения"),
        FeatureMarkRow("Индивидуальный экран: комбинированный", "Ифл", "эфэл", "ЭаЭл", "Э + эфэмл после сечения"),
        FeatureMarkRow("Общий экран: медная проволока", "Ом", "Э", "Э", "Эм"),
        FeatureMarkRow("Общий экран: медная луженая проволока", "Ол", "Эл", "Эл", "Эмл"),
        FeatureMarkRow("Общий экран: алюмополимерная/алюмофольгированная лента", "Оф", "Эф", "Эа", "Эф"),
        FeatureMarkRow("Общий экран: меднофольгированная лента", "Омф", "Эмф", "Эм", "Эмф"),
        FeatureMarkRow("Общий экран: комбинированный", "Офл", "ЭфЭ", "ЭаЭл", "ЭфЭмл"),
        FeatureMarkRow("Броня: стальные оцинкованные ленты", "Б", "Б", "Б", "Б"),
        FeatureMarkRow("Броня: стальные оцинкованные проволоки", "К", "К", "К", "К"),
        FeatureMarkRow("Изоляция/материал: ПВХ", "В", "В", "В", "В"),
        FeatureMarkRow("Изоляция/материал: безгалогенная композиция", "П", "П", "П", "П"),
        FeatureMarkRow("Изоляция/материал: сшитый полиолефин", "Пс", "Пс", "Пс", "Пс"),
        FeatureMarkRow("Изоляция/материал: этиленпропиленовая резина", "Рэ", "Р", "—", "Р"),
        FeatureMarkRow("Изоляция/материал: кремнеорганическая резина", "Рк", "—", "—", "С"),
        FeatureMarkRow("Оболочка: ПВХ", "В", "В", "В", "В"),
        FeatureMarkRow("Оболочка: безгалогенная композиция", "П", "П", "П", "П"),
        FeatureMarkRow("Водоблокирующий элемент", "в", "в", "в", "в"),
        FeatureMarkRow("Заполнение", "—", "—", "—", "з"),
        FeatureMarkRow("Без внутреннего заполнения", "—", "—", "—", "ОП"),
        FeatureMarkRow("Луженая медная жила", "л перед кл", "л", "л после сечения", "л"),
        FeatureMarkRow("Класс гибкости жил: 1", "кл1", "ок после сечения", "ок после сечения", "ок после сечения"),
        FeatureMarkRow("Класс гибкости жил: 2", "кл2", "мк после сечения", "мк после сечения", "мк после сечения"),
        FeatureMarkRow("Класс гибкости жил: 5", "кл5", "без обозначения", "без обозначения", "без обозначения"),
        FeatureMarkRow("Показатель пожарной опасности: нг(А)", "нг(А)", "нг(А)", "нг(А)", "нг(А)"),
        FeatureMarkRow("Огнестойкость", "FR", "FR", "FR", "FR"),
        FeatureMarkRow("Низкое дымо- и газовыделение", "LS", "LS", "LS", "LS"),
        FeatureMarkRow("Безгалогенное исполнение", "HF", "HF", "HF", "HF"),
        FeatureMarkRow("Низкая токсичность продуктов горения", "LTx", "LTx", "LTx", "LTx"),
        FeatureMarkRow("Холодостойкость", "ХЛ", "ХЛ", "ХЛ", "ХЛ"),
        FeatureMarkRow("УФ-стойкость", "УФ", "УФ", "УФ", "УФ"),
        FeatureMarkRow("Маслобензостойкость", "М", "М", "М", "М"),
        FeatureMarkRow("Химическая стойкость", "АС", "—", "—", "—"),
        FeatureMarkRow("Взрывоопасные зоны", "Вз- перед маркой", "Ex", "—", "Ex"),
        FeatureMarkRow("Искробезопасные сети", "i", "Ex-i", "i", "Ex-i"),
        FeatureMarkRow("Синяя оболочка", "blue в скобках, если не по умолчанию", "по Ex-i умолчанию", "с", "с"),
        FeatureMarkRow("Красная оболочка", "red в скобках", "—", "—", "к"),
        FeatureMarkRow("Серая оболочка", "gray в скобках", "—", "—", "серый"),
        FeatureMarkRow("Конструкция: одиночные жилы", "NхS", "NхS", "NхS", "NхS"),
        FeatureMarkRow("Конструкция: пары", "Nх2хS", "Nх2хS", "Nх2хS", "Nх2хS"),
        FeatureMarkRow("Конструкция: тройки", "Nх3хS", "Nх3хS", "Nх3хS", "Nх3хS"),
        FeatureMarkRow("Конструкция: четверки", "Nх4хS", "Nх4хS", "Nх4хS", "Nх4хS"),
        FeatureMarkRow("Конструкция: пятерки", "—", "—", "—", "Nх5хS"),
        FeatureMarkRow("Индивидуальный экран группы в конструкции", "префикс И*", "Nх(2хS)э*", "префикс Э* перед изоляцией", "Nх(2хS)э*"),
        FeatureMarkRow("Общий экран в конструкции", "префикс О*", "префикс Э*", "префикс Э* после изоляции", "(Nх...)"),
        FeatureMarkRow("Напряжение: 300 В", "300В", "300В", "300", "300"),
        FeatureMarkRow("Напряжение: 500 В", "500В", "500В", "500", "500"),
        FeatureMarkRow("Напряжение: 660 В", "660В", "660В", "660", "660"),
        FeatureMarkRow("Напряжение: 690 В", "690В", "—", "—", "—"),
    ]


def build_feature_mark_matrix() -> list[list[str]]:
    rows = [HEADERS]
    rows.extend(
        [row.feature, row.atomkip, row.conflex, row.toflex, row.mk]
        for row in build_feature_mark_rows()
    )

    return rows


def export_feature_mark_matrix(output_path: Path = OUTPUT_PATH) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_xlsx(output_path, build_feature_mark_matrix())

    return output_path


def write_xlsx(path: Path, rows: Iterable[Iterable[str]]) -> None:
    materialized_rows = [list(row) for row in rows]

    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", root_relationships_xml())
        archive.writestr("docProps/app.xml", app_properties_xml())
        archive.writestr("docProps/core.xml", core_properties_xml())
        archive.writestr("xl/workbook.xml", workbook_xml())
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_relationships_xml())
        archive.writestr("xl/styles.xml", styles_xml())
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml(materialized_rows))


def worksheet_xml(rows: list[list[str]]) -> str:
    row_xml = []

    for row_index, row in enumerate(rows, start=1):
        cell_xml = []

        for column_index, value in enumerate(row, start=1):
            reference = f"{column_name(column_index)}{row_index}"
            style = 1 if row_index == 1 else 0
            cell_xml.append(
                f'<c r="{reference}" t="inlineStr" s="{style}">'
                f"<is><t>{escape(str(value))}</t></is></c>"
            )

        row_xml.append(f'<row r="{row_index}">{"".join(cell_xml)}</row>')

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheetViews>
    <sheetView workbookViewId="0">
      <pane ySplit="1" xSplit="1" topLeftCell="B2" activePane="bottomRight" state="frozen"/>
      <selection pane="bottomRight" activeCell="B2" sqref="B2"/>
    </sheetView>
  </sheetViews>
  <cols>
    <col min="1" max="1" width="48" customWidth="1"/>
    <col min="2" max="5" width="24" customWidth="1"/>
  </cols>
  <sheetData>{"".join(row_xml)}</sheetData>
  <autoFilter ref="A1:E{len(rows)}"/>
</worksheet>"""


def column_name(index: int) -> str:
    name = ""

    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name

    return name


def content_types_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>"""


def root_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>"""


def workbook_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
 xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets>
    <sheet name="Feature matrix" sheetId="1" r:id="rId1"/>
  </sheets>
</workbook>"""


def workbook_relationships_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>"""


def styles_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="2">
    <font><sz val="11"/><name val="Calibri"/></font>
    <font><b/><color rgb="FFFFFFFF"/><sz val="11"/><name val="Calibri"/></font>
  </fonts>
  <fills count="3">
    <fill><patternFill patternType="none"/></fill>
    <fill><patternFill patternType="gray125"/></fill>
    <fill><patternFill patternType="solid"><fgColor rgb="FF1F4E79"/><bgColor indexed="64"/></patternFill></fill>
  </fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="2">
    <xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment wrapText="1" vertical="top"/></xf>
    <xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFill="1" applyFont="1" applyAlignment="1"><alignment wrapText="1" horizontal="center" vertical="center"/></xf>
  </cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>"""


def app_properties_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
 xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex</Application>
</Properties>"""


def core_properties_xml() -> str:
    timestamp = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:dcterms="http://purl.org/dc/terms/"
 xmlns:dcmitype="http://purl.org/dc/dcmitype/"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:creator>Codex</dc:creator>
  <cp:lastModifiedBy>Codex</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{timestamp}</dcterms:modified>
</cp:coreProperties>"""


def main() -> None:
    output_path = export_feature_mark_matrix()
    print(f"rows: {len(build_feature_mark_rows())}")
    print(f"output_file: {output_path}")


if __name__ == "__main__":
    main()
