from src.generators.registry import GENERATORS
from src.models.enums import ConductorMaterial, InsulationMaterial
from src.models.enums import GroupType, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_handles_im_p_om_p_hf_water_blocking_mark():
    parser = AtomkipParser()
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043c\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-HF-\u0432 "
        "10\u04453\u04451,0\u043b\u043a\u043b3 690\u0412"
    )

    ucm = parser.parse(mark)

    assert ucm.core_groups == 10
    assert ucm.group_type == GroupType.TRIPLE.value
    assert ucm.cross_section_mm2 == 1.0
    assert ucm.conductor_material == ConductorMaterial.CU_TINNED.value
    assert ucm.conductor_flexibility_class == 3
    assert ucm.individual_screen == ScreenType.COPPER_BRAID.value
    assert ucm.insulation_material == InsulationMaterial.HALOGEN_FREE.value
    assert ucm.overall_screen == ScreenType.COPPER_BRAID.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.flame_retardant is True
    assert ucm.halogen_free is True
    assert ucm.water_blocking is True
    assert ucm.rated_voltage_v == 690


def test_atomkip_generator_round_trips_im_p_om_p_hf_water_blocking_mark():
    parser = AtomkipParser()
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043c\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-HF-\u0432 "
        "10\u04453\u04451,0\u043b\u043a\u043b3 690\u0412"
    )

    ucm = parser.parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == mark
