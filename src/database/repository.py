from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

import numpy as np
import pandas as pd
from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session, sessionmaker

from src.database.models import Base, ModelRun, PricePrediction, SourceOffer, UCMFeature
from src.database.migrations import migrate_schema
from src.feature_engineering.feature_builder import COMMERCIAL_COLUMNS, TECHNICAL_COLUMNS
from src.pricing.price_model import PRICE_COLUMN, UCMPriceModelCatalog, parse_decimal


class CableRepository:
    def __init__(self, engine: Engine) -> None:
        self.engine = engine
        self.session_factory = sessionmaker(
            bind=engine,
            expire_on_commit=False,
            class_=Session,
        )

    def create_schema(self) -> None:
        Base.metadata.create_all(self.engine)
        migrate_schema(self.engine)

    def store_ucm_frame(
        self,
        frame: pd.DataFrame,
        dataset_role: str,
        source_dataset: str = "in_memory",
        load_run_id: str | None = None,
    ) -> tuple[list[int], int]:
        offer_ids = []
        inserted = 0
        run_id = load_run_id or str(uuid4())

        with self.session_factory.begin() as session:
            for row_number, (_, row) in enumerate(frame.iterrows(), start=1):
                values = {
                    column: self._clean_value(row.get(column))
                    for column in COMMERCIAL_COLUMNS + TECHNICAL_COLUMNS
                }
                row_hash = self._row_hash(
                    values,
                    dataset_role,
                    source_dataset,
                    row_number,
                )
                existing_id = session.scalar(
                    select(SourceOffer.id).where(SourceOffer.row_hash == row_hash)
                )

                if existing_id is not None:
                    session.execute(
                        update(SourceOffer)
                        .where(SourceOffer.id == existing_id)
                        .values(
                            load_run_id=run_id,
                            is_current_load=True,
                        )
                    )
                    offer_ids.append(existing_id)
                    continue

                offer = SourceOffer(
                    row_hash=row_hash,
                    dataset_role=dataset_role,
                    load_run_id=run_id,
                    is_current_load=True,
                    source_dataset=source_dataset,
                    source_row_number=row_number,
                    source_file=values["source_file"],
                    invoice_number=values["invoice_number"],
                    invoice_date=values["invoice_date"],
                    product_description=str(values["product_description"] or ""),
                    length_km=parse_decimal(values["length_km"]),
                    unit_price_excl_vat=parse_decimal(values[PRICE_COLUMN]),
                    comment=values["comment"],
                )
                session.add(offer)
                session.flush()
                session.add(
                    UCMFeature(
                        offer_id=offer.id,
                        **{
                            column: values[column]
                            for column in TECHNICAL_COLUMNS
                        },
                    )
                )
                offer_ids.append(offer.id)
                inserted += 1

        return offer_ids, inserted

    def start_current_load(self, dataset_role: str) -> None:
        with self.session_factory.begin() as session:
            session.execute(
                update(SourceOffer)
                .where(SourceOffer.dataset_role == dataset_role)
                .values(is_current_load=False)
            )

    def load_training_frame(self) -> pd.DataFrame:
        columns = [
            SourceOffer.source_file,
            SourceOffer.invoice_number,
            SourceOffer.invoice_date,
            SourceOffer.product_description,
            SourceOffer.length_km,
            SourceOffer.unit_price_excl_vat,
            SourceOffer.comment,
        ] + [
            getattr(UCMFeature, column)
            for column in TECHNICAL_COLUMNS
        ]
        statement = (
            select(*columns)
            .join(UCMFeature, UCMFeature.offer_id == SourceOffer.id)
            .where(
                SourceOffer.dataset_role == "training",
                SourceOffer.is_current_load.is_(True),
                SourceOffer.unit_price_excl_vat.is_not(None),
                SourceOffer.unit_price_excl_vat > 0,
            )
            .order_by(
                SourceOffer.source_dataset,
                SourceOffer.source_row_number,
                SourceOffer.id,
            )
        )
        frame = pd.read_sql(statement, self.engine)

        for feature in ("individual_screen", "overall_screen", "armor_type"):
            if feature in frame.columns:
                frame[feature] = frame[feature].fillna("None")

        return frame

    def record_model_runs(
        self,
        catalog: UCMPriceModelCatalog,
        artifact_path: str | Path,
    ) -> dict[str, int]:
        run_group_id = str(uuid4())
        model_run_ids = {}

        with self.session_factory.begin() as session:
            session.execute(
                update(ModelRun)
                .where(ModelRun.is_active.is_(True))
                .values(is_active=False)
            )

            for cable_family, model in sorted(catalog.models.items()):
                metrics = model.metrics()
                model_run = ModelRun(
                    run_group_id=run_group_id,
                    cable_family=cable_family,
                    model_type="ucm_hist_gradient_boosting",
                    artifact_path=str(artifact_path),
                    training_rows=metrics.train_rows if metrics else 0,
                    test_rows=metrics.test_rows if metrics else 0,
                    mae=metrics.mae if metrics else None,
                    mape=metrics.mape if metrics else None,
                    rmse=metrics.rmse if metrics else None,
                    r2=metrics.r2 if metrics else None,
                    is_active=model.regression_model is not None,
                )
                session.add(model_run)
                session.flush()
                model_run_ids[cable_family] = model_run.id

        return model_run_ids

    def active_model_run_ids(self) -> dict[str, int]:
        with self.session_factory() as session:
            rows = session.execute(
                select(ModelRun.cable_family, ModelRun.id).where(
                    ModelRun.is_active.is_(True)
                )
            ).all()
        return dict(rows)

    def record_predictions(
        self,
        offer_ids: list[int],
        prediction_frame: pd.DataFrame,
        prediction_run_id: str | None = None,
    ) -> int:
        if len(offer_ids) != len(prediction_frame):
            raise ValueError("Offer and prediction row counts must match.")

        active_runs = self.active_model_run_ids()
        run_id = prediction_run_id or str(uuid4())

        with self.session_factory.begin() as session:
            for offer_id, (_, row) in zip(offer_ids, prediction_frame.iterrows()):
                target_family = row.get(
                    "target_cable_family",
                    row.get("cable_family"),
                )
                session.add(
                    PricePrediction(
                        offer_id=offer_id,
                        model_run_id=active_runs.get(str(target_family)),
                        predicted_price=parse_decimal(row.get("model_price_excl_vat")),
                        status=str(row.get("prediction_status")),
                        reason=str(row.get("prediction_reason")),
                        model_type=self._clean_value(row.get("prediction_model_type")),
                        comparable_rows=int(row.get("prediction_comparable_rows") or 0),
                        prediction_run_id=run_id,
                        target_manufacturer=self._clean_value(
                            row.get("target_manufacturer")
                        ),
                        target_cable_family=self._clean_value(target_family),
                        generated_designation=self._clean_value(
                            row.get("generated_designation")
                        ),
                        construction_description=self._clean_value(
                            row.get("construction_description")
                        ),
                        construction_compatible=self._clean_value(
                            row.get("construction_compatible")
                        ),
                        compatibility_differences=self._clean_value(
                            row.get("compatibility_differences")
                        ),
                        effective_target_voltage_v=self._clean_value(
                            row.get("effective_target_voltage_v")
                        ),
                        voltage_equivalence_applied=self._clean_value(
                            row.get("voltage_equivalence_applied")
                        ),
                    )
                )

        return len(offer_ids)

    @staticmethod
    def _clean_value(value: Any) -> Any:
        if value is None or pd.isna(value):
            return None
        if isinstance(value, np.generic):
            return value.item()
        return value

    @staticmethod
    def _row_hash(
        values: dict[str, Any],
        dataset_role: str,
        source_dataset: str,
        source_row_number: int,
    ) -> str:
        payload = json.dumps(
            {
                "dataset_role": dataset_role,
                "source_dataset": source_dataset,
                "source_row_number": source_row_number,
                **values,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()
