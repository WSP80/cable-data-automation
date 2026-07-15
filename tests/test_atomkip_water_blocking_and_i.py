from src.generators.registry import GENERATORS
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_handles_water_blocking_before_i_suffix():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u041f\u0441\u041e\u0444\u041a\u041f\u043d\u0433(\u0410)-FRHF-"
        "\u0423\u0424-\u0432-i 12\u04452\u04451,0\u043a\u043b5 690\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.water_blocking is True
    assert ucm.intrinsically_safe is True


def test_atomkip_generator_round_trips_water_blocking_before_i_suffix():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u041F\u0441\u041E\u0444\u041A\u041F\u043D\u0433(\u0410)-FRHF-"
        "\u0423\u0424-\u0432-i 12\u04452\u04451,0\u043A\u043B5 690\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == mark
