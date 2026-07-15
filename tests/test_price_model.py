import pandas as pd

from src.pricing import ManufacturerPriceModel, PriceModelConfig
from src.pricing import fit_price_models_from_ucm_dir, load_ucm_price_frames
from src.pricing import load_price_model_catalog, save_price_model_catalog
from src.pricing.price_model import parse_decimal


def base_training_rows() -> list[dict]:
    rows = []

    for price in [1000, 1100, 1200]:
        rows.append(
            {
                "cable_family": "MK",
                "group_type": "pair",
                "conductor_flexibility_class": 5,
                "conductor_material": "Cu",
                "insulation_material": "PVC",
                "individual_screen": "None",
                "overall_screen": "Aluminum foil",
                "sheath_material": "PVC",
                "armor_type": "None",
                "flame_retardant": True,
                "fire_resistant": False,
                "low_smoke": True,
                "low_toxicity": False,
                "halogen_free": False,
                "rated_voltage_v": 660,
                "sheath_color": "black",
                "core_groups": 2,
                "cross_section_mm2": 1.0,
                "total_conductors": 4,
                "copper_area_mm2": 4.0,
                "unit_price_excl_vat": price,
            }
        )

    return rows


def test_parse_decimal_accepts_comma_decimal_text():
    assert parse_decimal("107278,262") == 107278.262
    assert parse_decimal("1 234,5") == 1234.5
    assert parse_decimal(None) is None


def test_price_model_predicts_with_regression_for_sufficient_data():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)

    prediction = model.predict(frame.iloc[0].to_dict())

    assert prediction.can_predict is True
    assert prediction.status == "ok"
    assert prediction.model_type == "ucm_hist_gradient_boosting"
    assert 900 < prediction.predicted_price < 1300
    assert prediction.comparable_rows == 3


def test_price_model_counts_comparable_training_groups():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)

    assert model.comparable_group_sizes().tolist() == [3, 3, 3]


def test_price_model_exposes_train_test_metrics():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        test_size=0.34,
        random_seed=1,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)

    metrics = model.metrics()

    assert metrics is not None
    assert metrics.train_rows == 2
    assert metrics.test_rows == 1
    assert metrics.mae is not None


def test_price_model_rejects_insufficient_feature_value_coverage():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)
    features = frame.iloc[0].to_dict()
    features["overall_screen"] = "Copper foil"

    prediction = model.predict(features)

    assert prediction.can_predict is False
    assert prediction.status == "insufficient_feature_value_data"
    assert "overall_screen=Copper foil (0 < 3)" in prediction.reason


def test_price_model_rejects_small_training_set():
    frame = pd.DataFrame(base_training_rows()[:2])
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=2,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)

    prediction = model.predict(frame.iloc[0].to_dict())

    assert prediction.can_predict is False
    assert prediction.status == "insufficient_model_data"


def test_ucm_price_catalog_trains_from_ucm_folder(tmp_path):
    frame = pd.DataFrame(base_training_rows())
    frame.to_csv(
        tmp_path / "MK_UCM.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )
    frame.assign(
        cable_family="CONFLEX",
        unit_price_excl_vat=["2000,0", "2100,0", "2200,0"],
    ).to_csv(
        tmp_path / "CONFLEX_UCM.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    frames = load_ucm_price_frames(tmp_path)
    catalog = fit_price_models_from_ucm_dir(
        tmp_path,
        config=PriceModelConfig(
            min_training_rows=3,
            min_feature_value_rows=3,
            min_unique_cross_sections=1,
        ),
    )
    features = frame.iloc[0].to_dict()
    prediction = catalog.predict(features)

    assert len(frames) == 2
    assert sorted(catalog.models) == ["CONFLEX", "MK"]
    assert prediction.can_predict is True
    assert 900 < prediction.predicted_price < 1300


def test_ucm_price_catalog_rejects_missing_family():
    catalog = fit_price_models_from_ucm_dir(
        ".",
        config=PriceModelConfig(
            min_training_rows=3,
            min_feature_value_rows=3,
            min_unique_cross_sections=1,
        ),
        pattern="no-such-file.csv",
    )

    prediction = catalog.predict({"core_groups": 2})

    assert prediction.can_predict is False
    assert prediction.status == "missing_cable_family"


def test_price_model_counts_feature_coverage_ready_rows():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)

    assert model.coverage_ready_rows().tolist() == [True, True, True]


def test_price_model_uses_copper_area_and_total_conductors_without_coverage_gate():
    frame = pd.DataFrame(base_training_rows())
    config = PriceModelConfig(
        min_training_rows=3,
        min_feature_value_rows=3,
        min_unique_cross_sections=1,
    )
    model = ManufacturerPriceModel("MK", config=config).fit(frame)
    features = frame.iloc[0].to_dict()
    features["copper_area_mm2"] = 999.0
    features["total_conductors"] = 999

    prediction = model.predict(features)

    assert prediction.can_predict is True
    assert "copper_area_mm2" not in prediction.matched_features
    assert "total_conductors" not in prediction.matched_features
    assert "copper_area_mm2" in model.regression_model.numeric_features
    assert "total_conductors" in model.regression_model.numeric_features


def test_catalog_reports_feature_value_prediction_coverage(tmp_path):
    frame = pd.DataFrame(base_training_rows())
    frame.to_csv(
        tmp_path / "MK_UCM.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )
    catalog = fit_price_models_from_ucm_dir(
        tmp_path,
        config=PriceModelConfig(
            min_training_rows=3,
            min_feature_value_rows=3,
            min_unique_cross_sections=1,
            boosting_max_iter=5,
        ),
    )

    report = catalog.feature_coverage_frame()
    copper_area = report[report["feature"] == "copper_area_mm2"].iloc[0]
    overall_screen = report[
        (report["feature"] == "overall_screen")
        & (report["value"] == "Aluminum foil")
    ].iloc[0]

    assert copper_area["value"] == "ALL_VALUES"
    assert copper_area["used_in_coverage_gate"] == False
    assert overall_screen["rows"] == 3
    assert overall_screen["valid_for_prediction"] == True


def test_price_model_allows_cross_section_extrapolation_with_diverse_training_data():
    frame = pd.DataFrame(base_training_rows() * 2)
    frame["cross_section_mm2"] = [0.5, 1.0, 1.5, 0.5, 1.0, 1.5]
    frame["copper_area_mm2"] = (
        frame["cross_section_mm2"] * frame["total_conductors"]
    )
    model = ManufacturerPriceModel(
        "MK",
        config=PriceModelConfig(
            min_training_rows=6,
            min_feature_value_rows=6,
            min_unique_cross_sections=3,
            allow_cross_section_extrapolation=True,
            boosting_max_iter=5,
        ),
    ).fit(frame)
    features = frame.iloc[0].to_dict()
    features["cross_section_mm2"] = 6.0
    features["copper_area_mm2"] = 24.0

    prediction = model.predict(features)

    assert prediction.can_predict is True


def test_price_model_rejects_insufficient_cross_section_diversity():
    frame = pd.DataFrame(base_training_rows())
    model = ManufacturerPriceModel(
        "MK",
        config=PriceModelConfig(
            min_training_rows=3,
            min_feature_value_rows=3,
            min_unique_cross_sections=2,
            boosting_max_iter=5,
        ),
    ).fit(frame)

    prediction = model.predict(frame.iloc[0].to_dict())

    assert prediction.can_predict is False
    assert "cross_section_mm2 has only 1 unique values (< 2)" in prediction.reason


def test_price_model_catalog_can_be_saved_and_loaded(tmp_path):
    frame = pd.DataFrame(base_training_rows())
    frame.to_csv(
        tmp_path / "MK_UCM.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )
    catalog = fit_price_models_from_ucm_dir(
        tmp_path,
        config=PriceModelConfig(
            min_training_rows=3,
            min_feature_value_rows=3,
            min_unique_cross_sections=1,
            boosting_max_iter=5,
        ),
    )
    model_path = save_price_model_catalog(
        catalog,
        tmp_path / "models" / "catalog.joblib",
    )

    loaded = load_price_model_catalog(model_path)
    prediction = loaded.predict(frame.iloc[0].to_dict())

    assert prediction.can_predict is True
    assert prediction.model_type == "ucm_hist_gradient_boosting"
