from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class SourceOffer(Base):
    __tablename__ = "source_offers"

    id: Mapped[int] = mapped_column(primary_key=True)
    row_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    dataset_role: Mapped[str] = mapped_column(String(20), index=True)
    load_run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    is_current_load: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    source_dataset: Mapped[str] = mapped_column(String(255), index=True)
    source_row_number: Mapped[int] = mapped_column(Integer)
    source_file: Mapped[str | None] = mapped_column(Text)
    invoice_number: Mapped[str | None] = mapped_column(String(255))
    invoice_date: Mapped[str | None] = mapped_column(String(50))
    product_description: Mapped[str] = mapped_column(Text)
    length_km: Mapped[float | None] = mapped_column(Float)
    unit_price_excl_vat: Mapped[float | None] = mapped_column(Float)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    ucm: Mapped["UCMFeature"] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
        uselist=False,
    )
    predictions: Mapped[list["PricePrediction"]] = relationship(
        back_populates="offer",
        cascade="all, delete-orphan",
    )


class UCMFeature(Base):
    __tablename__ = "ucm_features"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("source_offers.id", ondelete="CASCADE"),
        unique=True,
        index=True,
    )
    cable_family: Mapped[str] = mapped_column(String(100), index=True)
    core_groups: Mapped[int | None] = mapped_column(Integer)
    group_type: Mapped[str | None] = mapped_column(String(50))
    cross_section_mm2: Mapped[float | None] = mapped_column(Float)
    cross_section_designation: Mapped[str | None] = mapped_column(String(100))
    conductor_flexibility_class: Mapped[int | None] = mapped_column(Integer)
    conductor_material: Mapped[str | None] = mapped_column(String(100))
    insulation_material: Mapped[str | None] = mapped_column(String(150))
    mica_tape_layers: Mapped[int | None] = mapped_column(Integer)
    individual_screen: Mapped[str | None] = mapped_column(String(200))
    filler_material: Mapped[str | None] = mapped_column(String(150))
    bedding_under_screen: Mapped[bool | None] = mapped_column(Boolean)
    overall_screen: Mapped[str | None] = mapped_column(String(200))
    sheath_material: Mapped[str | None] = mapped_column(String(150))
    armor_type: Mapped[str | None] = mapped_column(String(200))
    water_blocking: Mapped[bool | None] = mapped_column(Boolean)
    flame_retardant: Mapped[bool | None] = mapped_column(Boolean)
    fire_resistant: Mapped[bool | None] = mapped_column(Boolean)
    low_smoke: Mapped[bool | None] = mapped_column(Boolean)
    low_toxicity: Mapped[bool | None] = mapped_column(Boolean)
    halogen_free: Mapped[bool | None] = mapped_column(Boolean)
    cold_resistant: Mapped[bool | None] = mapped_column(Boolean)
    uv_resistant: Mapped[bool | None] = mapped_column(Boolean)
    oil_resistant: Mapped[bool | None] = mapped_column(Boolean)
    chemical_resistant: Mapped[bool | None] = mapped_column(Boolean)
    rated_voltage_v: Mapped[int | None] = mapped_column(Integer)
    intrinsically_safe: Mapped[bool | None] = mapped_column(Boolean)
    explosive_area_application: Mapped[bool | None] = mapped_column(Boolean)
    sheath_color: Mapped[str | None] = mapped_column(String(100))
    total_conductors: Mapped[int | None] = mapped_column(Integer)
    copper_area_mm2: Mapped[float | None] = mapped_column(Float)

    offer: Mapped[SourceOffer] = relationship(back_populates="ucm")


class ModelRun(Base):
    __tablename__ = "model_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    run_group_id: Mapped[str] = mapped_column(String(36), index=True)
    cable_family: Mapped[str] = mapped_column(String(100), index=True)
    model_type: Mapped[str] = mapped_column(String(100))
    artifact_path: Mapped[str] = mapped_column(Text)
    training_rows: Mapped[int] = mapped_column(Integer)
    test_rows: Mapped[int] = mapped_column(Integer)
    mae: Mapped[float | None] = mapped_column(Float)
    mape: Mapped[float | None] = mapped_column(Float)
    rmse: Mapped[float | None] = mapped_column(Float)
    r2: Mapped[float | None] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    trained_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    predictions: Mapped[list["PricePrediction"]] = relationship(back_populates="model_run")


class PricePrediction(Base):
    __tablename__ = "price_predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(ForeignKey("source_offers.id"), index=True)
    model_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("model_runs.id"),
        index=True,
    )
    predicted_price: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(100), index=True)
    reason: Mapped[str] = mapped_column(Text)
    model_type: Mapped[str | None] = mapped_column(String(100))
    comparable_rows: Mapped[int] = mapped_column(Integer)
    prediction_run_id: Mapped[str | None] = mapped_column(String(36), index=True)
    target_manufacturer: Mapped[str | None] = mapped_column(String(100))
    target_cable_family: Mapped[str | None] = mapped_column(String(100), index=True)
    generated_designation: Mapped[str | None] = mapped_column(Text)
    construction_description: Mapped[str | None] = mapped_column(Text)
    construction_compatible: Mapped[bool | None] = mapped_column(Boolean)
    compatibility_differences: Mapped[str | None] = mapped_column(Text)
    effective_target_voltage_v: Mapped[int | None] = mapped_column(Integer)
    voltage_equivalence_applied: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    offer: Mapped[SourceOffer] = relationship(back_populates="predictions")
    model_run: Mapped[ModelRun | None] = relationship(back_populates="predictions")
