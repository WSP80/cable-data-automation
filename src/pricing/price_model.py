from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PRICE_COLUMN = "unit_price_excl_vat"

IDENTITY_COLUMNS = {
    "source_file",
    "invoice_number",
    "invoice_date",
    "product_description",
    "length_km",
    "comment",
    PRICE_COLUMN,
}

DEFAULT_EXACT_FEATURES = [
    "cable_family",
    "group_type",
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
]

DEFAULT_NUMERIC_FEATURES = [
    "core_groups",
    "cross_section_mm2",
    "total_conductors",
    "copper_area_mm2",
]

DEFAULT_COVERAGE_EXCLUDED_FEATURES = [
    "core_groups",
    "group_type",
    "cross_section_mm2",
    "cross_section_designation",
    "total_conductors",
    "copper_area_mm2",
]


@dataclass(frozen=True)
class PriceModelConfig:
    min_training_rows: int = 100
    min_feature_value_rows: int = 30
    min_unique_cross_sections: int = 5
    allow_cross_section_extrapolation: bool = True
    test_size: float = 0.2
    random_seed: int = 42
    ridge_alpha: float = 1.0
    boosting_learning_rate: float = 0.05
    boosting_max_iter: int = 400
    boosting_max_leaf_nodes: int = 31
    boosting_min_samples_leaf: int = 20
    boosting_l2_regularization: float = 1.0
    exact_features: list[str] = field(default_factory=lambda: DEFAULT_EXACT_FEATURES.copy())
    numeric_features: list[str] = field(default_factory=lambda: DEFAULT_NUMERIC_FEATURES.copy())
    coverage_excluded_features: list[str] = field(
        default_factory=lambda: DEFAULT_COVERAGE_EXCLUDED_FEATURES.copy()
    )


@dataclass(frozen=True)
class PricePrediction:
    status: str
    predicted_price: float | None
    comparable_rows: int
    reason: str
    matched_features: list[str]
    price_min: float | None = None
    price_median: float | None = None
    price_max: float | None = None
    model_type: str | None = None

    @property
    def can_predict(self) -> bool:
        return self.status == "ok"


@dataclass(frozen=True)
class PriceModelMetrics:
    train_rows: int
    test_rows: int
    mae: float | None
    mape: float | None
    rmse: float | None
    r2: float | None


def load_price_training_frame(path: str | Path) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        sep=";",
        encoding="utf-8-sig",
        keep_default_na=False,
        na_values=[""],
    )
    frame = frame.copy()
    frame[PRICE_COLUMN] = frame[PRICE_COLUMN].map(parse_decimal)

    return frame[
        frame[PRICE_COLUMN].notna() & (frame[PRICE_COLUMN] > 0)
    ].reset_index(drop=True)


def load_ucm_price_frames(
    input_dir: str | Path,
    pattern: str = "*_UCM.csv",
) -> list[pd.DataFrame]:
    input_path = Path(input_dir)
    frames = [
        load_price_training_frame(path)
        for path in sorted(input_path.glob(pattern))
    ]

    return [
        frame
        for frame in frames
        if not frame.empty
    ]


def parse_decimal(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None

    if isinstance(value, int | float):
        return float(value)

    text = str(value).strip().replace(" ", "").replace("\u00a0", "")

    if not text:
        return None

    return float(text.replace(",", "."))


class UCMRidgeRegressor:
    """
    Ridge regression over normalized UCM features.
    """

    def __init__(self, config: PriceModelConfig) -> None:
        self.config = config
        self.numeric_features: list[str] = []
        self.categorical_features: list[str] = []
        self.numeric_means: dict[str, float] = {}
        self.numeric_stds: dict[str, float] = {}
        self.category_levels: dict[str, list[Any]] = {}
        self.coefficients: np.ndarray | None = None
        self.metrics: PriceModelMetrics | None = None

    def fit(self, frame: pd.DataFrame) -> UCMRidgeRegressor:
        train_frame, test_frame = split_train_test(
            frame,
            test_size=self.config.test_size,
            random_seed=self.config.random_seed,
        )

        self.numeric_features = [
            feature
            for feature in self.config.numeric_features
            if feature in train_frame.columns
        ]
        self.categorical_features = [
            feature
            for feature in self.config.exact_features
            if feature in train_frame.columns
        ]
        self._fit_preprocessor(train_frame)

        x_train = self.transform(train_frame)
        y_train = np.log(train_frame[PRICE_COLUMN].astype(float).to_numpy())
        self.coefficients = fit_ridge_coefficients(
            x_train,
            y_train,
            alpha=self.config.ridge_alpha,
        )

        self.metrics = self._evaluate(train_frame, test_frame)

        return self

    def predict_one(self, features: Mapping[str, Any]) -> float:
        if self.coefficients is None:
            raise ValueError("Regression model is not fitted.")

        frame = pd.DataFrame([features])
        x = self.transform(frame)
        log_prediction = float((x @ self.coefficients)[0])

        return float(np.exp(log_prediction))

    def transform(self, frame: pd.DataFrame) -> np.ndarray:
        columns = [np.ones(len(frame))]

        for feature in self.numeric_features:
            values = pd.to_numeric(frame.get(feature), errors="coerce").fillna(
                self.numeric_means[feature]
            )
            columns.append(
                ((values - self.numeric_means[feature]) / self.numeric_stds[feature]).to_numpy()
            )

        for feature in self.categorical_features:
            values = frame.get(feature, pd.Series([None] * len(frame))).astype(object)

            for level in self.category_levels[feature]:
                columns.append((values == level).astype(float).to_numpy())

        return np.column_stack(columns)

    def _fit_preprocessor(self, frame: pd.DataFrame) -> None:
        for feature in self.numeric_features:
            values = pd.to_numeric(frame[feature], errors="coerce").astype(float)
            mean = float(values.mean())
            std = float(values.std(ddof=0))
            self.numeric_means[feature] = mean
            self.numeric_stds[feature] = std if std > 0 else 1.0

        for feature in self.categorical_features:
            self.category_levels[feature] = sorted(
                frame[feature].dropna().unique().tolist(),
                key=lambda value: str(value),
            )

    def _evaluate(self, train_frame: pd.DataFrame, test_frame: pd.DataFrame) -> PriceModelMetrics:
        if test_frame.empty:
            return PriceModelMetrics(
                train_rows=len(train_frame),
                test_rows=0,
                mae=None,
                mape=None,
                rmse=None,
                r2=None,
            )

        actual = test_frame[PRICE_COLUMN].astype(float).to_numpy()
        predicted = np.array([
            self.predict_one(row.to_dict())
            for _, row in test_frame.iterrows()
        ])

        return calculate_metrics(
            actual=actual,
            predicted=predicted,
            train_rows=len(train_frame),
        )


class UCMHistGradientBoostingRegressor:
    """
    Histogram gradient boosting over normalized and one-hot encoded UCM features.
    """

    def __init__(self, config: PriceModelConfig) -> None:
        self.config = config
        self.numeric_features: list[str] = []
        self.categorical_features: list[str] = []
        self.pipeline: Pipeline | None = None
        self.metrics: PriceModelMetrics | None = None

    def fit(self, frame: pd.DataFrame) -> UCMHistGradientBoostingRegressor:
        train_frame, test_frame = split_train_test(
            frame,
            test_size=self.config.test_size,
            random_seed=self.config.random_seed,
        )
        self.numeric_features = [
            feature
            for feature in self.config.numeric_features
            if feature in train_frame.columns
        ]
        self.categorical_features = [
            feature
            for feature in self.config.exact_features
            if feature in train_frame.columns
        ]
        self.pipeline = Pipeline(
            [
                ("preprocessor", self._build_preprocessor()),
                (
                    "regressor",
                    HistGradientBoostingRegressor(
                        learning_rate=self.config.boosting_learning_rate,
                        max_iter=self.config.boosting_max_iter,
                        max_leaf_nodes=self.config.boosting_max_leaf_nodes,
                        min_samples_leaf=self.config.boosting_min_samples_leaf,
                        l2_regularization=self.config.boosting_l2_regularization,
                        random_state=self.config.random_seed,
                    ),
                ),
            ]
        )
        x_train = self._prepare_features(train_frame)
        y_train = np.log(train_frame[PRICE_COLUMN].astype(float).to_numpy())
        self.pipeline.fit(x_train, y_train)
        self.metrics = self._evaluate(train_frame, test_frame)
        return self

    def predict_one(self, features: Mapping[str, Any]) -> float:
        if self.pipeline is None:
            raise ValueError("Regression model is not fitted.")

        frame = self._prepare_features(pd.DataFrame([features]))
        log_prediction = float(self.pipeline.predict(frame)[0])
        return float(np.exp(log_prediction))

    def _prepare_features(self, frame: pd.DataFrame) -> pd.DataFrame:
        columns = self.numeric_features + self.categorical_features
        prepared = frame.reindex(columns=columns).copy()

        for feature in self.numeric_features:
            prepared[feature] = pd.to_numeric(prepared[feature], errors="coerce")

        for feature in self.categorical_features:
            prepared[feature] = prepared[feature].fillna("__missing__").astype(str)

        return prepared

    def _build_preprocessor(self) -> ColumnTransformer:
        numeric_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]
        )
        categorical_pipeline = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="most_frequent")),
                (
                    "one_hot",
                    OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                ),
            ]
        )
        return ColumnTransformer(
            [
                ("numeric", numeric_pipeline, self.numeric_features),
                ("categorical", categorical_pipeline, self.categorical_features),
            ],
            remainder="drop",
        )

    def _evaluate(
        self,
        train_frame: pd.DataFrame,
        test_frame: pd.DataFrame,
    ) -> PriceModelMetrics:
        if test_frame.empty:
            return PriceModelMetrics(
                train_rows=len(train_frame),
                test_rows=0,
                mae=None,
                mape=None,
                rmse=None,
                r2=None,
            )

        actual = test_frame[PRICE_COLUMN].astype(float).to_numpy()
        prepared = self._prepare_features(test_frame)
        predicted = np.exp(self.pipeline.predict(prepared))
        return calculate_metrics(
            actual=actual,
            predicted=predicted,
            train_rows=len(train_frame),
        )


def split_train_test(
    frame: pd.DataFrame,
    test_size: float,
    random_seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if len(frame) < 2 or test_size <= 0:
        return frame.reset_index(drop=True), frame.iloc[0:0].copy()

    rng = np.random.default_rng(random_seed)
    indices = np.arange(len(frame))
    rng.shuffle(indices)
    test_count = max(1, int(round(len(frame) * test_size)))
    test_count = min(test_count, len(frame) - 1)
    test_indices = indices[:test_count]
    train_indices = indices[test_count:]

    return (
        frame.iloc[train_indices].reset_index(drop=True),
        frame.iloc[test_indices].reset_index(drop=True),
    )


def fit_ridge_coefficients(x: np.ndarray, y: np.ndarray, alpha: float) -> np.ndarray:
    penalty = np.eye(x.shape[1]) * alpha
    penalty[0, 0] = 0

    return np.linalg.pinv(x.T @ x + penalty) @ x.T @ y


def calculate_metrics(
    actual: np.ndarray,
    predicted: np.ndarray,
    train_rows: int,
) -> PriceModelMetrics:
    residuals = predicted - actual
    mae = float(np.mean(np.abs(residuals)))
    mape = float(np.mean(np.abs(residuals / actual)) * 100)
    rmse = float(np.sqrt(np.mean(residuals ** 2)))
    total_variance = float(np.sum((actual - np.mean(actual)) ** 2))
    r2 = None

    if total_variance > 0:
        r2 = float(1 - (np.sum(residuals ** 2) / total_variance))

    return PriceModelMetrics(
        train_rows=train_rows,
        test_rows=len(actual),
        mae=mae,
        mape=mape,
        rmse=rmse,
        r2=r2,
    )


class ManufacturerPriceModel:
    """
    Conservative per-manufacturer price estimator.

    The model predicts only from rows of one mark family and only when enough
    comparable constructions exist in the historical data.
    """

    def __init__(self, manufacturer: str, config: PriceModelConfig | None = None) -> None:
        self.manufacturer = manufacturer
        self.config = config or PriceModelConfig()
        self.training_frame = pd.DataFrame()
        self.supported_values: dict[str, set[Any]] = {}
        self.regression_model: UCMHistGradientBoostingRegressor | None = None

    def fit(self, frame: pd.DataFrame) -> ManufacturerPriceModel:
        cleaned = frame.copy()
        cleaned[PRICE_COLUMN] = cleaned[PRICE_COLUMN].map(parse_decimal)
        cleaned = cleaned[
            cleaned[PRICE_COLUMN].notna() & (cleaned[PRICE_COLUMN] > 0)
        ].reset_index(drop=True)

        self.training_frame = cleaned
        self.supported_values = {
            feature: set(cleaned[feature].dropna().unique())
            for feature in self.config.exact_features
            if feature in cleaned.columns
        }
        if len(cleaned) >= self.config.min_training_rows:
            self.regression_model = UCMHistGradientBoostingRegressor(self.config).fit(cleaned)
        else:
            self.regression_model = None

        return self

    def predict(self, features: Mapping[str, Any]) -> PricePrediction:
        if len(self.training_frame) < self.config.min_training_rows:
            return PricePrediction(
                status="insufficient_model_data",
                predicted_price=None,
                comparable_rows=len(self.training_frame),
                reason=(
                    f"Need at least {self.config.min_training_rows} priced rows "
                    f"for {self.manufacturer}."
                ),
                matched_features=[],
            )

        coverage_gaps = self._feature_value_coverage_gaps(features)
        cross_section_gap = self._cross_section_coverage_gap(features)

        if cross_section_gap:
            coverage_gaps.append(cross_section_gap)

        if coverage_gaps:
            return PricePrediction(
                status="insufficient_feature_value_data",
                predicted_price=None,
                comparable_rows=0,
                reason="Insufficient feature value data: " + ", ".join(coverage_gaps),
                matched_features=[],
            )

        if self.regression_model is None:
            return PricePrediction(
                status="regression_model_not_trained",
                predicted_price=None,
                comparable_rows=len(self.training_frame),
                reason="Not enough coverage-ready UCM rows to train regression model.",
                matched_features=self._present_coverage_features(features),
            )

        predicted_price = self.regression_model.predict_one(features)
        prices = self.training_frame[PRICE_COLUMN].astype(float)

        return PricePrediction(
            status="ok",
            predicted_price=predicted_price,
            comparable_rows=len(self.training_frame),
            reason=(
                "Prediction is produced by per-family histogram gradient boosting over UCM "
                "features "
                "after feature coverage checks."
            ),
            matched_features=self._present_coverage_features(features),
            price_min=float(prices.min()),
            price_median=float(prices.median()),
            price_max=float(prices.max()),
            model_type="ucm_hist_gradient_boosting",
        )

    def support_summary(self) -> dict[str, Any]:
        return {
            "manufacturer": self.manufacturer,
            "priced_rows": len(self.training_frame),
            "can_train": len(self.training_frame) >= self.config.min_training_rows,
            "min_training_rows": self.config.min_training_rows,
            "min_feature_value_rows": self.config.min_feature_value_rows,
            "regression_trained": self.regression_model is not None,
        }

    def metrics(self) -> PriceModelMetrics | None:
        if self.regression_model is None:
            return None

        return self.regression_model.metrics

    def feature_value_counts_for(self, features: Mapping[str, Any]) -> dict[str, int]:
        counts = {}

        for feature in self._present_coverage_features(features):
            counts[feature] = int((self.training_frame[feature] == features[feature]).sum())

        return counts

    def coverage_ready_rows(self) -> pd.Series:
        if len(self.training_frame) < self.config.min_training_rows:
            return pd.Series([False] * len(self.training_frame), index=self.training_frame.index)

        coverage_features = [
            feature
            for feature in self.config.exact_features + self.config.numeric_features
            if feature not in set(self.config.coverage_excluded_features)
            and feature in self.training_frame.columns
        ]

        if not coverage_features:
            return pd.Series([True] * len(self.training_frame), index=self.training_frame.index)

        ready = pd.Series([True] * len(self.training_frame), index=self.training_frame.index)

        for feature in coverage_features:
            counts = self.training_frame.groupby(feature, dropna=False)[PRICE_COLUMN].transform("size")
            ready = ready & (counts >= self.config.min_feature_value_rows)

        return ready

    def comparable_group_sizes(self) -> pd.Series:
        group_features = [
            feature
            for feature in self.config.exact_features + self.config.numeric_features
            if feature in self.training_frame.columns
        ]

        if not group_features:
            return pd.Series([len(self.training_frame)] * len(self.training_frame))

        return self.training_frame.groupby(
            group_features,
            dropna=False,
        )[PRICE_COLUMN].transform("size")

    def _unknown_feature_values(self, features: Mapping[str, Any]) -> list[str]:
        unknown = []

        for feature in self._present_exact_features(features):
            value = features[feature]
            supported = self.supported_values.get(feature, set())

            if value not in supported:
                unknown.append(f"{feature}={value}")

        return unknown

    def _feature_value_coverage_gaps(self, features: Mapping[str, Any]) -> list[str]:
        gaps = []

        for feature, count in self.feature_value_counts_for(features).items():
            if count < self.config.min_feature_value_rows:
                gaps.append(
                    f"{feature}={features[feature]} ({count} < {self.config.min_feature_value_rows})"
                )

        return gaps

    def _cross_section_coverage_gap(
        self,
        features: Mapping[str, Any],
    ) -> str | None:
        feature = "cross_section_mm2"

        if feature not in self.training_frame.columns:
            return f"{feature} is missing from training data"

        training_values = pd.to_numeric(
            self.training_frame[feature],
            errors="coerce",
        ).dropna()
        unique_count = int(training_values.nunique())

        if unique_count < self.config.min_unique_cross_sections:
            return (
                f"{feature} has only {unique_count} unique values "
                f"(< {self.config.min_unique_cross_sections})"
            )

        requested = parse_decimal(features.get(feature))

        if (
            requested is not None
            and not self.config.allow_cross_section_extrapolation
            and not training_values.empty
            and (requested < training_values.min() or requested > training_values.max())
        ):
            return (
                f"{feature}={requested} is outside training range "
                f"{training_values.min()}..{training_values.max()}"
            )

        return None

    def _present_coverage_features(self, features: Mapping[str, Any]) -> list[str]:
        excluded = set(self.config.coverage_excluded_features)

        return [
            feature
            for feature in self.config.exact_features + self.config.numeric_features
            if feature not in excluded
            and feature in self.training_frame.columns
            and feature in features
            and not pd.isna(features[feature])
        ]

    def _present_exact_features(self, features: Mapping[str, Any]) -> list[str]:
        return [
            feature
            for feature in self.config.exact_features
            if feature in self.training_frame.columns and feature in features and not pd.isna(features[feature])
        ]

    def _present_numeric_features(self, features: Mapping[str, Any]) -> list[str]:
        return [
            feature
            for feature in self.config.numeric_features
            if feature in self.training_frame.columns and feature in features and not pd.isna(features[feature])
        ]

    def _present_model_features(self, features: Mapping[str, Any]) -> list[str]:
        return self._present_exact_features(features) + self._present_numeric_features(features)


class UCMPriceModelCatalog:
    """
    Collection of price models trained from normalized UCM feature tables.
    """

    def __init__(self, models: Mapping[str, ManufacturerPriceModel]) -> None:
        self.models = dict(models)

    def predict(self, features: Mapping[str, Any]) -> PricePrediction:
        cable_family = features.get("cable_family")

        if not cable_family:
            return PricePrediction(
                status="missing_cable_family",
                predicted_price=None,
                comparable_rows=0,
                reason="UCM features must include cable_family.",
                matched_features=[],
            )

        model = self.models.get(str(cable_family))

        if model is None:
            return PricePrediction(
                status="insufficient_model_data",
                predicted_price=None,
                comparable_rows=0,
                reason=f"No price model is trained for cable_family={cable_family}.",
                matched_features=[],
            )

        return model.predict(features)

    def readiness_frame(self) -> pd.DataFrame:
        rows = []

        for cable_family, model in sorted(self.models.items()):
            priced_rows = len(model.training_frame)
            coverage_ready_rows = model.coverage_ready_rows()
            coverage_ready_count = int(coverage_ready_rows.sum())
            metrics = model.metrics()

            rows.append(
                {
                    **model.support_summary(),
                    "cable_family": cable_family,
                    "feature_coverage_ready_rows": coverage_ready_count,
                    "feature_coverage_ready_share": (
                        round(coverage_ready_count / priced_rows, 4)
                        if priced_rows
                        else 0
                    ),
                    "regression_train_rows": metrics.train_rows if metrics else 0,
                    "regression_test_rows": metrics.test_rows if metrics else 0,
                    "mae": round(metrics.mae, 2) if metrics and metrics.mae is not None else None,
                    "mape": round(metrics.mape, 2) if metrics and metrics.mape is not None else None,
                    "rmse": round(metrics.rmse, 2) if metrics and metrics.rmse is not None else None,
                    "r2": round(metrics.r2, 4) if metrics and metrics.r2 is not None else None,
                }
            )

        return pd.DataFrame(rows)

    def feature_coverage_frame(self) -> pd.DataFrame:
        rows = []

        for cable_family, model in sorted(self.models.items()):
            model_trained = model.regression_model is not None
            excluded = set(model.config.coverage_excluded_features)
            model_features = model.config.numeric_features + model.config.exact_features

            for feature in model_features:
                if feature not in model.training_frame.columns:
                    continue

                if feature in excluded:
                    numeric_values = pd.to_numeric(
                        model.training_frame[feature],
                        errors="coerce",
                    ).dropna()
                    numeric_value_is_valid = model_trained

                    if feature == "cross_section_mm2":
                        numeric_value_is_valid = (
                            numeric_value_is_valid
                            and numeric_values.nunique()
                            >= model.config.min_unique_cross_sections
                        )

                    rows.append(
                        {
                            "cable_family": cable_family,
                            "feature": feature,
                            "value": "ALL_VALUES",
                            "rows": len(model.training_frame),
                            "min_required": "not_checked",
                            "used_in_model": model_trained,
                            "used_in_coverage_gate": False,
                            "valid_for_prediction": numeric_value_is_valid,
                            "unique_values": int(numeric_values.nunique()),
                            "minimum": (
                                float(numeric_values.min())
                                if not numeric_values.empty
                                else None
                            ),
                            "maximum": (
                                float(numeric_values.max())
                                if not numeric_values.empty
                                else None
                            ),
                            "extrapolation_allowed": (
                                model.config.allow_cross_section_extrapolation
                                if feature == "cross_section_mm2"
                                else None
                            ),
                        }
                    )
                    continue

                counts = model.training_frame[feature].value_counts(dropna=False)

                for value, count in counts.items():
                    display_value = "__missing__" if pd.isna(value) else value
                    rows.append(
                        {
                            "cable_family": cable_family,
                            "feature": feature,
                            "value": display_value,
                            "rows": int(count),
                            "min_required": model.config.min_feature_value_rows,
                            "used_in_model": model_trained,
                            "used_in_coverage_gate": True,
                            "valid_for_prediction": (
                                model_trained
                                and count >= model.config.min_feature_value_rows
                            ),
                            "unique_values": None,
                            "minimum": None,
                            "maximum": None,
                            "extrapolation_allowed": None,
                        }
                    )

        return pd.DataFrame(rows)


def fit_price_models_by_family(
    frames: Iterable[pd.DataFrame],
    config: PriceModelConfig | None = None,
) -> dict[str, ManufacturerPriceModel]:
    combined = pd.concat(list(frames), ignore_index=True)
    models = {}

    for cable_family, group in combined.groupby("cable_family"):
        model = ManufacturerPriceModel(str(cable_family), config=config)
        models[str(cable_family)] = model.fit(group)

    return models


def fit_price_models_from_ucm_dir(
    input_dir: str | Path,
    config: PriceModelConfig | None = None,
    pattern: str = "*_UCM.csv",
) -> UCMPriceModelCatalog:
    frames = load_ucm_price_frames(input_dir, pattern=pattern)

    if not frames:
        return UCMPriceModelCatalog({})

    return UCMPriceModelCatalog(
        fit_price_models_by_family(frames, config=config)
    )


def save_price_model_catalog(
    catalog: UCMPriceModelCatalog,
    path: str | Path,
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(catalog, output_path)
    return output_path


def load_price_model_catalog(path: str | Path) -> UCMPriceModelCatalog:
    model_path = Path(path)

    if not model_path.exists():
        raise FileNotFoundError(
            f"Trained price model catalog not found: {model_path}. "
            "Run scripts/audit_price_models.py first."
        )

    catalog = joblib.load(model_path)

    if not isinstance(catalog, UCMPriceModelCatalog):
        raise TypeError(f"Unsupported model artifact: {model_path}")

    return catalog
