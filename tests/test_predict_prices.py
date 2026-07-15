import pandas as pd

from scripts.predict_prices import (
    load_prediction_source,
    predict_ucm_frame,
    predict_ucm_frame_all_models,
    write_prediction_report,
)
from scripts.export_ucm import load_manufacturer_config
from src.descriptions import transliterate_designation
from src.feature_engineering import FeatureBuilder
from src.parsers.registry import PARSERS
from src.pricing import (
    PriceModelConfig,
    UCMPriceModelCatalog,
    ManufacturerPriceModel,
)


def test_predict_ucm_frame_adds_model_price_without_overwriting_actual_price():
    rows = []

    for index, section in enumerate([0.5, 1.0, 1.5] * 2):
        rows.append(
            {
                "cable_family": "MK",
                "group_type": "core",
                "overall_screen": "None",
                "core_groups": 2,
                "cross_section_mm2": section,
                "total_conductors": 2,
                "copper_area_mm2": section * 2,
                "unit_price_excl_vat": 1000 + index * 100,
            }
        )

    training = pd.DataFrame(rows)
    model = ManufacturerPriceModel(
        "MK",
        config=PriceModelConfig(
            min_training_rows=6,
            min_feature_value_rows=6,
            min_unique_cross_sections=3,
            boosting_max_iter=5,
        ),
    ).fit(training)
    input_frame = training.iloc[[0]].copy()
    input_frame["unit_price_excl_vat"] = None

    result = predict_ucm_frame(
        input_frame,
        UCMPriceModelCatalog({"MK": model}),
    )

    assert pd.isna(result.loc[0, "unit_price_excl_vat"])
    assert result.loc[0, "model_price_excl_vat"] > 0
    assert result.loc[0, "prediction_status"] == "ok"


def test_load_prediction_source_accepts_one_designation_per_line(tmp_path):
    input_path = tmp_path / "ATOMKIP-KU.csv"
    input_path.write_text(
        "ATOMKIP-KUVVng(A)-LS 2x2x1,0kl5 690V\n"
        "ATOMKIP-KUVVng(A)-LS 4x2x1,5kl5 690V\n",
        encoding="utf-8",
    )

    source = load_prediction_source(input_path)

    assert source["product_description"].tolist() == [
        "ATOMKIP-KUVVng(A)-LS 2x2x1,0kl5 690V",
        "ATOMKIP-KUVVng(A)-LS 4x2x1,5kl5 690V",
    ]


def test_load_prediction_source_accepts_windows_1251(tmp_path):
    input_path = tmp_path / "ATOMKIP-KU.csv"
    designation = "АТОМКИП-КУВВнг(А)-LS 2х2х1,0кл5 690В"
    input_path.write_bytes(designation.encode("cp1251"))

    source = load_prediction_source(input_path)

    assert source.loc[0, "product_description"] == designation


def test_predict_ucm_frame_all_models_returns_one_row_per_manufacturer():
    ucm = PARSERS["atomkip"].parse(
        "АТОМКИП-КУВВнг(А)-LS 2х2х1,0кл5 660В"
    )
    ucm_frame = pd.DataFrame([FeatureBuilder().ucm_to_features(ucm)])

    result = predict_ucm_frame_all_models(
        ucm_frame,
        UCMPriceModelCatalog({}),
        load_manufacturer_config(),
    )

    assert len(result) == 4
    assert set(result["target_manufacturer"]) == {
        "ATOMKIP-KU",
        "CONFLEX",
        "MK",
        "TOFLEX",
    }
    assert result["generated_designation"].notna().all()
    assert result["construction_description"].notna().all()

    for _, row in result.iterrows():
        assert not any(
            "\u0400" <= character <= "\u04ff"
            for character in row["generated_designation"]
        )
        first_description_line = row["construction_description"].splitlines()[0]
        assert first_description_line == transliterate_designation(
            row["generated_designation"],
            row["target_cable_family"],
        )


def test_atomkip_690_volts_maps_to_660_for_other_manufacturers():
    ucm = PARSERS["atomkip"].parse(
        "АТОМКИП-КУВВнг(А)-LS 2х2х1,0кл5 690В"
    )
    ucm_frame = pd.DataFrame([FeatureBuilder().ucm_to_features(ucm)])

    result = predict_ucm_frame_all_models(
        ucm_frame,
        UCMPriceModelCatalog({}),
        load_manufacturer_config(),
    ).set_index("target_manufacturer")

    assert result.loc["ATOMKIP-KU", "effective_target_voltage_v"] == 690

    for manufacturer in ("CONFLEX", "MK", "TOFLEX"):
        assert result.loc[manufacturer, "effective_target_voltage_v"] == 660
        assert bool(
            result.loc[manufacturer, "voltage_equivalence_applied"]
        )
        assert "660" in result.loc[manufacturer, "generated_designation"]


def test_target_cable_family_is_filled_when_generation_is_skipped():
    ucm = PARSERS["atomkip"].parse(
        "РђРўРћРњРљРРџ-РљРЈР’Р’РЅРі(Рђ)-LS 2С…2С…1,0РєР»5 690Р’"
    )
    features = FeatureBuilder().ucm_to_features(ucm)
    features["rated_voltage_v"] = 999
    ucm_frame = pd.DataFrame([features])

    result = predict_ucm_frame_all_models(
        ucm_frame,
        UCMPriceModelCatalog({}),
        load_manufacturer_config(),
    ).set_index("target_manufacturer")

    assert result["target_cable_family"].notna().all()
    assert result.loc["ATOMKIP-KU", "target_cable_family"] == "ATOMKIP-KU"
    assert result.loc["CONFLEX", "target_cable_family"] == "CONFLEX"
    assert result.loc["MK", "target_cable_family"] == "MK"
    assert result.loc["TOFLEX", "target_cable_family"] == "TOFLEX-KU"
    assert result["construction_description"].isna().all()


def test_prediction_report_separates_source_groups_with_blank_line(tmp_path):
    result = pd.DataFrame(
        [
            {"source_row_number": 1, "target_manufacturer": "ATOMKIP-KU"},
            {"source_row_number": 1, "target_manufacturer": "MK"},
            {"source_row_number": 2, "target_manufacturer": "ATOMKIP-KU"},
            {"source_row_number": 2, "target_manufacturer": "MK"},
        ]
    )
    output_path = tmp_path / "report.csv"

    write_prediction_report(result, output_path)
    text = output_path.read_text(encoding="utf-8-sig")

    assert "1;MK\n\n2;ATOMKIP-KU" in text
