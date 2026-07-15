import re
from dataclasses import dataclass
from typing import Optional

from src.models.enums import ArmorType, ConductorMaterial, FillerMaterial
from src.models.enums import InsulationMaterial, ScreenType, SheathMaterial
from src.parsers.text_normalization import repair_mojibake


NO_FILLER = "None"


@dataclass
class MKMarkParts:
    insulation_material: Optional[str] = None
    sheath_material: Optional[str] = None
    individual_screen_marker: bool = False
    overall_screen: Optional[str] = None
    armor_type: Optional[str] = None
    filler_material: Optional[str] = None
    conductor_material: Optional[str] = None
    water_blocking: bool = False


SCREEN_TOKENS = [
    ("\u042d\u0444\u042d\u043c\u043b", "EfEml", ScreenType.COMBINED.value),
    ("\u042d\u0444\u042d\u043c", "EfEm", ScreenType.COMBINED.value),
    ("\u042d\u043c\u0444", "Emf", ScreenType.COPPER_FOIL.value),
    ("\u042d\u043c\u043b", "Eml", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u042d\u0444", "Ef", ScreenType.ALUMINUM_FOIL.value),
    ("\u042d\u043c", "Em", ScreenType.COPPER_BRAID.value),
    ("\u042d", "E", ScreenType.COPPER_BRAID.value),
]

GROUP_SCREEN_TOKENS = [
    ("\u044d\u0444\u044d\u043c\u043b", "efeml", ScreenType.COMBINED.value),
    ("\u044d\u043c\u0444", "emf", ScreenType.COPPER_FOIL.value),
    ("\u044d\u043c\u043b", "eml", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u044d\u0444", "ef", ScreenType.ALUMINUM_FOIL.value),
    ("\u044d\u043c", "em", ScreenType.COPPER_BRAID.value),
    ("\u044d", "e", ScreenType.COPPER_BRAID.value),
]

ARMOR_TOKENS = [
    ("\u041a", "K", ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value),
    ("\u0411", "B", ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value),
]

MATERIAL_TOKENS = [
    ("\u041f\u0441", "Ps", InsulationMaterial.XLPO.value),
    ("\u0412", "V", InsulationMaterial.PVC.value),
    ("\u041f", "P", InsulationMaterial.HALOGEN_FREE.value),
    ("\u0420", "R", InsulationMaterial.EPR.value),
    ("\u0421", "S", InsulationMaterial.CERAMIFIABLE_SILICONE.value),
]


def normalize_mk_mark(text: str) -> str:
    repaired = repair_mojibake(text)

    return (
        repaired.replace("\u00d7", "x")
        .replace("\u0445", "x")
        .replace("*", "x")
        .replace(",", ".")
        .strip()
    )


def consume_token(
    text: str,
    token_rules: list[tuple[str, str, str]],
) -> tuple[Optional[str], str]:
    for cyrillic_token, latin_token, value in token_rules:
        if text.startswith(cyrillic_token):
            return value, text[len(cyrillic_token):]

        if text.upper().startswith(latin_token.upper()):
            return value, text[len(latin_token):]

    return None, text


def extract_mk_prefix(text: str) -> str:
    normalized = normalize_mk_mark(text)
    normalized = re.sub(r"^(\u041c\u041a|MK)", "", normalized, flags=re.IGNORECASE)

    match = re.search(r"\s+\(?\d+\s*x", normalized, flags=re.IGNORECASE)

    if match:
        return normalized[:match.start()].strip()

    return normalized.strip()


def parse_mark_parts(text: str) -> MKMarkParts:
    body = extract_mk_prefix(text)
    parts = MKMarkParts()

    parts.individual_screen_marker, body = consume_individual_screen_marker(body)
    parts.overall_screen, body = consume_token(body, SCREEN_TOKENS)
    parts.armor_type, body = consume_token(body, ARMOR_TOKENS)

    if body.startswith("\u0428"):
        body = body[1:]
    elif body.upper().startswith("SH"):
        body = body[2:]

    material, body = consume_token(body, MATERIAL_TOKENS)
    parts.insulation_material = material
    parts.sheath_material = material_to_sheath(material)

    if body.startswith("\u0432") or body.upper().startswith("V"):
        parts.water_blocking = True
        body = body[1:]

    if body.startswith("\u0437") or body.upper().startswith("Z"):
        parts.filler_material = material_to_filler(material)
        body = body[1:]
    else:
        parts.filler_material = NO_FILLER

    if body.startswith("\u043b") or body.upper().startswith("L"):
        parts.conductor_material = ConductorMaterial.CU_TINNED.value

    return parts


def consume_individual_screen_marker(text: str) -> tuple[bool, str]:
    if text.startswith("\u042d") and len(text) > 1 and text[1] not in "\u0444\u043c\u0424\u041c":
        return True, text[1:]

    if text.upper().startswith("E") and len(text) > 1 and text[1].upper() not in "FM":
        return True, text[1:]

    return False, text


def material_to_sheath(material: Optional[str]) -> Optional[str]:
    if material == InsulationMaterial.PVC.value:
        return SheathMaterial.PVC.value

    if material == InsulationMaterial.HALOGEN_FREE.value:
        return SheathMaterial.HALOGEN_FREE.value

    return material


def material_to_filler(material: Optional[str]) -> str:
    if material == InsulationMaterial.HALOGEN_FREE.value:
        return FillerMaterial.HALOGEN_FREE.value

    return FillerMaterial.PVC.value


def contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    normalized = normalize_mk_mark(text).upper()

    return any(token.upper() in normalized for token in tokens)


def has_flame_retardant(text: str) -> bool:
    return contains_any(text, ("\u043d\u0433(\u0410)", "ng(A)"))


def has_fire_resistant(text: str) -> bool:
    return contains_any(text, ("FR",))


def has_low_smoke(text: str) -> bool:
    return contains_any(text, ("LS",))


def has_halogen_free(text: str) -> bool:
    return contains_any(text, ("HF",))


def has_low_toxicity(text: str) -> bool:
    return contains_any(text, ("LTX",))


def has_cold_resistant(text: str) -> bool:
    return contains_any(text, ("\u0425\u041b", "HL"))


def has_uv_resistant(text: str) -> bool:
    return contains_any(text, ("\u0423\u0424", "UF"))


def has_oil_resistant(text: str) -> bool:
    normalized = normalize_mk_mark(text).upper()

    return re.search(r"(^|-|\s)(\u041c|M)(-|\s|$)", normalized) is not None


def has_no_filler_marker(text: str) -> bool:
    return contains_any(text, ("\u041e\u041f", "OP"))


def has_explosive_area_application(text: str) -> bool:
    normalized = normalize_mk_mark(text).upper()

    return re.search(r"(^|-|\s)EX(-|\s|$)", normalized) is not None


def has_intrinsically_safe_execution(text: str) -> bool:
    normalized = normalize_mk_mark(text).upper()

    return re.search(r"(^|-|\s)EX-I(-|\s|$)", normalized) is not None


def extract_sheath_color(text: str) -> Optional[str]:
    normalized = normalize_mk_mark(text)

    if re.search(r"(\u0423\u0424|UF)(\u0441\u0435\u0440|\u0441\u0435\u0440\u044b\u0439|SER|SERYY|GREY|GRAY)", normalized, re.IGNORECASE):
        return "gray"

    if re.search(r"(\u0423\u0424|UF)(\u043a|K)", normalized, re.IGNORECASE):
        return "red"

    if re.search(r"(\u0423\u0424|UF)(\u0441|S)", normalized, re.IGNORECASE):
        return "blue"

    if re.search(r"(^|-|\s)(\u0441|s)(-|\s|$)", normalized, re.IGNORECASE):
        return "blue"

    if re.search(r"(^|(?<!\u0447)-|\s)(\u043a|k)(-|\s|$)", normalized, re.IGNORECASE):
        return "red"

    if re.search(r"(^|-|\s)(\u0441\u0435\u0440\u044b\u0439|seryy|grey|gray)(-|\s|$)", normalized, re.IGNORECASE):
        return "gray"

    return None


def extract_core_groups(text: str) -> Optional[int]:
    normalized = normalize_mk_mark(text)

    match = re.search(r"\(?\s*(\d+)\s*x\s*\(?\s*\d+\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"\(?\s*(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    return None


def extract_group_type(text: str) -> Optional[str]:
    normalized = normalize_mk_mark(text)

    match = re.search(r"\d+\s*x\s*\(?\s*(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        conductors_per_group = int(match.group(1))

        if conductors_per_group == 2:
            return "pair"

        if conductors_per_group == 3:
            return "triple"

        if conductors_per_group == 4:
            return "quad"

        if conductors_per_group == 5:
            return "quint"

    match = re.search(r"\(?\s*\d+\s*x\s*[\d.]+", normalized)

    if match:
        return "core"

    return None


def extract_cross_section_designation(text: str) -> Optional[str]:
    normalized = repair_mojibake(text).replace("\u0445", "x").replace("*", "x")

    match = re.search(r"\d+\s*x\s*\(?\s*\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    match = re.search(r"\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    return None


def extract_cross_section_mm2(text: str) -> Optional[float]:
    designation = extract_cross_section_designation(text)

    if designation is None:
        return None

    return float(designation.replace(",", "."))


def extract_conductor_flexibility_class(text: str) -> int:
    normalized = normalize_mk_mark(text)

    if re.search(r"[\d.]\s*(\u043e\u043a|ok)(?=\)|\s|-|$)", normalized, re.IGNORECASE):
        return 1

    if re.search(r"[\d.]\s*(\u043c\u043a|mk)(?=\)|\s|-|$)", normalized, re.IGNORECASE):
        return 2

    return 5


def extract_group_screen(text: str) -> Optional[str]:
    normalized = normalize_mk_mark(text)

    match = re.search(
        r"\d+\s*x\s*\(?\s*\d+\s*x\s*[\d.]+(?:\u043e\u043a|ok|\u043c\u043a|mk)?\)?\s*([^\s\)-]+)",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    token = match.group(1)

    for cyrillic_token, latin_token, value in GROUP_SCREEN_TOKENS:
        if token.startswith(cyrillic_token) or token.upper().startswith(latin_token.upper()):
            return value

    return None


def extract_rated_voltage_v(text: str) -> Optional[int]:
    normalized = normalize_mk_mark(text).upper()

    match = re.search(r"(\d{3})\s*(?:\u0412|V)?\s*$", normalized)

    if match:
        return int(match.group(1))

    return None
