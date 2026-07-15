from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, ConductorMaterial, GroupType
from src.models.enums import InsulationMaterial, ScreenType, SheathMaterial
from src.models.ucm import UCM
from src.parsers.toflex.parser import ToflexParser


def test_toflex_parser_extracts_real_dataset_mark():
    mark = (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u043b\u0412\u043d\u0433(\u0410)-FRLS-\u0425\u041b "
        "2\u04452\u04451 \u0432 - 660"
    )

    ucm = ToflexParser().parse(mark)

    assert ucm.cable_family == "TOFLEX-KU"
    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.0
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.TINNED_COPPER_BRAID.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.cold_resistant is True
    assert ucm.water_blocking is True
    assert ucm.rated_voltage_v == 660


def test_toflex_parser_extracts_group_screen_combined_screen_and_armor():
    mark = (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u042d\u0430\u0412\u042d\u0430\u042d\u043b\u041a\u0412"
        "\u043d\u0433(\u0410)-LS-\u0425\u041b 4\u04452\u04450,5 - 660"
    )

    ucm = ToflexParser().parse(mark)

    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.COMBINED.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.low_smoke is True
    assert ucm.cold_resistant is True


def test_toflex_parser_accepts_latin_transliteration():
    mark = "TOFLEX KUVElVng(A)-FRLS-HL 2x2x1 v - 660"

    ucm = ToflexParser().parse(mark)

    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.TINNED_COPPER_BRAID.value
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.cold_resistant is True
    assert ucm.water_blocking is True
    assert ucm.rated_voltage_v == 660


def test_toflex_parser_extracts_additional_indicators():
    mark = (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u0430\u0412\u043d\u0433(\u0410)-LS-\u0425\u041b-i "
        "12\u04452\u04451\u043b \u0423\u0424 - 660"
    )

    ucm = ToflexParser().parse(mark)

    assert ucm.intrinsically_safe is True
    assert ucm.conductor_material == ConductorMaterial.CU_TINNED.value
    assert ucm.uv_resistant is True
    assert ucm.sheath_color == "blue"


def test_toflex_generator_builds_mark_with_tail_indicators():
    ucm = UCM(
        core_groups=12,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1",
        conductor_material=ConductorMaterial.CU_TINNED.value,
        insulation_material=InsulationMaterial.PVC.value,
        overall_screen=ScreenType.ALUMINUM_FOIL.value,
        sheath_material=SheathMaterial.PVC.value,
        flame_retardant=True,
        low_smoke=True,
        cold_resistant=True,
        intrinsically_safe=True,
        uv_resistant=True,
        sheath_color="blue",
        rated_voltage_v=660,
    )

    mark = GENERATORS["toflex"].generate(ucm)

    assert mark == (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u0430\u0412\u043d\u0433(\u0410)-LS-\u0425\u041b-i "
        "12\u04452\u04451\u043b \u0423\u0424 - 660"
    )


def test_toflex_generator_can_emit_latin_transliteration():
    ucm = ToflexParser().parse(
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u043b\u0412\u043d\u0433(\u0410)-FRLS-\u0425\u041b "
        "2\u04452\u04451 \u0432 - 660"
    )

    mark = GENERATORS["toflex"].generate(ucm, alphabet="latin")

    assert mark == "TOFLEX KUVElVng(A)-FRLS-HL 2x2x1 v - 660"


def test_toflex_parser_accepts_asterisk_core_separator():
    mark = (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u043b\u0412\u043d\u0433(\u0410)-FRLS-\u0425\u041b "
        "2*2*1 \u0432 - 660"
    )

    ucm = ToflexParser().parse(mark)
    generated = GENERATORS["toflex"].generate(ucm)

    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.0
    assert ucm.cross_section_designation == "1"
    assert generated == (
        "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 "
        "\u041a\u0423\u0412\u042d\u043b\u0412\u043d\u0433(\u0410)-FRLS-\u0425\u041b "
        "2\u04452\u04451 \u0432 - 660"
    )


def test_toflex_parser_extracts_conductor_flexibility_class_suffixes():
    assert ToflexParser().parse("\u0422\u041e\u0424\u041b\u0415\u041a\u0421 \u041a\u0423\u0412\u0412 2\u04452\u04451\u043e\u043a").conductor_flexibility_class == 1
    assert ToflexParser().parse("\u0422\u041e\u0424\u041b\u0415\u041a\u0421 \u041a\u0423\u0412\u0412 2\u04452\u04451\u043c\u043a").conductor_flexibility_class == 2
    assert ToflexParser().parse("\u0422\u041e\u0424\u041b\u0415\u041a\u0421 \u041a\u0423\u0412\u0412 2\u04452\u04451").conductor_flexibility_class == 5
    assert ToflexParser().parse("TOFLEX KUVV 2x2x1mk").conductor_flexibility_class == 2


def test_toflex_generator_emits_conductor_flexibility_class_suffix():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1",
        conductor_flexibility_class=2,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
    )

    mark = GENERATORS["toflex"].generate(ucm)
    latin_mark = GENERATORS["toflex"].generate(ucm, alphabet="latin")

    assert mark == "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 \u041a\u0423\u0412\u0412 2\u04452\u04451\u043c\u043a"
    assert latin_mark == "TOFLEX KUVV 2x2x1mk"
