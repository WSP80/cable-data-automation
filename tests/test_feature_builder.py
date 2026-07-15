import pandas as pd

from src.feature_engineering import FeatureBuilder
from src.models.cable import Cable
from src.models.ucm import UCM


def test_feature_builder_creates_ml_dataframe_from_cables():
    ucm = UCM(
        cable_family="ATOMKIP-KU",
        core_groups=2,
        group_type="pair",
        cross_section_mm2=1.5,
        rated_voltage_v=690,
    )
    cable = Cable(
        source_file="invoice.csv",
        invoice_number="INV-001",
        invoice_date="2026-04-20",
        product_description="ATOMKIP-KU 2x2x1,5 690V",
        length_km=0.5,
        unit_price_excl_vat=1200.0,
        comment="sample",
        ucm=ucm,
    )

    df = FeatureBuilder().build_dataframe([cable])

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.loc[0, "source_file"] == "invoice.csv"
    assert df.loc[0, "unit_price_excl_vat"] == 1200.0
    assert df.loc[0, "core_groups"] == 2
    assert df.loc[0, "group_type"] == "pair"
    assert df.loc[0, "cross_section_mm2"] == 1.5
    assert "cross_section_designation" in df.columns
    assert df.loc[0, "rated_voltage_v"] == 690
    assert df.loc[0, "total_conductors"] == 4
    assert df.loc[0, "copper_area_mm2"] == 6.0


def test_feature_builder_requires_parsed_ucm():
    cable = Cable(product_description="ATOMKIP-KU 2x2x1,5 690V")

    try:
        FeatureBuilder().cable_to_features(cable)
    except ValueError as error:
        assert "no UCM" in str(error)
    else:
        raise AssertionError("Expected ValueError for cable without UCM")
