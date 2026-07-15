from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import GroupType, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_handles_ifl_p_of_b_p_hf_mark():
    parser = AtomkipParser()
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u043b\u041f\u041e\u0444\u0411\u041f\u043d\u0433(\u0410)-HF "
        "2\u04452\u04450,75\u043b\u043a\u043b1 300\u0412"
    )

    ucm = parser.parse(mark)

    assert ucm.core_groups == 2
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 0.75
    assert ucm.conductor_material == ConductorMaterial.CU_TINNED.value
    assert ucm.conductor_flexibility_class == 1
    assert ucm.individual_screen == ScreenType.COMBINED.value
    assert ucm.insulation_material == InsulationMaterial.HALOGEN_FREE.value
    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.flame_retardant is True
    assert ucm.halogen_free is True
    assert ucm.rated_voltage_v == 300


def test_atomkip_generator_round_trips_ifl_p_of_b_p_hf_mark():
    parser = AtomkipParser()
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u043b\u041f\u041e\u0444\u0411\u041f\u043d\u0433(\u0410)-HF "
        "2\u04452\u04450,75\u043b\u043a\u043b1 300\u0412"
    )

    ucm = parser.parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == mark
