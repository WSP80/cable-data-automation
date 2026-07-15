from src.generators.technical_mark import format_core_construction
from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.models.ucm import UCM


ATOMKIP_FAMILY_PREFIX = "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
ATOMKIP_DEFAULT_SCREEN_TOKEN = "\u0412\u041e\u0444\u0412"
ATOMKIP_INDIVIDUAL_SCREEN_TOKEN = "\u0418\u0444"

INDIVIDUAL_SCREEN_TOKENS = {
    ScreenType.ALUMINUM_FOIL.value: "\u0418\u0444",
    ScreenType.COPPER_BRAID.value: "\u0418\u043c",
    ScreenType.TINNED_COPPER_BRAID.value: "\u0418\u043b",
    ScreenType.COPPER_FOIL.value: "\u0418\u043c\u0444",
    ScreenType.COMBINED.value: "\u0418\u0444\u043b",
}

INSULATION_TOKENS = {
    InsulationMaterial.PVC.value: "\u0412",
    InsulationMaterial.HALOGEN_FREE.value: "\u041f",
    InsulationMaterial.XLPO.value: "\u041f\u0441",
    InsulationMaterial.EPR.value: "\u0420\u044d",
    InsulationMaterial.CERAMIFIABLE_SILICONE.value: "\u0420\u043a",
}

OVERALL_SCREEN_TOKENS = {
    ScreenType.ALUMINUM_FOIL.value: "\u041e\u0444",
    ScreenType.COPPER_BRAID.value: "\u041e\u043c",
    ScreenType.COPPER_FOIL.value: "\u041e\u043c\u0444",
    ScreenType.TINNED_COPPER_BRAID.value: "\u041e\u043b",
    ScreenType.COMBINED.value: "\u041e\u0444\u043b",
}

ARMOR_TOKENS = {
    ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value: "\u0411",
    ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value: "\u041a",
}

SHEATH_TOKENS = {
    SheathMaterial.PVC.value: "\u0412",
    SheathMaterial.HALOGEN_FREE.value: "\u041f",
}


class MarkGenerationError(ValueError):
    """
    Raised when UCM does not contain enough data for mark generation.
    """


def require_core_construction(ucm: UCM) -> None:
    if ucm.core_groups is None:
        raise MarkGenerationError("core_groups is required")

    if ucm.group_type is None:
        raise MarkGenerationError("group_type is required")

    if ucm.cross_section_mm2 is None:
        raise MarkGenerationError("cross_section_mm2 is required")


def build_fire_performance_token(ucm: UCM) -> str:
    if ucm.flame_retardant:
        return "\u043d\u0433(\u0410)"

    return ""


def build_climate_token(ucm: UCM) -> str:
    tokens = []

    if ucm.cold_resistant:
        tokens.append("\u0425\u041b")

    if ucm.uv_resistant:
        tokens.append("\u0423\u0424")

    return "-".join(tokens)


def build_fire_smoke_halogen_token(ucm: UCM) -> str:
    if ucm.fire_resistant:
        if ucm.low_smoke and ucm.low_toxicity:
            return "FRLSLTx"

        if ucm.low_smoke:
            return "FRLS"

        if ucm.halogen_free:
            return "FRHF"

        if ucm.low_toxicity:
            return "FRLTx"

        return "FR"

    if ucm.low_smoke and ucm.low_toxicity:
        return "LSLTx"

    if ucm.low_smoke:
        return "LS"

    if ucm.halogen_free:
        return "HF"

    if ucm.low_toxicity:
        return "LTx"

    return ""


def build_special_environment_tokens(ucm: UCM) -> list[str]:
    tokens = []

    if ucm.chemical_resistant:
        tokens.append("\u0410\u0421")

    if ucm.oil_resistant:
        tokens.append("\u041c")

    return tokens


def build_water_blocking_token(ucm: UCM) -> str:
    if ucm.water_blocking:
        return "\u0432"

    return ""


def build_intrinsically_safe_token(ucm: UCM) -> str:
    if ucm.intrinsically_safe:
        return "i"

    return ""


def build_conductor_class_token(ucm: UCM) -> str:
    if ucm.conductor_flexibility_class is None:
        return ""

    conductor_material_token = ""

    if ucm.conductor_material == ConductorMaterial.CU_TINNED.value:
        conductor_material_token = "\u043b"

    return f"{conductor_material_token}\u043a\u043b{ucm.conductor_flexibility_class}"


def build_voltage_token(ucm: UCM) -> str:
    if ucm.rated_voltage_v is None:
        return ""

    return f"{ucm.rated_voltage_v}\u0412"


def build_construction_token(ucm: UCM) -> str:
    token = ""
    token += INDIVIDUAL_SCREEN_TOKENS.get(ucm.individual_screen, "")
    token += INSULATION_TOKENS.get(ucm.insulation_material, "")
    token += OVERALL_SCREEN_TOKENS.get(ucm.overall_screen, "")
    token += ARMOR_TOKENS.get(ucm.armor_type, "")
    token += SHEATH_TOKENS.get(ucm.sheath_material, "")

    return token


def build_atomkip_prefix(ucm: UCM) -> str:
    base = ATOMKIP_FAMILY_PREFIX

    base += build_construction_token(ucm)

    fire_token = build_fire_performance_token(ucm)

    if fire_token:
        base += fire_token

    suffixes = []

    fire_smoke_halogen_token = build_fire_smoke_halogen_token(ucm)

    if fire_smoke_halogen_token:
        suffixes.append(fire_smoke_halogen_token)

    climate_token = build_climate_token(ucm)

    if climate_token:
        suffixes.append(climate_token)

    suffixes.extend(build_special_environment_tokens(ucm))

    water_blocking_token = build_water_blocking_token(ucm)

    if water_blocking_token:
        suffixes.append(water_blocking_token)

    intrinsically_safe_token = build_intrinsically_safe_token(ucm)

    if intrinsically_safe_token:
        suffixes.append(intrinsically_safe_token)

    if suffixes:
        return "-".join([base] + suffixes)

    return base


def build_atomkip_mark(ucm: UCM, alphabet: str = "cyrillic") -> str:
    require_core_construction(ucm)

    construction = format_atomkip_core_construction(ucm)
    conductor_class = build_conductor_class_token(ucm)
    voltage = build_voltage_token(ucm)
    size_token = f"{construction}{conductor_class}"
    parts = [build_atomkip_prefix(ucm), size_token]

    if voltage:
        parts.append(voltage)

    mark = " ".join(parts)

    if ucm.explosive_area_application:
        mark = f"\u0412\u0437-{mark}"

    color_token = build_sheath_color_token(ucm)

    if color_token:
        mark = f"{mark} ({color_token})"

    if alphabet == "latin":
        return transliterate_atomkip_mark(mark)

    if alphabet != "cyrillic":
        raise MarkGenerationError(f"Unsupported alphabet: {alphabet}")

    return mark


def build_sheath_color_token(ucm: UCM) -> str:
    default_color = "blue" if ucm.intrinsically_safe else "black"

    if not ucm.sheath_color:
        return ""

    if ucm.sheath_color == default_color:
        return ""

    return ucm.sheath_color


def format_atomkip_cross_section(value: float) -> str:
    if value.is_integer():
        return f"{value:.1f}".replace(".", ",")

    return f"{value:g}".replace(".", ",")


def format_atomkip_core_construction(ucm: UCM) -> str:
    cross_section = ucm.cross_section_designation

    if cross_section is None:
        cross_section = format_atomkip_cross_section(ucm.cross_section_mm2)

    if ucm.group_type == "core":
        return f"{ucm.core_groups}\u0445{cross_section}"

    group_size = {
        "pair": 2,
        "triple": 3,
        "quad": 4,
    }.get(ucm.group_type)

    if group_size is None:
        return format_core_construction(ucm).replace(".", ",").replace("x", "\u0445")

    return f"{ucm.core_groups}\u0445{group_size}\u0445{cross_section}"


def transliterate_atomkip_mark(mark: str) -> str:
    replacements = [
        ("\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423", "ATOMKIP-KU"),
        ("\u043d\u0433(\u0410)", "ng(A)"),
        ("\u0418\u043c\u0444", "Imf"),
        ("\u0418\u0444\u043b", "Ifl"),
        ("\u0418\u043c", "Im"),
        ("\u0418\u043b", "Il"),
        ("\u0418\u0444", "If"),
        ("\u041f\u0441", "Ps"),
        ("\u0420\u044d", "Re"),
        ("\u0420\u043a", "Rk"),
        ("\u041e\u0444\u043b", "Ofl"),
        ("\u041e\u043c\u0444", "Omf"),
        ("\u041e\u043c", "Om"),
        ("\u041e\u043b", "Ol"),
        ("\u041e\u0444", "Of"),
        ("\u0412\u0437-", "Vz-"),
        ("\u0425\u041b", "HL"),
        ("\u0423\u0424", "UF"),
        ("\u0410\u0421", "AC"),
        ("\u0412", "V"),
        ("\u041f", "P"),
        ("\u0411", "B"),
        ("\u041a", "K"),
        ("\u041c", "M"),
        ("\u0432", "v"),
        ("\u043b\u043a\u043b", "lkl"),
        ("\u043a\u043b", "kl"),
        ("\u0445", "x"),
        ("\u043c", "m"),
    ]

    result = mark

    for source, target in replacements:
        result = result.replace(source, target)

    return result
