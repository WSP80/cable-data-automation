from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.models.ucm import UCM


SCREEN_TOKENS = {
    ScreenType.COPPER_BRAID.value: "\u042d",
    ScreenType.COPPER_FOIL.value: "\u042d\u043c",
    ScreenType.ALUMINUM_FOIL.value: "\u042d\u0430",
    ScreenType.TINNED_COPPER_BRAID.value: "\u042d\u043b",
    ScreenType.COMBINED.value: "\u042d\u0430\u042d\u043b",
}

INSULATION_TOKENS = {
    InsulationMaterial.PVC.value: "\u0412",
    InsulationMaterial.HALOGEN_FREE.value: "\u041f",
    InsulationMaterial.XLPO.value: "\u041f\u0441",
}

ARMOR_TOKENS = {
    ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value: "\u0411",
    ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value: "\u041a",
}

SHEATH_TOKENS = {
    SheathMaterial.PVC.value: "\u0412",
    SheathMaterial.HALOGEN_FREE.value: "\u041f",
}


class ToflexGenerationError(ValueError):
    """
    Raised when UCM does not contain enough data for TOFLEX mark generation.
    """


def require_core_construction(ucm: UCM) -> None:
    if ucm.core_groups is None:
        raise ToflexGenerationError("core_groups is required")

    if ucm.group_type is None:
        raise ToflexGenerationError("group_type is required")

    if ucm.cross_section_mm2 is None:
        raise ToflexGenerationError("cross_section_mm2 is required")


def format_toflex_cross_section(ucm: UCM) -> str:
    if ucm.cross_section_designation:
        cross_section = ucm.cross_section_designation.replace(".", ",")
        return f"{cross_section}{format_conductor_class_suffix(ucm)}"

    value = ucm.cross_section_mm2

    if value.is_integer():
        cross_section = f"{value:g}".replace(".", ",")
        return f"{cross_section}{format_conductor_class_suffix(ucm)}"

    cross_section = f"{value:g}".replace(".", ",")
    return f"{cross_section}{format_conductor_class_suffix(ucm)}"


def format_conductor_class_suffix(ucm: UCM) -> str:
    if ucm.conductor_flexibility_class == 1:
        return "\u043e\u043a"

    if ucm.conductor_flexibility_class == 2:
        return "\u043c\u043a"

    return ""


def format_toflex_core_construction(ucm: UCM) -> str:
    cross_section = format_toflex_cross_section(ucm)

    if ucm.group_type == "core":
        return f"{ucm.core_groups}\u0445{cross_section}"

    group_size = {
        "pair": 2,
        "triple": 3,
        "quad": 4,
    }.get(ucm.group_type)

    if group_size is None:
        return f"{ucm.core_groups}\u0445{cross_section}"

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


def build_toflex_prefix(ucm: UCM) -> str:
    prefix = "\u0422\u041e\u0424\u041b\u0415\u041a\u0421 \u041a\u0423"
    prefix += SCREEN_TOKENS.get(ucm.individual_screen, "")
    prefix += INSULATION_TOKENS.get(ucm.insulation_material, "")
    prefix += SCREEN_TOKENS.get(ucm.overall_screen, "")
    prefix += ARMOR_TOKENS.get(ucm.armor_type, "")
    prefix += SHEATH_TOKENS.get(ucm.sheath_material, "\u0412")

    if ucm.flame_retardant:
        prefix += "\u043d\u0433(\u0410)"

    suffixes = []
    fire_safety_suffix = build_fire_safety_suffix(ucm)

    if fire_safety_suffix:
        suffixes.append(fire_safety_suffix)

    if ucm.cold_resistant:
        suffixes.append("\u0425\u041b")

    if ucm.intrinsically_safe:
        suffixes.append("i")

    if suffixes:
        return "-".join([prefix] + suffixes)

    return prefix


def build_additional_tokens(ucm: UCM) -> list[str]:
    tokens = []

    if ucm.conductor_material == ConductorMaterial.CU_TINNED.value:
        tokens.append("\u043b")

    if ucm.oil_resistant:
        tokens.append("\u041c")

    if ucm.uv_resistant:
        tokens.append("\u0423\u0424")

    if ucm.water_blocking:
        tokens.append("\u0432")

    if ucm.sheath_color == "blue" and not ucm.intrinsically_safe:
        tokens.append("\u0441")

    return tokens


def build_toflex_mark(ucm: UCM, alphabet: str = "cyrillic") -> str:
    require_core_construction(ucm)
    construction = format_toflex_core_construction(ucm)
    additional_tokens = build_additional_tokens(ucm)

    if additional_tokens and additional_tokens[0] == "\u043b":
        construction = f"{construction}\u043b"
        additional_tokens = additional_tokens[1:]

    parts = [build_toflex_prefix(ucm), construction]

    if additional_tokens:
        parts.extend(additional_tokens)

    mark = " ".join(parts)

    if ucm.rated_voltage_v is not None:
        mark = f"{mark} - {ucm.rated_voltage_v}"

    if alphabet == "latin":
        return transliterate_toflex_mark(mark)

    if alphabet != "cyrillic":
        raise ToflexGenerationError(f"Unsupported alphabet: {alphabet}")

    return mark


def transliterate_toflex_mark(mark: str) -> str:
    replacements = [
        ("\u0422\u041e\u0424\u041b\u0415\u041a\u0421", "TOFLEX"),
        ("\u041a\u0423", "KU"),
        ("\u043d\u0433(\u0410)", "ng(A)"),
        ("\u043c\u043a", "mk"),
        ("\u043e\u043a", "ok"),
        ("\u042d\u0430\u042d\u043b", "EaEl"),
        ("\u042d\u043c", "Em"),
        ("\u042d\u0430", "Ea"),
        ("\u042d\u043b", "El"),
        ("\u042d", "E"),
        ("\u041f\u0441", "Ps"),
        ("\u0425\u041b", "HL"),
        ("\u0423\u0424", "UF"),
        ("\u0412", "V"),
        ("\u041f", "P"),
        ("\u0411", "B"),
        ("\u041a", "K"),
        ("\u041c", "M"),
        ("\u0445", "x"),
        ("\u043b", "l"),
        ("\u0432", "v"),
        ("\u0441", "s"),
    ]

    result = mark

    for source, target in replacements:
        result = result.replace(source, target)

    return result
