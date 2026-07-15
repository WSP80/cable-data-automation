from src.models.enums import ConductorMaterial, SheathMaterial
from src.models.ucm import UCM
from src.parsers.base_parser import BaseParser
from src.parsers.toflex.rules import extract_rated_voltage_v
from src.parsers.toflex.rules import extract_toflex_conductor_flexibility_class
from src.parsers.toflex.rules import extract_toflex_core_groups
from src.parsers.toflex.rules import extract_toflex_cross_section_designation
from src.parsers.toflex.rules import extract_toflex_cross_section_mm2
from src.parsers.toflex.rules import extract_toflex_group_type
from src.parsers.toflex.rules import has_blue_sheath, has_cold_resistant
from src.parsers.toflex.rules import has_fire_resistant, has_flame_retardant
from src.parsers.toflex.rules import has_halogen_free, has_intrinsically_safe_execution
from src.parsers.toflex.rules import has_low_smoke, has_low_toxicity
from src.parsers.toflex.rules import has_oil_resistance, has_tinned_conductor_suffix
from src.parsers.toflex.rules import has_uv_resistant, has_water_blocking
from src.parsers.toflex.rules import parse_mark_parts


class ToflexParser(BaseParser):
    """
    Parser for TOFLEX-KU cable designations.
    """

    def parse(self, designation: str, comment: str | None = None) -> UCM:
        ucm = UCM()
        parts = parse_mark_parts(designation)

        ucm.cable_family = "TOFLEX-KU"
        ucm.core_groups = extract_toflex_core_groups(designation)
        ucm.group_type = extract_toflex_group_type(designation)
        ucm.cross_section_mm2 = extract_toflex_cross_section_mm2(designation)
        ucm.cross_section_designation = extract_toflex_cross_section_designation(
            designation
        )
        ucm.rated_voltage_v = extract_rated_voltage_v(designation)
        ucm.conductor_flexibility_class = extract_toflex_conductor_flexibility_class(
            designation
        )

        ucm.individual_screen = parts.individual_screen
        ucm.insulation_material = parts.insulation_material
        ucm.overall_screen = parts.overall_screen
        ucm.armor_type = parts.armor_type
        ucm.sheath_material = parts.sheath_material

        if has_tinned_conductor_suffix(designation):
            ucm.conductor_material = ConductorMaterial.CU_TINNED.value

        ucm.flame_retardant = has_flame_retardant(designation)
        ucm.fire_resistant = has_fire_resistant(designation)
        ucm.low_smoke = has_low_smoke(designation)
        ucm.low_toxicity = has_low_toxicity(designation)
        ucm.halogen_free = has_halogen_free(designation)

        if ucm.sheath_material == SheathMaterial.HALOGEN_FREE.value:
            ucm.halogen_free = True

        ucm.cold_resistant = has_cold_resistant(designation)
        ucm.intrinsically_safe = has_intrinsically_safe_execution(designation)
        ucm.oil_resistant = has_oil_resistance(designation)
        ucm.uv_resistant = has_uv_resistant(designation)
        ucm.water_blocking = has_water_blocking(designation)

        if has_blue_sheath(designation):
            ucm.sheath_color = "blue"

        ucm.finalize_features()

        return ucm
