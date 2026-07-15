import re
from dataclasses import dataclass
from typing import Optional

from src.models.enums import ArmorType, ConductorMaterial, InsulationMaterial
from src.models.enums import ScreenType, SheathMaterial
from src.parsers.text_normalization import repair_mojibake


@dataclass
class ToflexMarkParts:
    individual_screen: Optional[str] = None
    insulation_material: Optional[str] = None
    overall_screen: Optional[str] = None
    armor_type: Optional[str] = None
    sheath_material: Optional[str] = None


SCREEN_TOKENS = [
    ("\u042d\u0430\u042d\u043b", "EAEL", ScreenType.COMBINED.value),
    ("\u042d\u043c", "EM", ScreenType.COPPER_FOIL.value),
    ("\u042d\u0430", "EA", ScreenType.ALUMINUM_FOIL.value),
    ("\u042d\u043b", "EL", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u042d", "E", ScreenType.COPPER_BRAID.value),
]

INSULATION_TOKENS = [
    ("\u041f\u0441", "PS", InsulationMaterial.XLPO.value),
    ("\u0412", "V", InsulationMaterial.PVC.value),
    ("\u041f", "P", InsulationMaterial.HALOGEN_FREE.value),
]

ARMOR_TOKENS = [
    ("\u0411", "B", ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value),
    ("\u041a", "K", ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value),
]

SHEATH_TOKENS = [
    ("\u0412", "V", SheathMaterial.PVC.value),
    ("\u041f", "P", SheathMaterial.HALOGEN_FREE.value),
]


def normalize_toflex_mark(text: str) -> str:
    repaired = repair_mojibake(text)

    return (
        repaired.replace("\u00d7", "x")
        .replace("\u0445", "x")
        .replace("*", "x")
        .replace(",", ".")
        .strip()
    )


def extract_toflex_prefix(text: str) -> str:
    normalized = normalize_toflex_mark(text)
    normalized = re.sub(
        r"^(\u0422\u041e\u0424\u041b\u0415\u041a\u0421|TOFLEX)\s+(\u041a\u0423|KU)",
        "",
        normalized,
        flags=re.IGNORECASE,
    )

    match = re.search(r"\s+\d+\s*x", normalized, flags=re.IGNORECASE)

    if match:
        return normalized[:match.start()].strip()

    return normalized.strip()


def consume_token(
    text: str,
    token_rules: list[tuple[str, str, str]],
) -> tuple[Optional[str], str]:
    for cyrillic_token, latin_token, value in token_rules:
        if text.startswith(cyrillic_token):
            return value, text[len(cyrillic_token):]

        if text.upper().startswith(latin_token):
            return value, text[len(latin_token):]

    return None, text


def parse_mark_parts(text: str) -> ToflexMarkParts:
    body = extract_toflex_prefix(text)
    parts = ToflexMarkParts()

    parts.individual_screen, body = consume_token(body, SCREEN_TOKENS)
    parts.insulation_material, body = consume_token(body, INSULATION_TOKENS)
    parts.overall_screen, body = consume_token(body, SCREEN_TOKENS)
    parts.armor_type, body = consume_token(body, ARMOR_TOKENS)
    parts.sheath_material, body = consume_token(body, SHEATH_TOKENS)

    return parts


def contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    normalized = normalize_toflex_mark(text).upper()

    return any(token.upper() in normalized for token in tokens)


def has_flame_retardant(text: str) -> bool:
    return contains_any(text, ("\u043d\u0433(\u0410)", "NG(A)"))


def has_fire_resistant(text: str) -> bool:
    return contains_any(text, ("FR",))


def has_low_smoke(text: str) -> bool:
    return contains_any(text, ("LS",))


def has_low_toxicity(text: str) -> bool:
    return contains_any(text, ("LTX", "LTx"))


def has_halogen_free(text: str) -> bool:
    return contains_any(text, ("HF",))


def has_cold_resistant(text: str) -> bool:
    return contains_any(text, ("\u0425\u041b", "HL"))


def has_intrinsically_safe_execution(text: str) -> bool:
    normalized = normalize_toflex_mark(text).upper()

    return re.search(r"(^|-|\s)I(-|\s|$)", normalized) is not None


def has_oil_resistance(text: str) -> bool:
    normalized = normalize_toflex_mark(text).upper()

    return re.search(r"(^|-|\s)\u041c(-|\s|$)", normalized) is not None


def has_uv_resistant(text: str) -> bool:
    return contains_any(text, ("\u0423\u0424", "UF"))


def has_water_blocking(text: str) -> bool:
    normalized = normalize_toflex_mark(text)

    return re.search(
        r"(^|-|\s)(\u0432|v)(-|\s|$)",
        normalized,
        re.IGNORECASE,
    ) is not None


def has_blue_sheath(text: str) -> bool:
    normalized = normalize_toflex_mark(text)

    return re.search(
        r"(^|-|\s)(\u0441|s)(-|\s|$)",
        normalized,
        re.IGNORECASE,
    ) is not None


def has_tinned_conductor_suffix(text: str) -> bool:
    normalized = normalize_toflex_mark(text)

    return re.search(
        r"\d+(?:\.\d+)?\s*(\u043b|l)(?:\s|-|$)",
        normalized,
        re.IGNORECASE,
    ) is not None


def extract_toflex_core_groups(text: str) -> Optional[int]:
    normalized = normalize_toflex_mark(text)

    match = re.search(r"(\d+)\s*x\s*\d+\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        return int(match.group(1))

    return None


def extract_toflex_group_type(text: str) -> Optional[str]:
    normalized = normalize_toflex_mark(text)

    match = re.search(r"\d+\s*x\s*(\d+)\s*x\s*[\d.]+", normalized)

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


def extract_toflex_cross_section_designation(text: str) -> Optional[str]:
    normalized = (
        repair_mojibake(text)
        .replace("\u00d7", "x")
        .replace("\u0445", "x")
        .replace("*", "x")
    )

    match = re.search(r"\d+\s*x\s*\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    match = re.search(r"\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    return None


def extract_toflex_cross_section_mm2(text: str) -> Optional[float]:
    designation = extract_toflex_cross_section_designation(text)

    if designation is None:
        return None

    return float(designation.replace(",", "."))


def extract_toflex_conductor_flexibility_class(text: str) -> int:
    normalized = normalize_toflex_mark(text)

    if re.search(r"[\d.]\s*(\u043e\u043a|ok)(?=\s|-|$)", normalized, re.IGNORECASE):
        return 1

    if re.search(r"[\d.]\s*(\u043c\u043a|mk)(?=\s|-|$)", normalized, re.IGNORECASE):
        return 2

    return 5


def extract_rated_voltage_v(text: str) -> Optional[int]:
    normalized = normalize_toflex_mark(text).upper()

    match = re.search(r"(?:-|\s)(\d{3,4})\s*(?:\u0412|V)?\s*$", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d{3,4})\s*(?:\u0412|V)", normalized)

    if match:
        return int(match.group(1))

    return None
