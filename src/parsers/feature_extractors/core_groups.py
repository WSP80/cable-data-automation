import re
from typing import Optional

from src.parsers.text_normalization import normalize_for_matching


def extract_core_groups(text: str) -> Optional[int]:
    """
    Extract number of conductor groups from a cable designation.
    """

    normalized = normalize_for_matching(text)

    match = re.search(r"(\d+)\s*x\s*(\d+)\s*x\s*([\d.]+)", normalized)

    if match:
        return int(match.group(1))

    match = re.search(r"(\d+)\s*x\s*([\d.]+)", normalized)

    if match:
        return int(match.group(1))

    return None
