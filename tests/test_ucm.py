from src.models.enums import ArmorType, ConductorMaterial, ScreenType
from src.models.ucm import UCM


def test_calculate_derived_features_for_pair_cable():
    ucm = UCM(core_groups=2, group_type="pair", cross_section_mm2=1.5)

    ucm.calculate_derived_features()

    assert ucm.total_conductors == 4
    assert ucm.copper_area_mm2 == 6.0


def test_finalize_features_fills_ml_defaults():
    ucm = UCM(core_groups=2, group_type="pair", cross_section_mm2=1.5)

    ucm.finalize_features()

    assert ucm.conductor_material == ConductorMaterial.CU.value
    assert ucm.mica_tape_layers == 0
    assert ucm.individual_screen == ScreenType.NONE.value
    assert ucm.bedding_under_screen is False
    assert ucm.overall_screen == ScreenType.NONE.value
    assert ucm.armor_type == ArmorType.NONE.value
    assert ucm.water_blocking is False
    assert ucm.flame_retardant is False
    assert ucm.fire_resistant is False
    assert ucm.low_smoke is False
    assert ucm.low_toxicity is False
    assert ucm.halogen_free is False
    assert ucm.cold_resistant is False
    assert ucm.uv_resistant is False
    assert ucm.oil_resistant is False
    assert ucm.chemical_resistant is False
    assert ucm.intrinsically_safe is False
    assert ucm.explosive_area_application is False
    assert ucm.sheath_color == "black"
    assert ucm.total_conductors == 4
    assert ucm.copper_area_mm2 == 6.0
