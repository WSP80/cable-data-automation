import re
from typing import Optional

from src.parsers.text_normalization import normalize_designation


def extract_rated_voltage_v(text: str) -> Optional[int]:
    """
    Extract rated AC voltage.
    """

    normalized = normalize_designation(text).upper()

    match = re.search(r"(\d{3,4})\s*V", normalized)

    if match:
        return int(match.group(1))

    return None
