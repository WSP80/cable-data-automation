from typing import Iterable

import pandas as pd

from src.models.cable import Cable
from src.models.ucm import UCM


COMMERCIAL_COLUMNS = [
    "source_file",
    "invoice_number",
    "invoice_date",
    "product_description",
    "length_km",
    "unit_price_excl_vat",
    "comment",
]

TECHNICAL_COLUMNS = [
    "cable_family",
    "core_groups",
    "group_type",
    "cross_section_mm2",
    "cross_section_designation",
    "conductor_flexibility_class",
    "conductor_material",
    "insulation_material",
    "mica_tape_layers",
    "individual_screen",
    "filler_material",
    "bedding_under_screen",
    "overall_screen",
    "sheath_material",
    "armor_type",
    "water_blocking",
    "flame_retardant",
    "fire_resistant",
    "low_smoke",
    "low_toxicity",
    "halogen_free",
    "cold_resistant",
    "uv_resistant",
    "oil_resistant",
    "chemical_resistant",
    "rated_voltage_v",
    "intrinsically_safe",
    "explosive_area_application",
    "sheath_color",
    "total_conductors",
    "copper_area_mm2",
]


class FeatureBuilder:
    """
    Convert parsed cable objects into a machine-learning feature table.
    """

    def ucm_to_features(self, ucm: UCM) -> dict:
        ucm.finalize_features()

        return {
            column: getattr(ucm, column)
            for column in TECHNICAL_COLUMNS
        }

    def cable_to_features(self, cable: Cable) -> dict:
        if cable.ucm is None:
            raise ValueError("Cable has no UCM. Parse the cable before feature building.")

        row = {
            column: getattr(cable, column)
            for column in COMMERCIAL_COLUMNS
        }

        row.update(self.ucm_to_features(cable.ucm))

        return row

    def build_dataframe(self, cables: Iterable[Cable]) -> pd.DataFrame:
        rows = [
            self.cable_to_features(cable)
            for cable in cables
        ]

        return pd.DataFrame(rows, columns=COMMERCIAL_COLUMNS + TECHNICAL_COLUMNS)
