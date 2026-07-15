from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, ConductorMaterial, FillerMaterial
from src.models.enums import GroupType, InsulationMaterial, ScreenType, SheathMaterial
from src.models.ucm import UCM
from src.parsers.mk.parser import MKParser
from src.parsers.mk.rules import NO_FILLER


def test_mk_parser_extracts_real_armored_frls_mark():
    mark = "\u041c\u041a\u042d\u0444\u0411\u0428\u0412\u0437\u043d\u0433(\u0410)-FRLS (2\u04452\u04451,0) 660"

    ucm = MKParser().parse(mark)

    assert ucm.cable_family == "MK"
    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.filler_material == FillerMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.0
    assert ucm.rated_voltage_v == 660


def test_mk_parser_extracts_group_screen_and_special_indexes():
    mark = (
        "\u041c\u041a\u042d\u0444\u041a\u0428\u0412\u0437\u043d\u0433(\u0410)-FRLS "
        "(10\u0445(2\u04451,0)\u044d\u0444 \u0425\u041b-\u0423\u0424 660"
    )

    ucm = MKParser().parse(mark)

    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.core_groups == 10
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cold_resistant is True
    assert ucm.uv_resistant is True


def test_mk_parser_extracts_no_filler_hf_and_voltage():
    mark = "\u041c\u041a\u042d\u0444\u0428\u041f\u043d\u0433(\u0410)-HF (2\u0445(2\u04450,50)\u044d\u0444 \u041e\u041f-\u0425\u041b-\u0423\u0424 300"

    ucm = MKParser().parse(mark)

    assert ucm.insulation_material == InsulationMaterial.HALOGEN_FREE.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.halogen_free is True
    assert ucm.filler_material == NO_FILLER
    assert ucm.rated_voltage_v == 300


def test_mk_parser_accepts_latin_transliteration():
    mark = "MKEfBShVzng(A)-FRLS (2x2x1,0) HL-UF 660"

    ucm = MKParser().parse(mark)

    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.cold_resistant is True
    assert ucm.uv_resistant is True


def test_mk_generator_builds_cyrillic_and_latin_marks():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1,0",
        overall_screen=ScreenType.ALUMINUM_FOIL.value,
        armor_type=ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
        filler_material=FillerMaterial.PVC.value,
        flame_retardant=True,
        fire_resistant=True,
        low_smoke=True,
        cold_resistant=True,
        uv_resistant=True,
        rated_voltage_v=660,
    )

    mark = GENERATORS["mk"].generate(ucm)
    latin_mark = GENERATORS["mk"].generate(ucm, alphabet="latin")

    assert mark == (
        "\u041c\u041a\u042d\u0444\u0411\u0428\u0412\u0437\u043d\u0433(\u0410)-FRLS "
        "(2\u04452\u04451,0) \u0425\u041b-\u0423\u0424 660"
    )
    assert latin_mark == "MKEfBShVzng(A)-FRLS (2x2x1,0) HL-UF 660"


def test_mk_generator_builds_group_screen_mark():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1,0",
        individual_screen=ScreenType.TINNED_COPPER_BRAID.value,
        overall_screen=ScreenType.COPPER_BRAID.value,
        armor_type=ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
        filler_material=FillerMaterial.PVC.value,
        water_blocking=True,
        conductor_material=ConductorMaterial.CU_TINNED.value,
        flame_retardant=True,
        low_smoke=True,
        cold_resistant=True,
        uv_resistant=True,
        rated_voltage_v=660,
    )

    mark = GENERATORS["mk"].generate(ucm)

    assert mark == (
        "\u041c\u041a\u042d\u043c\u041a\u0428\u0412\u0432\u0437\u043b\u043d\u0433(\u0410)-LS "
        "(2\u0445(2\u04451,0)\u044d\u043c\u043b \u0425\u041b-\u0423\u0424 660"
    )


def test_mk_parser_extracts_conductor_flexibility_class_suffixes():
    assert MKParser().parse("\u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043e\u043a 660").conductor_flexibility_class == 1
    assert MKParser().parse("\u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043c\u043a 660").conductor_flexibility_class == 2
    assert MKParser().parse("\u041c\u041a\u0428\u0412 2\u04452\u04451,0 660").conductor_flexibility_class == 5
    assert MKParser().parse("MKShV 2x2x1,0mk 660").conductor_flexibility_class == 2


def test_mk_generator_emits_conductor_flexibility_class_suffix():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1,0",
        conductor_flexibility_class=2,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
    )

    mark = GENERATORS["mk"].generate(ucm)
    latin_mark = GENERATORS["mk"].generate(ucm, alphabet="latin")

    assert mark == "\u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043c\u043a"
    assert latin_mark == "MKShV 2x2x1,0mk"
