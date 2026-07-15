from src.models.enums import SheathMaterial
from src.models.ucm import UCM
from src.parsers.base_parser import BaseParser
from src.parsers.conflex.rules import extract_conflex_core_groups
from src.parsers.conflex.rules import extract_conflex_conductor_flexibility_class
from src.parsers.conflex.rules import extract_conflex_cross_section_designation
from src.parsers.conflex.rules import extract_conflex_cross_section_mm2
from src.parsers.conflex.rules import extract_conflex_group_type
from src.parsers.conflex.rules import extract_individual_screen
from src.parsers.conflex.rules import has_cold_resistant, has_explosive_area_application
from src.parsers.conflex.rules import has_fire_resistant, has_flame_retardant
from src.parsers.conflex.rules import has_halogen_free, has_intrinsically_safe_execution
from src.parsers.conflex.rules import has_low_smoke, has_low_toxicity
from src.parsers.conflex.rules import has_oil_resistance, has_uv_resistant
from src.parsers.conflex.rules import parse_mark_parts
from src.parsers.feature_extractors.voltage import extract_rated_voltage_v


class ConflexParser(BaseParser):
    """
    Parser for CONFLEX cable designations.
    """

    def parse(self, designation: str, comment: str | None = None) -> UCM:
        ucm = UCM()
        parts = parse_mark_parts(designation)

        ucm.cable_family = "CONFLEX"
        ucm.core_groups = extract_conflex_core_groups(designation)
        ucm.group_type = extract_conflex_group_type(designation)
        ucm.cross_section_mm2 = extract_conflex_cross_section_mm2(designation)
        ucm.cross_section_designation = extract_conflex_cross_section_designation(
            designation
        )
        ucm.rated_voltage_v = extract_rated_voltage_v(designation) or 300
        ucm.conductor_flexibility_class = extract_conflex_conductor_flexibility_class(
            designation
        )

        ucm.overall_screen = parts.overall_screen
        ucm.individual_screen = extract_individual_screen(designation)
        ucm.armor_type = parts.armor_type
        ucm.sheath_material = parts.sheath_material
        ucm.insulation_material = parts.insulation_material
        ucm.conductor_material = parts.conductor_material
        ucm.water_blocking = parts.water_blocking

        ucm.flame_retardant = has_flame_retardant(designation)
        ucm.fire_resistant = has_fire_resistant(designation)
        ucm.low_smoke = has_low_smoke(designation)
        ucm.low_toxicity = has_low_toxicity(designation)
        ucm.halogen_free = has_halogen_free(designation)

        if ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value:
            ucm.halogen_free = True

        ucm.cold_resistant = has_cold_resistant(designation)
        ucm.oil_resistant = has_oil_resistance(designation)
        ucm.uv_resistant = has_uv_resistant(designation)
        ucm.explosive_area_application = has_explosive_area_application(designation)
        ucm.intrinsically_safe = has_intrinsically_safe_execution(designation)

        ucm.finalize_features()

        return ucm
