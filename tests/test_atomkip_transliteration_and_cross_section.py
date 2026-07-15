from src.generators.registry import GENERATORS
from src.generators.atomkip.rules import transliterate_atomkip_mark
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_generator_preserves_cross_section_designation():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u0441\u041e\u0444\u043b\u041a\u041f\u043d\u0433(\u0410)-HF "
        "2\u04452\u04450,50\u043a\u043b1 300\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.cross_section_mm2 == 0.5
    assert ucm.cross_section_designation == "0,50"
    assert GENERATORS["atomkip"].generate(ucm) == mark


def test_atomkip_parser_accepts_latin_transliteration_and_generator_can_emit_latin():
    mark = "ATOMKIP-KUIfPsOfKPng(A)-FRHF-UF-v-i 12x2x1,0kl5 690V"

    ucm = AtomkipParser().parse(mark)

    assert ucm.water_blocking is True
    assert ucm.intrinsically_safe is True
    assert GENERATORS["atomkip"].generate(ucm, alphabet="latin") == mark


def test_atomkip_transliteration_handles_lowercase_screen_m_suffix():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u0441\u041e\u0444\u043c\u041f\u043d\u0433(\u0410)-HF "
        "10\u04453\u04452,5\u043a\u043b5 690\u0412"
    )

    assert (
        transliterate_atomkip_mark(mark)
        == "ATOMKIP-KUPsOfmPng(A)-HF 10x3x2,5kl5 690V"
    )
