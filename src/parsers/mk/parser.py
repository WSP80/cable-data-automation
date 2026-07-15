from src.models.enums import ConductorMaterial, ScreenType
from src.models.ucm import UCM
from src.parsers.base_parser import BaseParser
from src.parsers.mk.rules import NO_FILLER
from src.parsers.mk.rules import extract_core_groups, extract_cross_section_designation
from src.parsers.mk.rules import extract_cross_section_mm2
from src.parsers.mk.rules import extract_conductor_flexibility_class
from src.parsers.mk.rules import extract_group_screen
from src.parsers.mk.rules import extract_group_type, extract_rated_voltage_v
from src.parsers.mk.rules import extract_sheath_color, has_cold_resistant
from src.parsers.mk.rules import has_explosive_area_application, has_fire_resistant
from src.parsers.mk.rules import has_flame_retardant, has_halogen_free
from src.parsers.mk.rules import has_intrinsically_safe_execution, has_low_smoke
from src.parsers.mk.rules import has_low_toxicity, has_no_filler_marker
from src.parsers.mk.rules import has_oil_resistant, has_uv_resistant
from src.parsers.mk.rules import parse_mark_parts


class MKParser(BaseParser):
    """
    Parser for MK cable designations.
    """

    def parse(self, designation: str, comment: str | None = None) -> UCM:
        ucm = UCM()
        parts = parse_mark_parts(designation)

        ucm.cable_family = "MK"
        ucm.core_groups = extract_core_groups(designation)
        ucm.group_type = extract_group_type(designation)
        ucm.cross_section_mm2 = extract_cross_section_mm2(designation)
        ucm.cross_section_designation = extract_cross_section_designation(designation)
        ucm.rated_voltage_v = extract_rated_voltage_v(designation)
        ucm.conductor_flexibility_class = extract_conductor_flexibility_class(
            designation
        )

        ucm.insulation_material = parts.insulation_material
        ucm.sheath_material = parts.sheath_material
        ucm.overall_screen = parts.overall_screen
        ucm.individual_screen = extract_group_screen(designation)

        if parts.individual_screen_marker and ucm.individual_screen is None:
            ucm.individual_screen = ScreenType.COPPER_BRAID.value

        ucm.armor_type = parts.armor_type
        ucm.water_blocking = parts.water_blocking
        ucm.filler_material = NO_FILLER if has_no_filler_marker(designation) else parts.filler_material
        ucm.conductor_material = parts.conductor_material

        if ucm.conductor_material is None:
            ucm.conductor_material = ConductorMaterial.CU.value

        ucm.flame_retardant = has_flame_retardant(designation)
        ucm.fire_resistant = has_fire_resistant(designation)
        ucm.low_smoke = has_low_smoke(designation)
        ucm.halogen_free = has_halogen_free(designation)
        ucm.low_toxicity = has_low_toxicity(designation)
        ucm.cold_resistant = has_cold_resistant(designation)
        ucm.uv_resistant = has_uv_resistant(designation)
        ucm.oil_resistant = has_oil_resistant(designation)
        ucm.explosive_area_application = has_explosive_area_application(designation)
        ucm.intrinsically_safe = has_intrinsically_safe_execution(designation)

        color = extract_sheath_color(designation)

        if color:
            ucm.sheath_color = color

        ucm.finalize_features()

        return ucm
