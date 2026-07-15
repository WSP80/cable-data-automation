from src.generators.registry import GENERATORS
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_generator_round_trips_intrinsically_safe_suffix():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u041f\u043d\u0433(\u0410)-HF-i 1\u04452\u04451,0\u043a\u043b5 690\u0412"
    )
    ucm = AtomkipParser().parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == mark


def test_atomkip_generator_round_trips_explicit_color():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u041f\u043d\u0433(\u0410)-HF-i "
        "1\u04452\u04451,0\u043a\u043b5 690\u0412 "
        "(\u043a\u0440\u0430\u0441\u043d\u044b\u0439 \u0441 "
        "\u0441\u0438\u043d\u0438\u043c\u0438 \u043f\u043e\u043b\u043e\u0441\u0430\u043c\u0438)"
    )
    expected = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u041f\u043d\u0433(\u0410)-HF-i "
        "1\u04452\u04451,0\u043a\u043b5 690\u0412 "
        "(krasnyy s sinimi polosami)"
    )
    ucm = AtomkipParser().parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == expected


def test_atomkip_generator_round_trips_explosive_area_prefix():
    mark = (
        "\u0412\u0437-\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u041f\u041f\u043d\u0433(\u0410)-HF 1\u04452\u04451,0\u043a\u043b5 690\u0412"
    )
    ucm = AtomkipParser().parse(mark)

    assert GENERATORS["atomkip"].generate(ucm) == mark


def test_atomkip_generator_and_parser_use_ltx_for_low_toxicity():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0412\u041e\u0444\u0412\u043d\u0433(\u0410)-LTx 2\u04452\u04451,0\u043a\u043b5 300\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.low_toxicity is True
    assert GENERATORS["atomkip"].generate(ucm) == mark
