from src.generators.registry import GENERATORS
from src.models.enums import ScreenType
from src.models.ucm import UCM
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_distinguishes_im_and_imf():
    parser = AtomkipParser()

    im = parser.parse(
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043c\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-HF "
        "2\u04452\u04450,75\u043b\u043a\u043b1 300\u0412"
    )
    imf = parser.parse(
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043c\u0444\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-HF "
        "2\u04452\u04450,75\u043b\u043a\u043b1 300\u0412"
    )

    assert im.individual_screen == ScreenType.COPPER_BRAID.value
    assert imf.individual_screen == ScreenType.COPPER_FOIL.value


def test_atomkip_generator_distinguishes_im_and_imf():
    braid_ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=0.75,
        individual_screen=ScreenType.COPPER_BRAID.value,
    )
    foil_ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=0.75,
        individual_screen=ScreenType.COPPER_FOIL.value,
    )

    assert "\u0418\u043c " not in GENERATORS["atomkip"].generate(foil_ucm)
    assert "\u0418\u043c\u0444" in GENERATORS["atomkip"].generate(foil_ucm)
    assert "\u0418\u043c" in GENERATORS["atomkip"].generate(braid_ucm)


def test_atomkip_parser_and_generator_support_tinned_copper_individual_screen():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043b\u0412\u041e\u0444\u0412 2\u04452\u04451,0\u043a\u043b5 300\u0412"
    )

    ucm = AtomkipParser().parse(mark)
    generated = GENERATORS["atomkip"].generate(ucm)
    latin_mark = GENERATORS["atomkip"].generate(ucm, alphabet="latin")

    assert ucm.individual_screen == ScreenType.TINNED_COPPER_BRAID.value
    assert generated == mark
    assert latin_mark.startswith("ATOMKIP-KUIlVOfV")
