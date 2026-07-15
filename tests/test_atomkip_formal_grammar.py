from src.models.enums import ArmorType, InsulationMaterial, ScreenType, SheathMaterial
from src.parsers.atomkip.parser import AtomkipParser


def test_atomkip_parser_reads_formal_construction_order():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u043c\u0444\u0420\u044d\u041e\u043c\u0444\u0411\u0412\u043d\u0433(\u0410)-"
        "LS-\u0410\u0421-\u041c 2\u04452\u04451,0\u043a\u043b3 300\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.individual_screen == ScreenType.COPPER_FOIL.value
    assert ucm.insulation_material == InsulationMaterial.EPR.value
    assert ucm.overall_screen == ScreenType.COPPER_FOIL.value
    assert ucm.armor_type == ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value
    assert ucm.sheath_material == SheathMaterial.PVC.value
    assert ucm.low_smoke is True
    assert ucm.chemical_resistant is True
    assert ucm.oil_resistant is True


def test_atomkip_parser_reads_mark_without_optional_construction_parts():
    mark = (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0420\u043a\u041f\u043d\u0433(\u0410) 1\u04451,0\u043a\u043b1 300\u0412"
    )

    ucm = AtomkipParser().parse(mark)

    assert ucm.individual_screen == ScreenType.NONE.value
    assert ucm.insulation_material == InsulationMaterial.CERAMIFIABLE_SILICONE.value
    assert ucm.overall_screen == ScreenType.NONE.value
    assert ucm.armor_type == ArmorType.NONE.value
    assert ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value
