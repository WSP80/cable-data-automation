from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.models.ucm import UCM


OVERALL_SCREEN_TOKENS = {
    ScreenType.COPPER_BRAID.value: "\u042d",
    ScreenType.TINNED_COPPER_BRAID.value: "\u042d\u043b",
    ScreenType.ALUMINUM_FOIL.value: "\u042d\u0444",
    ScreenType.COPPER_FOIL.value: "\u042d\u043c\u0444",
    ScreenType.COMBINED.value: "\u042d\u0444\u042d",
}

INDIVIDUAL_SCREEN_TOKENS = {
    ScreenType.COPPER_BRAID.value: "\u044d",
    ScreenType.TINNED_COPPER_BRAID.value: "\u044d\u043b",
    ScreenType.ALUMINUM_FOIL.value: "\u044d\u0444",
    ScreenType.COPPER_FOIL.value: "\u044d\u043c\u0444",
    ScreenType.COMBINED.value: "\u044d\u0444\u044d\u043b",
}

ARMOR_TOKENS = {
    ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value: "\u041a",
    ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value: "\u0411",
}

SHEATH_TOKENS = {
    SheathMaterial.PVC.value: "\u0412",
    SheathMaterial.HALOGEN_FREE.value: "\u041f",
}

INSULATION_TOKENS = {
    InsulationMaterial.XLPO.value: "\u041f\u0441",
    InsulationMaterial.EPR.value: "\u0420",
}


class ConflexGenerationError(ValueError):
    """
    Raised when UCM does not contain enough data for CONFLEX mark generation.
    """


def require_core_construction(ucm: UCM) -> None:
    if ucm.core_groups is None:
        raise ConflexGenerationError("core_groups is required")

    if ucm.group_type is None:
        raise ConflexGenerationError("group_type is required")

    if ucm.cross_section_mm2 is None:
        raise ConflexGenerationError("cross_section_mm2 is required")


def format_conflex_cross_section(ucm: UCM) -> str:
    if ucm.cross_section_designation:
        cross_section = ucm.cross_section_designation.replace(".", ",")
        return f"{cross_section}{format_conductor_class_suffix(ucm)}"

    value = ucm.cross_section_mm2

    if value.is_integer():
        cross_section = f"{value:.1f}".replace(".", ",")
        return f"{cross_section}{format_conductor_class_suffix(ucm)}"

    cross_section = f"{value:g}".replace(".", ",")
    return f"{cross_section}{format_conductor_class_suffix(ucm)}"


def format_conductor_class_suffix(ucm: UCM) -> str:
    if ucm.conductor_flexibility_class == 1:
        return "\u043e\u043a"

    if ucm.conductor_flexibility_class == 2:
        return "\u043c\u043a"

    return ""


def format_conflex_core_construction(ucm: UCM) -> str:
    cross_section = format_conflex_cross_section(ucm)

    if ucm.group_type == "core":
        return f"{ucm.core_groups}\u0445{cross_section}"

    group_size = {
        "pair": 2,
        "triple": 3,
        "quad": 4,
    }.get(ucm.group_type)

    if group_size is None:
        return f"{ucm.core_groups}\u0445{cross_section}"

    individual_screen_token = INDIVIDUAL_SCREEN_TOKENS.get(ucm.individual_screen, "")

    if individual_screen_token:
        return (
            f"{ucm.core_groups}\u0445"
            f"({group_size}\u0445{cross_section})"
            f"{individual_screen_token}"
        )

    return f"{ucm.core_groups}\u0445{group_size}\u0445{cross_section}"


def build_fire_safety_suffix(ucm: UCM) -> str:
    if ucm.fire_resistant:
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


def build_climate_suffixes(ucm: UCM) -> list[str]:
    suffixes = []

    if ucm.cold_resistant:
        suffixes.append("\u0425\u041b")

    if ucm.oil_resistant:
        suffixes.append("\u041c")

    if ucm.uv_resistant:
        suffixes.append("\u0423\u0424")

    if ucm.intrinsically_safe:
        suffixes.append("Ex-i")
    elif ucm.explosive_area_application:
        suffixes.append("Ex")

    return suffixes


def build_conflex_prefix(ucm: UCM) -> str:
    prefix = "\u041c\u041a"
    prefix += OVERALL_SCREEN_TOKENS.get(ucm.overall_screen, "")
    prefix += ARMOR_TOKENS.get(ucm.armor_type, "")
    prefix += "\u0428"
    prefix += SHEATH_TOKENS.get(ucm.sheath_material, "\u0412")

    insulation_token = INSULATION_TOKENS.get(ucm.insulation_material, "")

    if insulation_token:
        prefix += insulation_token

    if ucm.conductor_material == ConductorMaterial.CU_TINNED.value:
        prefix += "\u043b"

    if ucm.water_blocking:
        prefix += "\u0432"

    if ucm.flame_retardant:
        prefix += "\u043d\u0433(\u0410)"

    fire_safety_suffix = build_fire_safety_suffix(ucm)

    if fire_safety_suffix:
        return "-".join([prefix, fire_safety_suffix])

    return prefix


def build_conflex_mark(ucm: UCM, alphabet: str = "cyrillic") -> str:
    require_core_construction(ucm)
    construction = format_conflex_core_construction(ucm)
    mark = f"CONFLEX {build_conflex_prefix(ucm)} {construction}"
    tail_suffixes = build_climate_suffixes(ucm)

    if tail_suffixes:
        mark = f"{mark} {'-'.join(tail_suffixes)}"

    if ucm.rated_voltage_v is not None:
        mark = f"{mark} {ucm.rated_voltage_v}\u0412"

    if alphabet == "latin":
        return transliterate_conflex_mark(mark)

    if alphabet != "cyrillic":
        raise ConflexGenerationError(f"Unsupported alphabet: {alphabet}")

    return mark


def transliterate_conflex_mark(mark: str) -> str:
    replacements = [
        ("\u043d\u0433(\u0410)", "ng(A)"),
        ("\u043c\u043a", "mk"),
        ("\u043e\u043a", "ok"),
        ("\u042d\u043c\u0444\u042d\u043b", "EmfEl"),
        ("\u042d\u0444\u042d\u043b", "EfEl"),
        ("\u042d\u043c\u0444\u042d", "EmfE"),
        ("\u042d\u0444\u042d", "EfE"),
        ("\u042d\u043c\u0444", "Emf"),
        ("\u042d\u0444", "Ef"),
        ("\u042d\u043b", "El"),
        ("\u042d", "E"),
        ("\u044d\u0444\u044d\u043b", "efel"),
        ("\u044d\u043c\u0444", "emf"),
        ("\u044d\u043b", "el"),
        ("\u044d\u0444", "ef"),
        ("\u044d", "e"),
        ("\u041f\u0441", "Ps"),
        ("\u0425\u041b", "HL"),
        ("\u0423\u0424", "UF"),
        ("\u0412", "V"),
        ("\u041f", "P"),
        ("\u0420", "R"),
        ("\u0411", "B"),
        ("\u041a", "K"),
        ("\u041c", "M"),
        ("\u0428", "Sh"),
        ("\u0445", "x"),
        ("\u043b", "l"),
        ("\u0432", "v"),
    ]

    result = mark

    for source, target in replacements:
        result = result.replace(source, target)

    return result
