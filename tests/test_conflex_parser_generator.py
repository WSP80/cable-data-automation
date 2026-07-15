from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, GroupType, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.models.ucm import UCM
from src.parsers.conflex.parser import ConflexParser


def test_conflex_parser_extracts_plain_pvc_mark():
    ucm = ConflexParser().parse("CONFLEX \u041c\u041a\u0428\u0412 6\u04450,75")

    assert ucm.cable_family == "CONFLEX"
    assert ucm.core_groups == 6
    assert ucm.group_type == GroupType.CORE.value
    assert ucm.cross_section_mm2 == 0.75
    assert ucm.rated_voltage_v == 300
    assert ucm.conductor_flexibility_class == 5
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.total_conductors == 6
    assert ucm.copper_area_mm2 == 4.5


def test_conflex_parser_extracts_screen_armor_and_frls():
    mark = (
        "CONFLEX \u041c\u041a\u042d\u041a\u0428\u0412"
        "\u043d\u0433(\u0410)-FRLS 4\u04452\u04451,0"
    )

    ucm = ConflexParser().parse(mark)

    assert ucm.overall_screen == ScreenType.COPPER_BRAID.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.group_type == GroupType.PAIR.value


def test_conflex_parser_extracts_aluminum_foil_and_hf():
    mark = (
        "CONFLEX \u041c\u041a\u042d\u0444\u0428\u041f"
        "\u043d\u0433(\u0410)-HF 3\u04453\u04452,5"
    )

    ucm = ConflexParser().parse(mark)

    assert ucm.overall_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.insulation_material == InsulationMaterial.HALOGEN_FREE.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
    assert ucm.flame_retardant is True
    assert ucm.halogen_free is True
    assert ucm.group_type == GroupType.TRIPLE.value


def test_conflex_generator_builds_plain_pvc_mark():
    ucm = UCM(
        core_groups=6,
        group_type=GroupType.CORE.value,
        cross_section_mm2=0.75,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
        rated_voltage_v=300,
    )

    mark = GENERATORS["conflex"].generate(ucm)

    assert mark == "CONFLEX \u041c\u041a\u0428\u0412 6\u04450,75 300\u0412"


def test_conflex_generator_builds_armored_frls_pair_mark():
    ucm = UCM(
        core_groups=4,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1,0",
        overall_screen=ScreenType.COPPER_BRAID.value,
        armor_type=ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
        flame_retardant=True,
        fire_resistant=True,
        low_smoke=True,
        rated_voltage_v=300,
    )

    mark = GENERATORS["conflex"].generate(ucm)

    assert mark == (
        "CONFLEX \u041c\u041a\u042d\u041a\u0428\u0412"
        "\u043d\u0433(\u0410)-FRLS 4\u04452\u04451,0 300\u0412"
    )


def test_conflex_parser_generator_adds_default_voltage_for_dataset_shape():
    mark = (
        "CONFLEX \u041c\u041a\u042d\u0444\u0428\u041f"
        "\u043d\u0433(\u0410)-HF 37\u04452\u04451,5"
    )

    ucm = ConflexParser().parse(mark)
    generated = GENERATORS["conflex"].generate(ucm)

    assert ucm.rated_voltage_v == 300
    assert generated == f"{mark} 300\u0412"


def test_conflex_parser_extracts_individual_screen_after_parenthesized_group():
    cases = [
        ("\u044d", ScreenType.COPPER_BRAID.value),
        ("\u044d\u043b", ScreenType.TINNED_COPPER_BRAID.value),
        ("\u044d\u0444", ScreenType.ALUMINUM_FOIL.value),
        ("\u044d\u043c\u0444", ScreenType.COPPER_FOIL.value),
        ("\u044d\u0444\u044d\u043b", ScreenType.COMBINED.value),
    ]

    for token, expected_screen in cases:
        mark = f"CONFLEX \u041c\u041a\u0428\u0412 2\u0445(2\u04450,5){token}"
        ucm = ConflexParser().parse(mark)

        assert ucm.core_groups == 2
        assert ucm.group_type == GroupType.PAIR.value
        assert ucm.cross_section_mm2 == 0.5
        assert ucm.cross_section_designation == "0,5"
        assert ucm.individual_screen == expected_screen


def test_conflex_generator_builds_parenthesized_group_with_individual_screen():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=0.5,
        cross_section_designation="0,5",
        individual_screen=ScreenType.ALUMINUM_FOIL.value,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
        rated_voltage_v=300,
    )

    mark = GENERATORS["conflex"].generate(ucm)

    assert mark == "CONFLEX \u041c\u041a\u0428\u0412 2\u0445(2\u04450,5)\u044d\u0444 300\u0412"


def test_conflex_parser_generator_roundtrip_with_individual_screen():
    mark = "CONFLEX \u041c\u041a\u0428\u0412 2\u0445(2\u04450,5)\u044d\u0444"

    ucm = ConflexParser().parse(mark)
    generated = GENERATORS["conflex"].generate(ucm)

    assert generated == f"{mark} 300\u0412"


def test_conflex_parser_extracts_tail_indexes_before_voltage():
    mark = (
        "CONFLEX \u041c\u041a\u0428\u0412 2\u0445(2\u04450,5)\u044d\u0444 "
        "\u041c-\u0423\u0424-Ex 300\u0412"
    )

    ucm = ConflexParser().parse(mark)

    assert ucm.oil_resistant is True
    assert ucm.uv_resistant is True
    assert ucm.explosive_area_application is True
    assert ucm.intrinsically_safe is False
    assert ucm.rated_voltage_v == 300


def test_conflex_parser_and_generator_handle_intrinsically_safe_tail_index():
    mark = (
        "CONFLEX \u041c\u041a\u0428\u0412 2\u0445(2\u04450,5)\u044d\u0444 "
        "\u041c-\u0423\u0424-Ex-i 300\u0412"
    )

    ucm = ConflexParser().parse(mark)
    generated = GENERATORS["conflex"].generate(ucm)

    assert ucm.oil_resistant is True
    assert ucm.uv_resistant is True
    assert ucm.explosive_area_application is True
    assert ucm.intrinsically_safe is True
    assert generated == mark


def test_conflex_parser_accepts_latin_transliteration():
    mark = "CONFLEX MKEKShVng(A)-FRLS 4x2x1,0 300V"

    ucm = ConflexParser().parse(mark)

    assert ucm.overall_screen == ScreenType.COPPER_BRAID.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value
    assert ucm.insulation_material == InsulationMaterial.PVC.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.flame_retardant is True
    assert ucm.fire_resistant is True
    assert ucm.low_smoke is True
    assert ucm.core_groups == 4
    assert ucm.group_type == GroupType.PAIR.value
    assert ucm.cross_section_mm2 == 1.0
    assert ucm.rated_voltage_v == 300


def test_conflex_parser_accepts_latin_individual_screen_and_tail_indexes():
    mark = "CONFLEX MKShV 2x(2x0,5)ef M-UF-Ex-i 300V"

    ucm = ConflexParser().parse(mark)

    assert ucm.individual_screen == ScreenType.ALUMINUM_FOIL.value
    assert ucm.oil_resistant is True
    assert ucm.uv_resistant is True
    assert ucm.explosive_area_application is True
    assert ucm.intrinsically_safe is True


def test_conflex_generator_can_emit_latin_transliteration():
    ucm = ConflexParser().parse(
        "CONFLEX \u041c\u041a\u042d\u041a\u0428\u0412"
        "\u043d\u0433(\u0410)-FRLS 4\u04452\u04451,0 300\u0412"
    )

    mark = GENERATORS["conflex"].generate(ucm, alphabet="latin")

    assert mark == "CONFLEX MKEKShVng(A)-FRLS 4x2x1,0 300V"


def test_conflex_parser_extracts_conductor_flexibility_class_suffixes():
    assert ConflexParser().parse("CONFLEX \u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043e\u043a").conductor_flexibility_class == 1
    assert ConflexParser().parse("CONFLEX \u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043c\u043a").conductor_flexibility_class == 2
    assert ConflexParser().parse("CONFLEX \u041c\u041a\u0428\u0412 2\u04452\u04451,0").conductor_flexibility_class == 5
    assert ConflexParser().parse("CONFLEX MKShV 2x2x1,0mk").conductor_flexibility_class == 2


def test_conflex_generator_emits_conductor_flexibility_class_suffix():
    ucm = UCM(
        core_groups=2,
        group_type=GroupType.PAIR.value,
        cross_section_mm2=1.0,
        cross_section_designation="1,0",
        conductor_flexibility_class=1,
        insulation_material=InsulationMaterial.PVC.value,
        sheath_material=SheathMaterial.PVC.value,
    )

    mark = GENERATORS["conflex"].generate(ucm)
    latin_mark = GENERATORS["conflex"].generate(ucm, alphabet="latin")

    assert mark == "CONFLEX \u041c\u041a\u0428\u0412 2\u04452\u04451,0\u043e\u043a"
    assert latin_mark == "CONFLEX MKShV 2x2x1,0ok"


def test_conflex_parser_and_generator_use_ltx_for_low_toxicity():
    mark = "CONFLEX \u041c\u041a\u0428\u0412\u043d\u0433(\u0410)-LTx 2\u04452\u04451,0 300\u0412"

    ucm = ConflexParser().parse(mark)

    assert ucm.low_toxicity is True
    assert GENERATORS["conflex"].generate(ucm) == mark
