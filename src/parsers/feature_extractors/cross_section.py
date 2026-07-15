import re
from typing import Optional

from src.parsers.text_normalization import repair_mojibake
from src.parsers.text_normalization import normalize_for_matching


def extract_cross_section_mm2(text: str) -> Optional[float]:
    """
    Extract conductor cross-section in square millimeters.
    """

    normalized = normalize_for_matching(text)

    match = re.search(r"\d+\s*x\s*\d+\s*x\s*([\d.]+)", normalized)

    if match:
        return float(match.group(1))

    match = re.search(r"\d+\s*x\s*([\d.]+)", normalized)

    if match:
        return float(match.group(1))

    return None


def extract_cross_section_designation(text: str) -> Optional[str]:
    """
    Extract cross-section exactly as it is written in the designation.
    """

    if not text:
        return None

    normalized = (
        repair_mojibake(text)
        .replace("×", "x")
        .replace("х", "x")
        .replace("Х", "x")
        .replace("*", "x")
    )

    match = re.search(r"\d+\s*x\s*\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    match = re.search(r"\d+\s*x\s*([\d,.]+)", normalized)

    if match:
        return match.group(1)

    return None
