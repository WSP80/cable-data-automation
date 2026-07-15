from src.feature_engineering import FeatureBuilder
from src.models.cable import Cable
from src.parsers.registry import PARSERS


parser = PARSERS["atomkip"]

product_description = (
    "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
    "\u0412\u041e\u0444\u0412\u043d\u0433(A)-LS-"
    "\u0425\u041b-\u0423\u0424 2\u04452\u04451,5\u043a\u043b5 690\u0412"
)

ucm = parser.parse(product_description)

cable = Cable(
    source_file="demo.csv",
    invoice_number="DEMO-001",
    invoice_date="2026-04-20",
    product_description=product_description,
    length_km=0.5,
    unit_price_excl_vat=1200.0,
    comment="demo row",
    ucm=ucm,
)

features = FeatureBuilder().build_dataframe([cable])

print(features.to_string(index=False))
