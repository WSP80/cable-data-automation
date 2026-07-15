from src.models.enums import GroupType
from src.models.enums import ArmorType, InsulationMaterial, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_extracts_main_structural_features():
    parser = AtomkipParser()

    ucm = parser.parse("ATOMKIP-KU 2x2x1,5 690V")

    assert ucm.cable_family == "ATOMKIP-KU"
    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.5
    assert ucm.rated_voltage_v == 690
    assert ucm.total_conductors == 4
    assert ucm.copper_area_mm2 == 6.0


def test_atomkip_parser_extracts_mark_formation_flags():
    parser = AtomkipParser()
    designation = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0412\u041e\u0444\u0412\u043d\u0433(A)-LS-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04451,5\u043a\u043b5 690\u0412"
    )

    ucm = parser.parse(designation)

    assert ucm.flame_retardant is True
    assert ucm.low_smoke is True
    assert ucm.cold_resistant is True
    assert ucm.uv_resistant is True
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.conductor_flexibility_class == 5


def test_atomkip_parser_extracts_individual_and_lapped_overall_screen():
    parser = AtomkipParser()
    designation = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u0412\u041e\u0444\u043b\u0412\u043d\u0433(\u0410)-LS-"
        "\u0423\u0424 4\u04452\u04451,5\u043a\u043b3 690\u0412"
    )

    ucm = parser.parse(designation)

    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.COMBINED.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.low_smoke is True
    assert ucm.uv_resistant is True
    assert ucm.conductor_flexibility_class == 3


def test_atomkip_parser_accepts_latin_transcription():
    parser = AtomkipParser()

    ucm = parser.parse("ATOMKIP-KUIfVOflVng(A)-LS-UF 4x2x1,5kl3 690V")

    assert ucm.core_groups == 4
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.5
    assert ucm.conductor_flexibility_class == 3
    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.COMBINED.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.low_smoke is True
    assert ucm.uv_resistant is True
    assert ucm.rated_voltage_v == 690


def test_atomkip_parser_extracts_ps_om_p_and_frhf():
    parser = AtomkipParser()
    designation = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u041f\u0441\u041e\u043c\u041f\u043d\u0433(\u0410)-FRHF-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04452,5\u043a\u043b5 300\u0412"
    )

    ucm = parser.parse(designation)

    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 2.5
    assert ucm.conductor_flexibility_class == 5
    assert ucm.insulation_material == InsulationMaterial.XLPO.value
    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.overall_screen == ScreenType.COPPER_BRAID.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.flame_retardant is True
    assert ucm.fire_resistant is True
    assert ucm.halogen_free is True
    assert ucm.cold_resistant is True
    assert ucm.uv_resistant is True
    assert ucm.rated_voltage_v == 300


def test_atomkip_parser_distinguishes_om_and_omf():
    parser = AtomkipParser()

    om = parser.parse(
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u0441\u041e\u043c\u041f 2\u04452\u04452,5\u043a\u043b5 300\u0412"
    )
    omf = parser.parse(
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u0441\u041e\u043c\u0444\u041f 2\u04452\u04452,5\u043a\u043b5 300\u0412"
    )

    assert om.overall_screen == ScreenType.COPPER_BRAID.value
    assert omf.overall_screen == ScreenType.COPPER_FOIL.value


def test_atomkip_parser_extracts_lapped_screen_armor_and_pvc_sheath():
    parser = AtomkipParser()
    designation = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0412\u041e\u0444\u043b\u041a\u0412\u043d\u0433(\u0410)-LS-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04450,5 500\u0412"
    )

    ucm = parser.parse(designation)

    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.COMBINED.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 0.5
    assert ucm.rated_voltage_v == 500


def test_atomkip_parser_repairs_common_mojibake():
    parser = AtomkipParser()
    mojibake_x = "\u0445".encode("utf-8").decode("cp1251")
    mojibake_v = "\u0412".encode("utf-8").decode("cp1251")
    mojibake = f"ATOMKIP-KU 2{mojibake_x}2{mojibake_x}1,5 690{mojibake_v}"

    ucm = parser.parse(mojibake)

    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.5
    assert ucm.rated_voltage_v == 690
