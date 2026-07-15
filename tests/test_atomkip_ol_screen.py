from src.generators.registry import GENERATORS
from src.models.enums import InsulationMaterial, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


MARK = (
    "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
    "\u0412\u041e\u043b\u0412\u043d\u0433(\u0410)-FRLS-\u0423\u0424 "
    "10\u04450,5\u043a\u043b3 690\u0412"
)


def test_atomkip_parser_handles_ol_overall_screen():
    ucm = AtomkipParser().parse(MARK)

    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.overall_screen == ScreenType.TINNED_COPPER_BRAID.value
    assert ucm.sheath_material == SheathMaterial.PVC.value


def test_atomkip_generator_round_trips_ol_overall_screen():
    ucm = AtomkipParser().parse(MARK)

    assert GENERATORS["atomkip"].generate(ucm) == MARK
