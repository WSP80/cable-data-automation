import re
from dataclasses import dataclass
from typing import Optional

from src.models.enums import ArmorType, InsulationMaterial, ScreenType, SheathMaterial
from src.models.enums import ConductorMaterial
from src.parsers.text_normalization import repair_mojibake


@dataclass
class ConstructionFeatures:
    individual_screen: Optional[str] = None
    insulation_material: Optional[str] = None
    overall_screen: Optional[str] = None
    armor_type: Optional[str] = None
    sheath_material: Optional[str] = None


INDIVIDUAL_SCREEN_TOKENS = [
    ("\u0418\u041c\u0424", "IMF", ScreenType.COPPER_FOIL.value),
    ("\u0418\u0424\u041B", "IFL", ScreenType.COMBINED.value),
    ("\u0418\u041C", "IM", ScreenType.COPPER_BRAID.value),
    ("\u0418\u041B", "IL", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u0418\u0424", "IF", ScreenType.ALUMINUM_FOIL.value),
]

INSULATION_TOKENS = [
    ("\u041F\u0421", "PS", InsulationMaterial.XLPO.value),
    ("\u0420\u042D", "RE", InsulationMaterial.EPR.value),
    ("\u0420\u041A", "RK", InsulationMaterial.CERAMIFIABLE_SILICONE.value),
    ("\u0412", "V", InsulationMaterial.PVC.value),
    ("\u041F", "P", InsulationMaterial.HALOGEN_FREE.value),
]

OVERALL_SCREEN_TOKENS = [
    ("\u041E\u0424\u041B", "OFL", ScreenType.COMBINED.value),
    ("\u041E\u041C\u0424", "OMF", ScreenType.COPPER_FOIL.value),
    ("\u041E\u041C", "OM", ScreenType.COPPER_BRAID.value),
    ("\u041E\u041B", "OL", ScreenType.TINNED_COPPER_BRAID.value),
    ("\u041E\u0424", "OF", ScreenType.ALUMINUM_FOIL.value),
]

ARMOR_TOKENS = [
    ("\u0411", "B", ArmorType.GALVANIZED_STEEL_TAPE_ARMOR.value),
    ("\u041A", "K", ArmorType.GALVANIZED_STEEL_WIRE_BRAID.value),
]

SHEATH_TOKENS = [
    ("\u0412", "V", SheathMaterial.PVC.value),
    ("\u041F", "P", SheathMaterial.HALOGEN_FREE.value),
]

CYRILLIC_TRANSLITERATION = {
    "\u0430": "a",
    "\u0431": "b",
    "\u0432": "v",
    "\u0433": "g",
    "\u0434": "d",
    "\u0435": "e",
    "\u0451": "e",
    "\u0436": "zh",
    "\u0437": "z",
    "\u0438": "i",
    "\u0439": "y",
    "\u043a": "k",
    "\u043b": "l",
    "\u043c": "m",
    "\u043d": "n",
    "\u043e": "o",
    "\u043f": "p",
    "\u0440": "r",
    "\u0441": "s",
    "\u0442": "t",
    "\u0443": "u",
    "\u0444": "f",
    "\u0445": "kh",
    "\u0446": "ts",
    "\u0447": "ch",
    "\u0448": "sh",
    "\u0449": "shch",
    "\u044a": "",
    "\u044b": "y",
    "\u044c": "",
    "\u044d": "e",
    "\u044e": "yu",
    "\u044f": "ya",
}


def normalize_atomkip_mark_text(text: str) -> str:
    return repair_mojibake(text).upper()


def transliterate_free_text(text: str) -> str:
    transliterated = "".join(
        CYRILLIC_TRANSLITERATION.get(character, character)
        for character in text.lower()
    )

    return re.sub(r"\s+", " ", transliterated).strip()


def contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return any(token in normalized for token in tokens)


def extract_mark_prefix_body(text: str) -> str:
    normalized = normalize_atomkip_mark_text(text)

    for family_token in ("\u041a\u0423", "KU"):
        if family_token in normalized:
            normalized = normalized.split(family_token, 1)[1]
            break

    stop_tokens = (
        "\u041d\u0413",
        "NG",
        "-LS",
        "-FR",
        "-\u0425\u041b",
        "-HL",
        "-\u0423\u0424",
        "-UF",
        " ",
    )
    stop_positions = [
        normalized.find(token)
        for token in stop_tokens
        if normalized.find(token) != -1
    ]

    if stop_positions:
        return normalized[:min(stop_positions)]

    return normalized


def consume_token(
    text: str,
    token_rules: list[tuple[str, str, str]],
) -> tuple[Optional[str], str]:
    for cyrillic_token, latin_token, value in token_rules:
        if text.startswith(cyrillic_token):
            return value, text[len(cyrillic_token):]

        if text.startswith(latin_token):
            return value, text[len(latin_token):]

    return None, text


def parse_construction_features(text: str) -> ConstructionFeatures:
    body = extract_mark_prefix_body(text)
    features = ConstructionFeatures()

    features.individual_screen, body = consume_token(body, INDIVIDUAL_SCREEN_TOKENS)
    features.insulation_material, body = consume_token(body, INSULATION_TOKENS)
    features.overall_screen, body = consume_token(body, OVERALL_SCREEN_TOKENS)
    features.armor_type, body = consume_token(body, ARMOR_TOKENS)
    features.sheath_material, body = consume_token(body, SHEATH_TOKENS)

    return features


def has_flame_retardant(text: str) -> bool:
    return contains_any(text, ("\u041d\u0413(A)", "\u041d\u0413(\u0410)", "NG(A)"))


def has_low_smoke(text: str) -> bool:
    return contains_any(text, ("LS",))


def has_cold_resistant(text: str) -> bool:
    return contains_any(text, ("\u0425\u041b", "HL"))


def has_uv_resistant(text: str) -> bool:
    return contains_any(text, ("\u0423\u0424", "UF"))


def extract_overall_screen(text: str) -> Optional[str]:
    return parse_construction_features(text).overall_screen


def has_individual_screen(text: str) -> bool:
    return parse_construction_features(text).individual_screen is not None


def extract_individual_screen(text: str) -> Optional[str]:
    return parse_construction_features(text).individual_screen


def extract_insulation_material(text: str) -> Optional[str]:
    return parse_construction_features(text).insulation_material


def extract_sheath_material(text: str) -> Optional[str]:
    return parse_construction_features(text).sheath_material


def extract_armor_type(text: str) -> Optional[str]:
    return parse_construction_features(text).armor_type


def extract_conductor_flexibility_class(text: str) -> Optional[int]:
    match = re.search(r"(\u041a\u041b|KL)\s*(\d+)", normalize_atomkip_mark_text(text))

    if match:
        return int(match.group(2))

    return None


def has_fire_resistant_halogen_free(text: str) -> bool:
    return contains_any(text, ("FRHF",))


def has_fire_resistant(text: str) -> bool:
    return contains_any(text, ("FR",))


def has_halogen_free(text: str) -> bool:
    return contains_any(text, ("HF",))


def has_low_toxicity(text: str) -> bool:
    return contains_any(text, ("LTX", "LSTX", "LSLT"))


def has_aggressive_environment_resistance(text: str) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return re.search(r"-(\u0410\u0421|AC)(-|\s|$)", normalized) is not None


def has_oil_resistance(text: str) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return re.search(r"-(\u041C|M)(-|\s|$)", normalized) is not None


def has_water_blocking(text: str) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return re.search(r"-(\u0412|V)(-|\s|$)", normalized) is not None


def has_intrinsically_safe_execution(text: str) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return re.search(r"-I(-|\s|$)", normalized) is not None


def has_explosive_area_application(text: str) -> bool:
    normalized = normalize_atomkip_mark_text(text)

    return normalized.startswith("\u0412\u0417-") or normalized.startswith("VZ-")


def extract_sheath_color(text: str) -> Optional[str]:
    normalized = repair_mojibake(text)
    voltage_match = re.search(r"\d{3,4}\s*[\u0412V]", normalized, re.IGNORECASE)

    if not voltage_match:
        return None

    tail = normalized[voltage_match.end():].strip()

    if not tail:
        return None

    if tail.startswith("(") and tail.endswith(")"):
        tail = tail[1:-1].strip()

    if not tail:
        return None

    return transliterate_free_text(tail)


def extract_conductor_material(text: str) -> Optional[str]:
    normalized = normalize_atomkip_mark_text(text)

    if re.search(r"\d+[.,]\d+\s*\u041b\s*\u041a\u041b\d+", normalized):
        return ConductorMaterial.CU_TINNED.value

    if re.search(r"\d+[.,]\d+\s*L\s*KL\d+", normalized):
        return ConductorMaterial.CU_TINNED.value

    return None


def comment_sets_one_mica_tape_layer(comment: Optional[str]) -> bool:
    if not comment:
        return False

    normalized = normalize_atomkip_mark_text(comment).replace(" ", "")

    return "FR=1" in normalized


def extract_mica_tape_layers(
    designation: str,
    insulation_material: Optional[str],
    comment: Optional[str] = None,
) -> int:
    if not has_fire_resistant(designation):
        return 0

    if insulation_material == InsulationMaterial.CERAMIFIABLE_SILICONE.value:
        return 0

    if comment_sets_one_mica_tape_layer(comment):
        return 1

    return 2
