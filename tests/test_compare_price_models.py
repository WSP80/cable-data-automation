import pandas as pd

from scripts.compare_price_models import compare_models
from src.pricing import PriceModelConfig


def test_compare_price_models_uses_same_split_and_returns_all_candidates():
    rows = []

    for index in range(40):
        conductors = (index % 5) + 1
        cross_section = float((index % 4) + 1)
        rows.append(
            {
                "cable_family": "ATOMKIP-KU",
                "group_type": "core",
                "overall_screen": "None" if index % 2 else "Aluminum foil",
                "core_groups": conductors,
                "cross_section_mm2": cross_section,
                "total_conductors": conductors,
                "copper_area_mm2": conductors * cross_section,
                "unit_price_excl_vat": 1000 + 120 * conductors * cross_section,
            }
        )

    report = compare_models(
        pd.DataFrame(rows),
        config=PriceModelConfig(test_size=0.25, random_seed=7),
    )

    assert set(report["model"]) == {
        "ridge",
        "elastic_net",
        "random_forest",
        "extra_trees",
        "hist_gradient_boosting",
    }
    assert report["train_rows"].eq(30).all()
    assert report["test_rows"].eq(10).all()
    assert report["mape"].notna().all()
