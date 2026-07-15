from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import GroupType, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


MARK = (
    "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
    "\u0418\u043c\u041f\u0441\u041e\u043c\u041a\u041f\u043d\u0433(\u0410)-HF-\u0423\u0424 "
    "10\u04454\u04450,5\u043b\u043a\u043b3 300\u0412"
)


def test_atomkip_parser_handles_im_ps_om_k_p_hf_uv_mark():
    ucm = AtomkipParser().parse(MARK)

    assert ucm.core_groups == 10
    assert ucm.group_type == GroupType.QUAD.value
    assert ucm.cross_section_mm2 == 0.5
    assert ucm.conductor_material == ConductorMaterial.CU_TINNED.value
    assert ucm.conductor_flexibility_class == 3
    assert ucm.individual_screen == ScreenType.COPPER_BRAID.value
    assert ucm.insulation_material == InsulationMaterial.XLPO.value
    assert ucm.overall_screen == ScreenType.COPPER_BRAID.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.flame_retardant is True
    assert ucm.halogen_free is True
    assert ucm.uv_resistant is True
    assert ucm.rated_voltage_v == 300


def test_atomkip_generator_round_trips_im_ps_om_k_p_hf_uv_mark():
    ucm = AtomkipParser().parse(MARK)

    assert GENERATORS["atomkip"].generate(ucm) == MARK
