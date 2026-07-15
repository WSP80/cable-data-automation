from src.generators.registry import GENERATORS
from src.models.enums import ArmorType, InsulationMaterial, ScreenType, SheathMaterial
from src.models.ucm import UCM
from src.pipeline.generator_pipeline import GeneratorPipeline


def test_atomkip_generator_builds_designation_from_ucm():
    ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=1.5,
        rated_voltage_v=690,
    )

    mark = GENERATORS["atomkip"].generate(ucm)

    assert mark == "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423 2\u04452\u04451,5 690\u0412"


def test_atomkip_generator_applies_mark_formation_rules():
    ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=1.5,
        conductor_flexibility_class=5,
        insulation_material=InsulationMaterial.PVC.value,
        overall_screen=ScreenType.ALUMINUM_FOIL.value,
        sheath_material=SheathMaterial.PVC.value,
        flame_retardant=True,
        low_smoke=True,
        cold_resistant=True,
        uv_resistant=True,
        rated_voltage_v=690,
    )

    mark = GENERATORS["atomkip"].generate(ucm)

    assert mark == (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0412\u041e\u0444\u0412\u043d\u0433(\u0410)-LS-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04451,5\u043a\u043b5 690\u0412"
    )


def test_atomkip_generator_builds_mark_with_individual_and_lapped_screen():
    ucm = UCM(
        core_groups=4,
        group_type="pair",
        cross_section_mm2=1.5,
        conductor_flexibility_class=3,
        individual_screen=ScreenType.ALUMINUM_FOIL.value,
        insulation_material=InsulationMaterial.PVC.value,
        overall_screen=ScreenType.COMBINED.value,
        sheath_material=SheathMaterial.PVC.value,
        flame_retardant=True,
        low_smoke=True,
        uv_resistant=True,
        rated_voltage_v=690,
    )

    mark = GENERATORS["atomkip"].generate(ucm)

    assert mark == (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u0412\u041e\u0444\u043b\u0412\u043d\u0433(\u0410)-LS-"
        "\u0423\u0424 4\u04452\u04451,5\u043a\u043b3 690\u0412"
    )


def test_atomkip_generator_builds_mark_with_ps_om_p_and_frhf():
    ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=2.5,
        conductor_flexibility_class=5,
        individual_screen=ScreenType.ALUMINUM_FOIL.value,
        insulation_material=InsulationMaterial.XLPO.value,
        overall_screen=ScreenType.COPPER_BRAID.value,
        sheath_material=SheathMaterial.HALOGEN_FREE.value,
        flame_retardant=True,
        fire_resistant=True,
        halogen_free=True,
        cold_resistant=True,
        uv_resistant=True,
        rated_voltage_v=300,
    )

    mark = GENERATORS["atomkip"].generate(ucm)

    assert mark == (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0418\u0444\u041f\u0441\u041e\u043c\u041f\u043d\u0433(\u0410)-FRHF-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04452,5\u043a\u043b5 300\u0412"
    )


def test_atomkip_generator_distinguishes_copper_braid_and_copper_foil():
    braid_ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=2.5,
        insulation_material=InsulationMaterial.XLPO.value,
        overall_screen=ScreenType.COPPER_BRAID.value,
        sheath_material=SheathMaterial.HALOGEN_FREE.value,
    )
    foil_ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=2.5,
        insulation_material=InsulationMaterial.XLPO.value,
        overall_screen=ScreenType.COPPER_FOIL.value,
        sheath_material=SheathMaterial.HALOGEN_FREE.value,
    )

    assert "\u041f\u0441\u041e\u043c\u041f" in GENERATORS["atomkip"].generate(braid_ucm)
    assert "\u041f\u0441\u041e\u043c\u0444\u041f" in GENERATORS["atomkip"].generate(foil_ucm)


def test_atomkip_generator_builds_mark_with_lapped_screen_armor_and_pvc_sheath():
    ucm = UCM(
        core_groups=2,
        group_type="pair",
        cross_section_mm2=0.5,
        insulation_material=InsulationMaterial.PVC.value,
        overall_screen=ScreenType.COMBINED.value,
        armor_type=ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value,
        sheath_material=SheathMaterial.PVC.value,
        flame_retardant=True,
        low_smoke=True,
        cold_resistant=True,
        uv_resistant=True,
        rated_voltage_v=500,
    )

    mark = GENERATORS["atomkip"].generate(ucm)

    assert mark == (
        "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
        "\u0412\u041e\u0444\u043b\u041a\u0412\u043d\u0433(\u0410)-LS-"
        "\u0425\u041b-\u0423\u0424 2\u04452\u04450,5 500\u0412"
    )


def test_generator_pipeline_can_generate_registered_targets():
    ucm = UCM(core_groups=4, group_type="core", cross_section_mm2=1.0)
    pipeline = GeneratorPipeline(GENERATORS)

    assert pipeline.generate(ucm, "mk") == "\u041c\u041a\u0428\u0412 4\u04451,0"
