from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_extracts_intrinsically_safe_default_blue_color():
    mark = (
        "\u0410\u0422\u041e\u041c\u041A\u0418\u041F-\u041A\u0423"
        "\u041F\u041F\u043D\u0433(\u0410)-HF-i 1\u04452\u04451,0\u043A\u043B5 690\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.intrinsically_safe is True
    assert ucm.sheath_color == "blue"


def test_atomkip_parser_extracts_explicit_color_after_voltage():
    mark = (
        "\u0410\u0422\u041E\u041C\u041A\u0418\u041F-\u041A\u0423"
        "\u041F\u041F\u043D\u0433(\u0410)-HF-i "
        "1\u04452\u04451,0\u043A\u043B5 690\u0412 "
        "(\u043A\u0440\u0430\u0441\u043D\u044B\u0439 \u0441 "
        "\u0441\u0438\u043D\u0438\u043C\u0438 \u043F\u043E\u043B\u043E\u0441\u0430\u043C\u0438)"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.intrinsically_safe is True
    assert ucm.sheath_color == "krasnyy s sinimi polosami"


def test_atomkip_parser_extracts_explosive_area_application_prefix():
    mark = (
        "\u0412\u0437-\u0410\u0422\u041E\u041C\u041A\u0418\u041F-\u041A\u0423"
        "\u041F\u041F\u043D\u0433(\u0410)-HF 1\u04452\u04451,0\u043A\u043B5 690\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.explosive_area_application is True
