from typing import Optional


MULTIPLICATION_SIGN = chr(0x00D7)
CYRILLIC_SMALL_HA = chr(0x0445)
CYRILLIC_CAPITAL_HA = chr(0x0425)
CYRILLIC_CAPITAL_VE = chr(0x0412)
CYRILLIC_SMALL_VE = chr(0x0432)
MOJIBAKE_MULTIPLICATION_SIGN = chr(0x0413) + chr(0x2014)
MOJIBAKE_CYRILLIC_SMALL_HA = chr(0x0421) + chr(0x2026)
MOJIBAKE_CYRILLIC_CAPITAL_HA = chr(0x0420) + chr(0x0490)
MOJIBAKE_CYRILLIC_CAPITAL_VE = chr(0x0420) + chr(0x2019)


def repair_mojibake(text: Optional[str]) -> str:
    """
    Repair common UTF-8 text that was decoded as Windows-1251.
    """

    if text is None:
        return ""

    try:
        return text.encode("cp1251").decode("utf-8")
    except UnicodeError:
        return text


def normalize_designation(text: Optional[str]) -> str:
    """
    Normalize cable designations before rule-based parsing.
    """

    repaired = repair_mojibake(text)

    return (
        repaired.replace(MULTIPLICATION_SIGN, "x")
        .replace(MOJIBAKE_MULTIPLICATION_SIGN, "x")
        .replace(CYRILLIC_SMALL_HA, "x")
        .replace(MOJIBAKE_CYRILLIC_SMALL_HA, "x")
        .replace(CYRILLIC_CAPITAL_HA, "x")
        .replace(MOJIBAKE_CYRILLIC_CAPITAL_HA, "x")
        .replace("*", "x")
        .replace(",", ".")
        .replace(CYRILLIC_CAPITAL_VE, "V")
        .replace(MOJIBAKE_CYRILLIC_CAPITAL_VE, "V")
        .replace(CYRILLIC_SMALL_VE, "V")
        .strip()
    )


def normalize_for_matching(text: Optional[str]) -> str:
    """
    Normalize designation text and lower-case it for regex matching.
    """

    return normalize_designation(text).lower()
