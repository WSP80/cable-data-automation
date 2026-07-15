import pandas as pd
from sqlalchemy import create_engine, func, select

from src.database import (
    Base,
    CableRepository,
    ModelRun,
    PricePrediction,
    SourceOffer,
)
from src.pricing import (
    ManufacturerPriceModel,
    PriceModelConfig,
    UCMPriceModelCatalog,
)


def training_frame() -> pd.DataFrame:
    rows = []

    for index, section in enumerate([0.5, 1.0, 1.5] * 2):
        rows.append(
            {
                "source_file": "test.csv",
                "invoice_number": f"INV-{index}",
                "invoice_date": "2026-07-09",
                "product_description": f"MKV 2x{section}",
                "length_km": 1.0,
                "unit_price_excl_vat": 1000 + index * 100,
                "comment": None,
                "cable_family": "MK",
                "core_groups": 2,
                "group_type": "core",
                "cross_section_mm2": section,
                "cross_section_designation": str(section),
                "individual_screen": "None",
                "overall_screen": "None",
                "armor_type": "None",
                "total_conductors": 2,
                "copper_area_mm2": section * 2,
            }
        )

    return pd.DataFrame(rows)


def repository() -> CableRepository:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return CableRepository(engine)


def test_ucm_import_is_idempotent_and_training_data_can_be_loaded():
    repo = repository()
    frame = training_frame()

    offer_ids, first_inserted = repo.store_ucm_frame(
        frame,
        "training",
        source_dataset="MK_UCM.csv",
    )
    repeated_ids, second_inserted = repo.store_ucm_frame(
        frame,
        "training",
        source_dataset="MK_UCM.csv",
    )
    loaded = repo.load_training_frame()

    assert first_inserted == 6
    assert second_inserted == 0
    assert repeated_ids == offer_ids
    assert len(loaded) == 6
    assert loaded["cable_family"].unique().tolist() == ["MK"]
    assert loaded["invoice_number"].tolist() == [
        "INV-0",
        "INV-1",
        "INV-2",
        "INV-3",
        "INV-4",
        "INV-5",
    ]
    assert loaded["individual_screen"].eq("None").all()
    assert loaded["overall_screen"].eq("None").all()
    assert loaded["armor_type"].eq("None").all()


def test_current_training_load_marks_previous_rows_as_not_current():
    repo = repository()
    frame = training_frame()

    repo.start_current_load("training")
    offer_ids, first_inserted = repo.store_ucm_frame(
        frame,
        "training",
        source_dataset="MK_UCM.csv",
        load_run_id="first-load",
    )
    repo.start_current_load("training")
    repeated_ids, second_inserted = repo.store_ucm_frame(
        frame.iloc[:2],
        "training",
        source_dataset="MK_UCM.csv",
        load_run_id="second-load",
    )

    with repo.session_factory() as session:
        offers = session.scalars(
            select(SourceOffer).order_by(SourceOffer.source_row_number)
        ).all()

    assert first_inserted == 6
    assert second_inserted == 0
    assert repeated_ids == offer_ids[:2]
    assert [offer.is_current_load for offer in offers] == [
        True,
        True,
        False,
        False,
        False,
        False,
    ]
    assert [offer.load_run_id for offer in offers[:2]] == [
        "second-load",
        "second-load",
    ]


def test_model_runs_and_predictions_are_recorded():
    repo = repository()
    frame = training_frame()
    offer_ids, _ = repo.store_ucm_frame(frame.iloc[[0]], "prediction")
    model = ManufacturerPriceModel(
        "MK",
        config=PriceModelConfig(
            min_training_rows=6,
            min_feature_value_rows=6,
            min_unique_cross_sections=3,
            boosting_max_iter=5,
        ),
    ).fit(frame)
    catalog = UCMPriceModelCatalog({"MK": model})
    run_ids = repo.record_model_runs(catalog, "model.joblib")
    prediction_frame = frame.iloc[[0]].assign(
        model_price_excl_vat=1234.56,
        prediction_status="ok",
        prediction_reason="Prediction produced.",
        prediction_model_type="ucm_hist_gradient_boosting",
        prediction_comparable_rows=6,
        target_manufacturer="MK",
        target_cable_family="MK",
        generated_designation="MKShV 2x0,5",
        construction_description="MKShV 2x0,5\nCable Family: MK",
        construction_compatible=True,
        compatibility_differences="",
        effective_target_voltage_v=660,
        voltage_equivalence_applied=False,
    )

    stored = repo.record_predictions(offer_ids, prediction_frame)

    with repo.session_factory() as session:
        offer_count = session.scalar(select(func.count(SourceOffer.id)))
        run_count = session.scalar(select(func.count(ModelRun.id)))
        prediction_count = session.scalar(select(func.count(PricePrediction.id)))
        prediction = session.scalar(select(PricePrediction))

    assert run_ids["MK"] > 0
    assert stored == 1
    assert offer_count == 1
    assert run_count == 1
    assert prediction_count == 1
    assert prediction.prediction_run_id is not None
    assert prediction.target_manufacturer == "MK"
    assert prediction.generated_designation == "MKShV 2x0,5"
    assert prediction.construction_description == "MKShV 2x0,5\nCable Family: MK"


def test_new_model_run_deactivates_models_not_present_in_current_training_run():
    repo = repository()
    frame = training_frame()
    model = ManufacturerPriceModel(
        "MK",
        config=PriceModelConfig(
            min_training_rows=6,
            min_feature_value_rows=6,
            min_unique_cross_sections=3,
            boosting_max_iter=5,
        ),
    ).fit(frame)

    first_run_ids = repo.record_model_runs(
        UCMPriceModelCatalog({"MK": model}),
        "first.joblib",
    )
    second_run_ids = repo.record_model_runs(
        UCMPriceModelCatalog({}),
        "second.joblib",
    )

    with repo.session_factory() as session:
        active_count = session.scalar(
            select(func.count(ModelRun.id)).where(ModelRun.is_active.is_(True))
        )
        first_run = session.get(ModelRun, first_run_ids["MK"])

    assert first_run_ids["MK"] > 0
    assert second_run_ids == {}
    assert active_count == 0
    assert first_run.is_active is False


def test_prediction_run_id_can_group_one_prediction_batch():
    repo = repository()
    frame = training_frame()
    offer_ids, _ = repo.store_ucm_frame(frame.iloc[[0]], "prediction")
    prediction_frame = frame.iloc[[0]].assign(
        model_price_excl_vat=None,
        prediction_status="insufficient_model_data",
        prediction_reason="No active model.",
        prediction_model_type=None,
        prediction_comparable_rows=0,
        target_manufacturer="TOFLEX",
        target_cable_family="TOFLEX-KU",
        generated_designation=None,
        construction_description=None,
        construction_compatible=False,
        compatibility_differences=None,
        effective_target_voltage_v=660,
        voltage_equivalence_applied=False,
    )

    repo.record_predictions(
        offer_ids,
        prediction_frame,
        prediction_run_id="test-prediction-run",
    )

    with repo.session_factory() as session:
        prediction = session.scalar(select(PricePrediction))

    assert prediction.prediction_run_id == "test-prediction-run"
