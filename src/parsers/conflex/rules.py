import re
from dataclasses import dataclass
from typing import Optional

from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.parsers.text_normalization import normalize_designation
from src.parsers.text_normalization import repair_mojibake


@dataclass
class ConflexMarkParts:
    overall_screen: Optional[str] = None
    armor_type: Optional[str] = None
    sheath_material: Optional[str] = None
    insulation_material: Optional[str] = None
    conductor_material: Optional[str] = None
    water_blocking: bool = False


INDIVIDUAL_SCREEN_TOKENS = [
    ("\u044d\u0444\u044d\u043b", ScreenType.COMBINED.value),
    ("efel", ScreenType.COMBINED.value),
    ("\u044d\u043c\u0444", ScreenType.COPPER_FOIL.value),
    ("emf", ScreenType.COPPER_FOIL.value),
    ("\u044d\u043b", ScreenType.TINNED_COPPER_BRAID.value),
    ("el", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u044d\u0444", ScreenType.ALUMINUM_FOIL.value),
    ("ef", ScreenType.ALUMINUM_FOIL.value),
    ("\u044d", ScreenType.COPPER_BRAID.value),
    ("e", ScreenType.COPPER_BRAID.value),
]

OVERALL_SCREEN_TOKENS = [
    ("\u042d\u043c\u0444\u042d\u043b", ScreenType.COMBINED.value),
    ("EmfEl", ScreenType.COMBINED.value),
    ("\u042d\u0444\u042d\u043b", ScreenType.COMBINED.value),
    ("EfEl", ScreenType.COMBINED.value),
    ("\u042d\u043c\u0444\u042d", ScreenType.COMBINED.value),
    ("EmfE", ScreenType.COMBINED.value),
    ("\u042d\u0444\u042d", ScreenType.COMBINED.value),
    ("EfE", ScreenType.COMBINED.value),
    ("\u042d\u043c\u0444", ScreenType.COPPER_FOIL.value),
    ("Emf", ScreenType.COPPER_FOIL.value),
    ("\u042d\u0444", ScreenType.ALUMINUM_FOIL.value),
    ("Ef", ScreenType.ALUMINUM_FOIL.value),
    ("\u042d\u043b", ScreenType.TINNED_COPPER_BRAID.value),
    ("El", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u042d", ScreenType.COPPER_BRAID.value),
    ("E", ScreenType.COPPER_BRAID.value),
]

ARMOR_TOKENS = [
    ("\u0411", ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value),
    ("B", ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value),
    ("\u041a", ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value),
    ("K", ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value),
]

MATERIAL_TOKENS = [
    ("\u041f\u0441", InsulationMaterial.XLPO.value),
    ("Ps", InsulationMaterial.XLPO.value),
    ("\u0420", InsulationMaterial.EPR.value),
    ("R", InsulationMaterial.EPR.value),
    ("\u0412", InsulationMaterial.PVC.value),
    ("V", InsulationMaterial.PVC.value),
    ("\u041f", InsulationMaterial.HALOGEN_FREE.value),
    ("P", InsulationMaterial.HALOGEN_FREE.value),
]


def normalize_conflex_mark(text: str) -> str:
    return normalize_designation(text).replace("V", "\u0412")


def extract_conflex_prefix(text: str) -> str:
    normalized = normalize_conflex_mark(text)
    normalized = re.sub(r"^CONFLEX\s+", "", normalized, flags=re.IGNORECASE)

    match = re.search(r"\s+\d+\s*x", normalized, flags=re.IGNORECASE)

    if match:
        return normalized[:match.start()].strip()

    return normalized.strip()


def consume_token(
    text: str,
    token_rules: list[tuple[str, str]],
) -> tuple[Optional[str], str]:
    for token, value in token_rules:
        if text.startswith(token):
            return value, text[len(token):]

        if text.upper().startswith(token.upper()):
            return value, text[len(token):]

    return None, text


def parse_mark_parts(text: str) -> ConflexMarkParts:
    prefix = extract_conflex_prefix(text)
    parts = ConflexMarkParts()

    if prefix.startswith("\u041c\u041a"):
        body = prefix[len("\u041c\u041a"):]
    elif prefix.upper().startswith("MK"):
        body = prefix[len("MK"):]
    else:
        return parts

    parts.overall_screen, body = consume_token(body, OVERALL_SCREEN_TOKENS)
    parts.armor_type, body = consume_token(body, ARMOR_TOKENS)

    if body.startswith("\u0428"):
        body = body[1:]
    elif body.upper().startswith("SH"):
        body = body[2:]

    sheath_material, body = consume_token(body, MATERIAL_TOKENS)
    parts.sheath_material = sheath_material

    insulation_material, body = consume_token(body, MATERIAL_TOKENS)
    parts.insulation_material = insulation_material or sheath_material

    if body.startswith("\u043b") or body.upper().startswith("L"):
        parts.conductor_material = ConductorMaterial.CU_TINNED.value
        body = body[1:]

    if body.startswith("\u0432") or body.upper().startswith("V"):
        parts.water_blocking = True

    return parts


def has_flame_retardant(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return "\u041d\u0413(\u0410)" in normalized or "NG(A)" in normalized


def has_fire_resistant(text: str) -> bool:
    return "FR" in normalize_conflex_mark(text).upper()


def has_low_smoke(text: str) -> bool:
    return "LS" in normalize_conflex_mark(text).upper()


def has_low_toxicity(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return "LTX" in normalized or "LSTX" in normalized


def has_halogen_free(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return "HF" in normalized


def has_cold_resistant(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return "\u0425\u041b" in normalized or "HL" in normalized


def has_oil_resistance(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return re.search(r"(^|-|\s)(\u041c|M)(-|\s|$)", normalized) is not None


def has_uv_resistant(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return "\u0423\u0424" in normalized or "UF" in normalized


def has_explosive_area_application(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return re.search(r"(^|-|\s)EX(-|\s|$)", normalized) is not None


def has_intrinsically_safe_execution(text: str) -> bool:
    normalized = normalize_conflex_mark(text).upper()

    return re.search(r"(^|-|\s)EX-I(-|\s|$)", normalized) is not None


def extract_conflex_cross_section_designation(text: str) -> Optional[str]:
    normalized = repair_mojibake(text).replace("\u0445", "x").replace("*", "x")

    match = re.search(r"\d+\s*x\s*\(\s*\d+\s*x\s*([\d,.]+)\s*\)", normalized)

    if match:
        return match.group(1)

    match = re.search(r"\d+\s*x\s*\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    match = re.search(r"\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    return None


def extract_conflex_core_groups(text: str) -> Optional[int]:
    normalized = normalize_conflex_mark(text)

    match = re.search(r"(\d+)\s*x\s*\(\s*\d+\s*x\s*[\d.]+\s*\)", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s*x\s*\d+\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    return None


def extract_conflex_group_type(text: str) -> Optional[str]:
    normalized = normalize_conflex_mark(text)

    match = re.search(r"\d+\s*x\s*\(?\s*(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        conductors_per_group = int(match.group(1))

        if conductors_per_group == 2:
            return "pair"

        if conductors_per_group == 3:
            return "triple"

        if conductors_per_group == 4:
            return "quad"

    match = re.search(r"\d+\s*x\s*[\d.]+", normalized)

    if match:
        return "core"

    return None


def extract_conflex_cross_section_mm2(text: str) -> Optional[float]:
    designation = extract_conflex_cross_section_designation(text)

    if designation is None:
        return None

    return float(designation.replace(",", "."))


def extract_conflex_conductor_flexibility_class(text: str) -> int:
    normalized = normalize_conflex_mark(text)

    if re.search(r"[\d.]\s*(\u043e\u043a|ok)(?=\)|\s|-|$)", normalized, re.IGNORECASE):
        return 1

    if re.search(r"[\d.]\s*(\u043c\u043a|mk)(?=\)|\s|-|$)", normalized, re.IGNORECASE):
        return 2

    return 5


def extract_individual_screen(text: str) -> Optional[str]:
    normalized = normalize_conflex_mark(text)

    match = re.search(
        r"\d+\s*x\s*\(\s*\d+\s*x\s*[\d.]+(?:\u043e\u043a|ok|\u043c\u043a|mk)?\s*\)\s*([^\s-]+)",
        normalized,
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    token = match.group(1)

    for screen_token, value in INDIVIDUAL_SCREEN_TOKENS:
        if token.startswith(screen_token) or token.upper().startswith(screen_token.upper()):
            return value

    return None
