from src.models.cable import Cable
from src.models.ucm import UCM


class ParserPipeline:
    """
    Converts standardized invoice rows into Cable objects with UCM.
    """

    def __init__(self, parsers: dict):
        self.parsers = parsers

    def parse_row(self, row, manufacturer: str) -> Cable:
        if manufacturer not in self.parsers:
            raise ValueError(f"No parser registered for manufacturer: {manufacturer}")

        parser = self.parsers[manufacturer]

        ucm: UCM = parser.parse(
            row["product_description"],
            comment=row.get("comment"),
        )
        ucm.calculate_derived_features()

        return Cable(
            source_file=row.get("source_file"),
            invoice_number=row.get("invoice_number"),
            invoice_date=row.get("invoice_date"),
            product_description=row.get("product_description"),
            cable_family=ucm.cable_family,
            length_km=row.get("length_km"),
            unit_price_excl_vat=row.get("unit_price_excl_vat"),
            comment=row.get("comment"),
            ucm=ucm,
        )

    def parse_dataframe(self, df, manufacturer: str) -> list[Cable]:
        return [
            self.parse_row(row, manufacturer)
            for _, row in df.iterrows()
        ]
