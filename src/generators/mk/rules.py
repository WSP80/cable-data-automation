from src.models.enums import ArmorType, ConductorMaterial, FillerMaterial
from src.models.enums import InsulationMaterial, ScreenType, SheathMaterial
from src.models.ucm import UCM


NO_FILLER = "None"


SCREEN_TOKENS = {
    ScreenType.COPPER_BRAID.value: "\u042d\u043c",
    ScreenType.TINNED_COPPER_BRAID.value: "\u042d\u043c\u043b",
    ScreenType.ALUMINUM_FOIL.value: "\u042d\u0444",
    ScreenType.COPPER_FOIL.value: "\u042d\u043c\u0444",
    ScreenType.COMBINED.value: "\u042d\u0444\u042d\u043c\u043b",
}

GROUP_SCREEN_TOKENS = {
    ScreenType.COPPER_BRAID.value: "\u044d\u043c",
    ScreenType.TINNED_COPPER_BRAID.value: "\u044d\u043c\u043b",
    ScreenType.ALUMINUM_FOIL.value: "\u044d\u0444",
    ScreenType.COPPER_FOIL.value: "\u044d\u043c\u0444",
    ScreenType.COMBINED.value: "\u044d\u0444\u044d\u043c\u043b",
}

ARMOR_TOKENS = {
    ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value: "\u041a",
    ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value: "\u0411",
}

MATERIAL_TOKENS = {
    InsulationMaterial.PVC.value: "\u0412",
    InsulationMaterial.HALOGEN_FREE.value: "\u041f",
    InsulationMaterial.XLPO.value: "\u041f\u0441",
    InsulationMaterial.EPR.value: "\u0420",
    InsulationMaterial.CERAMIFIABLE_SILICONE.value: "\u0421",
    SheathMaterial.PVC.value: "\u0412",
    SheathMaterial.HALOGEN_FREE.value: "\u041f",
}


class MKGenerationError(ValueError):
    """
    Raised when UCM does not contain enough data for MK mark generation.
    """


def require_core_construction(ucm: UCM) -> None:
    if ucm.core_groups is None:
        raise MKGenerationError("core_groups is required")

    if ucm.group_type is None:
        raise MKGenerationError("group_type is required")

    if ucm.cross_section_mm2 is None:
        raise MKGenerationError("cross_section_mm2 is required")


def format_cross_section(ucm: UCM) -> str:
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


def format_core_construction(ucm: UCM) -> str:
    cross_section = format_cross_section(ucm)

    if ucm.group_type == "core":
        construction = f"{ucm.core_groups}\u0445{cross_section}"
    else:
        group_size = {
            "pair": 2,
            "triple": 3,
            "quad": 4,
            "quint": 5,
        }.get(ucm.group_type)

        if group_size is None:
            construction = f"{ucm.core_groups}\u0445{cross_section}"
        elif ucm.individual_screen and ucm.individual_screen != ScreenType.NONE.value:
            screen_token = GROUP_SCREEN_TOKENS.get(ucm.individual_screen, "")
            construction = (
                f"{ucm.core_groups}\u0445"
                f"({group_size}\u0445{cross_section})"
                f"{screen_token}"
            )
        else:
            construction = f"{ucm.core_groups}\u0445{group_size}\u0445{cross_section}"

    if ucm.overall_screen and ucm.overall_screen != ScreenType.NONE.value:
        if (
            ucm.individual_screen
            and ucm.individual_screen != ScreenType.NONE.value
        ):
            return f"({construction}"

        return f"({construction})"

    return construction


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


def build_mk_prefix(ucm: UCM) -> str:
    prefix = "\u041c\u041a"

    if (
        ucm.individual_screen
        and ucm.individual_screen != ScreenType.NONE.value
        and (not ucm.overall_screen or ucm.overall_screen == ScreenType.NONE.value)
    ):
        prefix += "\u042d"

    prefix += SCREEN_TOKENS.get(ucm.overall_screen, "")
    prefix += ARMOR_TOKENS.get(ucm.armor_type, "")
    prefix += "\u0428"

    material = ucm.insulation_material or ucm.sheath_material
    prefix += MATERIAL_TOKENS.get(material, "\u0412")

    if ucm.water_blocking:
        prefix += "\u0432"

    if ucm.filler_material and ucm.filler_material != NO_FILLER:
        prefix += "\u0437"

    if ucm.conductor_material == ConductorMaterial.CU_TINNED.value:
        prefix += "\u043b"

    if ucm.flame_retardant:
        prefix += "\u043d\u0433(\u0410)"

    fire_suffixes = []
    fire_safety_suffix = build_fire_safety_suffix(ucm)

    if fire_safety_suffix:
        fire_suffixes.append(fire_safety_suffix)

    if fire_suffixes:
        prefix = "-".join([prefix] + fire_suffixes)

    if ucm.intrinsically_safe:
        return f"{prefix} Ex-i"

    if ucm.explosive_area_application:
        return f"{prefix} Ex"

    return prefix


def build_special_tokens(ucm: UCM) -> list[str]:
    tokens = []

    if ucm.cold_resistant:
        tokens.append("\u0425\u041b")

    if ucm.uv_resistant:
        tokens.append("\u0423\u0424")

    if ucm.oil_resistant:
        tokens.append("\u041c")

    if ucm.sheath_color == "blue" and not ucm.intrinsically_safe:
        tokens.append("\u0441")
    elif ucm.sheath_color == "red":
        tokens.append("\u043a")
    elif ucm.sheath_color == "gray":
        tokens.append("\u0441\u0435\u0440\u044b\u0439")

    return tokens


def build_mk_mark(ucm: UCM, alphabet: str = "cyrillic") -> str:
    require_core_construction(ucm)
    parts = [build_mk_prefix(ucm), format_core_construction(ucm)]
    special_tokens = build_special_tokens(ucm)

    if special_tokens:
        parts.append("-".join(special_tokens))

    if ucm.rated_voltage_v is not None:
        parts.append(str(ucm.rated_voltage_v))

    mark = " ".join(parts)

    if alphabet == "latin":
        return transliterate_mk_mark(mark)

    if alphabet != "cyrillic":
        raise MKGenerationError(f"Unsupported alphabet: {alphabet}")

    return mark


def transliterate_mk_mark(mark: str) -> str:
    replacements = [
        ("\u043d\u0433(\u0410)", "ng(A)"),
        ("\u043c\u043a", "mk"),
        ("\u043e\u043a", "ok"),
        ("\u042d\u0444\u042d\u043c\u043b", "EfEml"),
        ("\u042d\u043c\u0444", "Emf"),
        ("\u042d\u043c\u043b", "Eml"),
        ("\u042d\u0444", "Ef"),
        ("\u042d\u043c", "Em"),
        ("\u042d", "E"),
        ("\u044d\u0444\u044d\u043c\u043b", "efeml"),
        ("\u044d\u043c\u0444", "emf"),
        ("\u044d\u043c\u043b", "eml"),
        ("\u044d\u0444", "ef"),
        ("\u044d\u043c", "em"),
        ("\u044d", "e"),
        ("\u041f\u0441", "Ps"),
        ("\u041e\u041f", "OP"),
        ("\u0425\u041b", "HL"),
        ("\u0423\u0424", "UF"),
        ("\u0412", "V"),
        ("\u041f", "P"),
        ("\u0420", "R"),
        ("\u0421", "S"),
        ("\u0411", "B"),
        ("\u041a", "K"),
        ("\u041c", "M"),
        ("\u0428", "Sh"),
        ("\u0445", "x"),
        ("\u0437", "z"),
        ("\u043b", "l"),
        ("\u0432", "v"),
        ("\u043a", "k"),
        ("\u0441\u0435\u0440\u044b\u0439", "seryy"),
        ("\u0441", "s"),
    ]

    result = mark

    for source, target in replacements:
        result = result.replace(source, target)

    return result
