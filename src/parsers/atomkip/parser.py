from src.models.ucm import UCM
from src.parsers.base_parser import BaseParser
from src.parsers.atomkip.rules import (
    extract_armor_type,
    extract_conductor_material,
    extract_conductor_flexibility_class,
    extract_individual_screen,
    extract_insulation_material,
    extract_mica_tape_layers,
    extract_overall_screen,
    extract_sheath_material,
    extract_sheath_color,
    has_cold_resistant,
    has_explosive_area_application,
    has_flame_retardant,
    has_fire_resistant,
    has_fire_resistant_halogen_free,
    has_aggressive_environment_resistance,
    has_halogen_free,
    has_intrinsically_safe_execution,
    has_low_toxicity,
    has_low_smoke,
    has_oil_resistance,
    has_uv_resistant,
    has_water_blocking,
)

from src.parsers.feature_extractors.core_groups import extract_core_groups
from src.parsers.feature_extractors.group_type import extract_group_type
from src.parsers.feature_extractors.cross_section import extract_cross_section_mm2
from src.parsers.feature_extractors.cross_section import extract_cross_section_designation
from src.parsers.feature_extractors.voltage import extract_rated_voltage_v


class AtomkipParser(BaseParser):
    """
    Parser for ATOMKIP cable designations.
    """

    def parse(self, designation: str, comment: str | None = None) -> UCM:

        ucm = UCM()

        # Structural Features
        ucm.cable_family = "ATOMKIP-KU"

        ucm.core_groups = extract_core_groups(designation)

        ucm.group_type = extract_group_type(designation)

        ucm.cross_section_mm2 = extract_cross_section_mm2(designation)
        ucm.cross_section_designation = extract_cross_section_designation(designation)

        ucm.rated_voltage_v = extract_rated_voltage_v(designation)

        ucm.conductor_flexibility_class = extract_conductor_flexibility_class(
            designation
        )
        ucm.conductor_material = extract_conductor_material(designation)

        ucm.individual_screen = extract_individual_screen(designation)
        ucm.insulation_material = extract_insulation_material(designation)
        ucm.overall_screen = extract_overall_screen(designation)
        ucm.armor_type = extract_armor_type(designation)
        ucm.sheath_material = extract_sheath_material(designation)

        ucm.flame_retardant = has_flame_retardant(designation)

        if has_fire_resistant_halogen_free(designation):
            ucm.fire_resistant = True
            ucm.halogen_free = True

        if has_fire_resistant(designation):
            ucm.fire_resistant = True

        if has_halogen_free(designation):
            ucm.halogen_free = True

        ucm.mica_tape_layers = extract_mica_tape_layers(
            designation,
            ucm.insulation_material,
            comment=comment,
        )

        if has_water_blocking(designation):
            ucm.water_blocking = True

        ucm.low_smoke = has_low_smoke(designation)

        ucm.low_toxicity = has_low_toxicity(designation)

        ucm.cold_resistant = has_cold_resistant(designation)

        ucm.uv_resistant = has_uv_resistant(designation)

        ucm.chemical_resistant = has_aggressive_environment_resistance(designation)

        ucm.oil_resistant = has_oil_resistance(designation)

        ucm.intrinsically_safe = has_intrinsically_safe_execution(designation)

        ucm.explosive_area_application = has_explosive_area_application(designation)

        ucm.sheath_color = extract_sheath_color(designation)

        # Defaults and Derived Features
        ucm.finalize_features()

        return ucm
