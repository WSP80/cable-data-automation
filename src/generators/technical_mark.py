from src.models.ucm import UCM


def format_number(value: float) -> str:
    """
    Format numeric values without unnecessary trailing zeros.
    """

    return f"{value:g}"


def format_core_construction(ucm: UCM) -> str:
    """
    Format the conductor construction part of a cable mark.
    """

    if ucm.core_groups is None or ucm.cross_section_mm2 is None:
        return "unknown"

    cross_section = format_number(ucm.cross_section_mm2)

    if ucm.group_type == "core":
        return f"{ucm.core_groups}x{cross_section}"

    group_size = {
        "pair": 2,
        "triple": 3,
        "quad": 4,
    }.get(ucm.group_type)

    if group_size is None:
        return f"{ucm.core_groups}x{cross_section}"

    return f"{ucm.core_groups}x{group_size}x{cross_section}"


def build_technical_mark(prefix: str, ucm: UCM) -> str:
    """
    Build a compact manufacturer mark from shared UCM fields.
    """

    parts = [prefix, format_core_construction(ucm)]

    if ucm.rated_voltage_v is not None:
        parts.append(f"{ucm.rated_voltage_v}V")

    return " ".join(parts)
