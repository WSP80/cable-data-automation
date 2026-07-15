from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import sys
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import (
    ExtraTreesRegressor,
    HistGradientBoostingRegressor,
    RandomForestRegressor,
)
from sklearn.impute import SimpleImputer
from sklearn.linear_model import ElasticNet, Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.pricing.price_model import (
    PRICE_COLUMN,
    PriceModelConfig,
    calculate_metrics,
    load_price_training_frame,
    split_train_test,
)


INPUT_PATH = Path("data/processed/ATOMKIP-KU_UCM.csv")
OUTPUT_PATH = Path("reports/tables/price_model_comparison.csv")


def available_features(
    frame: pd.DataFrame,
    config: PriceModelConfig,
) -> tuple[list[str], list[str]]:
    numeric = [
        feature for feature in config.numeric_features if feature in frame.columns
    ]
    categorical = [
        feature for feature in config.exact_features if feature in frame.columns
    ]
    return numeric, categorical


def prepare_features(
    frame: pd.DataFrame,
    numeric: list[str],
    categorical: list[str],
) -> pd.DataFrame:
    prepared = frame[numeric + categorical].copy()

    for feature in numeric:
        prepared[feature] = pd.to_numeric(prepared[feature], errors="coerce")

    for feature in categorical:
        prepared[feature] = prepared[feature].fillna("__missing__").astype(str)

    return prepared


def build_preprocessor(
    numeric: list[str],
    categorical: list[str],
) -> ColumnTransformer:
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
                OneHotEncoder(
                    handle_unknown="ignore",
                    sparse_output=False,
                ),
            ),
        ]
    )

    return ColumnTransformer(
        [
            ("numeric", numeric_pipeline, numeric),
            ("categorical", categorical_pipeline, categorical),
        ],
        remainder="drop",
    )


def candidate_models(random_seed: int) -> dict[str, object]:
    return {
        "ridge": Ridge(alpha=1.0),
        "elastic_net": ElasticNet(
            alpha=0.001,
            l1_ratio=0.2,
            max_iter=20_000,
            random_state=random_seed,
        ),
        "random_forest": RandomForestRegressor(
            n_estimators=400,
            min_samples_leaf=2,
            max_features=0.8,
            n_jobs=-1,
            random_state=random_seed,
        ),
        "extra_trees": ExtraTreesRegressor(
            n_estimators=400,
            min_samples_leaf=2,
            max_features=1.0,
            n_jobs=-1,
            random_state=random_seed,
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            learning_rate=0.05,
            max_iter=400,
            max_leaf_nodes=31,
            min_samples_leaf=20,
            l2_regularization=1.0,
            random_state=random_seed,
        ),
    }


def compare_models(
    frame: pd.DataFrame,
    config: PriceModelConfig | None = None,
) -> pd.DataFrame:
    config = config or PriceModelConfig()
    train_frame, test_frame = split_train_test(
        frame,
        test_size=config.test_size,
        random_seed=config.random_seed,
    )
    numeric, categorical = available_features(train_frame, config)
    x_train = prepare_features(train_frame, numeric, categorical)
    x_test = prepare_features(test_frame, numeric, categorical)
    y_train = np.log(train_frame[PRICE_COLUMN].astype(float).to_numpy())
    actual = test_frame[PRICE_COLUMN].astype(float).to_numpy()
    rows = []

    for model_name, estimator in candidate_models(config.random_seed).items():
        pipeline = Pipeline(
            [
                ("preprocessor", build_preprocessor(numeric, categorical)),
                ("regressor", estimator),
            ]
        )
        started = perf_counter()
        pipeline.fit(x_train, y_train)
        predicted = np.exp(pipeline.predict(x_test))
        elapsed = perf_counter() - started
        metrics = calculate_metrics(
            actual=actual,
            predicted=predicted,
            train_rows=len(train_frame),
        )
        rows.append(
            {
                "model": model_name,
                **asdict(metrics),
                "fit_predict_seconds": round(elapsed, 3),
                "numeric_features": len(numeric),
                "categorical_features": len(categorical),
            }
        )

    result = pd.DataFrame(rows).sort_values(
        ["mape", "mae"],
        ascending=True,
    )
    result.insert(0, "rank_by_mape", range(1, len(result) + 1))
    return result.reset_index(drop=True)


def main() -> None:
    frame = load_price_training_frame(INPUT_PATH)
    report = compare_models(frame)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report.to_csv(OUTPUT_PATH, sep=";", index=False, encoding="utf-8-sig")

    print(report.to_string(index=False))
    print(f"output_file: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
