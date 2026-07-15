import re
from typing import Optional

from src.models.enums import GroupType
from src.parsers.text_normalization import normalize_for_matching


def extract_group_type(text: str) -> Optional[str]:
    """
    Extract conductor grouping type from a cable designation.
    """

    normalized = normalize_for_matching(text)

    match = re.search(r"\d+\s*x\s*(\d+)\s*x\s*[\d.]+", normalized)

    if match:
        conductors_per_group = int(match.group(1))

        if conductors_per_group == 2:
            return GroupType.PAIR.value
        if conductors_per_group == 3:
            return GroupType.TRIPLE.value
        if conductors_per_group == 4:
            return GroupType.QUAD.value

    match = re.search(r"\d+\s*x\s*[\d.]+", normalized)

    if match:
        return GroupType.CORE.value

    return None
