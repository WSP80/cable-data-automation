from dataclasses import dataclass
from typing import Optional

from src.models.ucm import UCM


@dataclass
class Cable:
    """
    Commercial cable item from invoice or price list.

    This class stores source and commercial information,
    while UCM stores the normalized technical cable structure.
    """

    # Source information
    source_file: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None

    # Original product data
    product_description: Optional[str] = None
    cable_family: Optional[str] = None

    # Commercial data
    length_km: Optional[float] = None
    unit_price_excl_vat: Optional[float] = None
    comment: Optional[str] = None

    # Normalized technical model
    ucm: Optional[UCM] = None