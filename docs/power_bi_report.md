# Power BI Report

This document describes the current Power BI report for the Cable Price
Intelligence project. The report is connected to PostgreSQL views created by the
project scripts.

## Prerequisites

- Docker Desktop is running.
- The PostgreSQL service is healthy.
- The project database has been initialized and populated.
- The Power BI presentation views have been created.
- Power BI Desktop is installed.

Run the data preparation commands from the project root:

```powershell
docker compose up -d
$env:DATABASE_URL="postgresql+psycopg://cable:cable@localhost:5432/cable_intelligence"
.venv\Scripts\python.exe scripts\init_database.py
.venv\Scripts\python.exe scripts\import_ucm_to_database.py
.venv\Scripts\python.exe scripts\train_models_from_database.py
.venv\Scripts\python.exe scripts\predict_prices_from_database.py
.venv\Scripts\python.exe scripts\create_power_bi_views.py
```

## PostgreSQL Connection

In Power BI Desktop:

1. Select **Get data**.
2. Select **PostgreSQL database**.
3. Enter `localhost:5432` as the server.
4. Enter `cable_intelligence` as the database.
5. Select **Import** mode.
6. Use database authentication.
7. Enter `cable` as the user and `cable` as the password.
8. Import these views:
   - `public.bi_offer_features`
   - `public.bi_model_runs`
   - `public.bi_predictions`

## Semantic Model

Create these relationships:

```text
bi_offer_features[offer_id] 1 --- * bi_predictions[offer_id]
bi_model_runs[model_run_id] 1 --- * bi_predictions[model_run_id]
Date[Date] 1 --- * bi_offer_features[invoice_date]
```

Use single-direction filtering from the one-side to the many-side.

Create the calculated Date table from `power_bi/date_table.dax`. Mark it as the
date table and use the `Date` column.

Create the measures from `power_bi/measures.dax`. A dedicated empty table named
`_Measures` can be used as the home table for all measures.

Import the report theme:

```text
View -> Themes -> Browse for themes -> power_bi/theme.json
```

## Report Separation

The report separates historical data from prediction output:

- **General Data** pages use `bi_offer_features` and `bi_model_runs`.
- **Export History** pages use all rows from `bi_predictions`.
- **Current Export** pages use `bi_predictions` filtered to the latest
  `prediction_run_id`.

Use `bi_offer_features[dataset_role] = "training"` when a visual should show
historical training data only.

Use `bi_predictions[is_current_prediction_run] = True` when a visual should show
only the most recent prediction batch from `data/prediction_input`.

Do not mix prediction KPI cards into pages filtered by
`bi_offer_features[dataset_role] = "training"`. Keep historical training pages
and prediction/export pages separate.

## Calculated Columns

Create a readable prediction status label in `bi_predictions`:

```DAX
Prediction Status Label =
SWITCH(
    bi_predictions[prediction_status],
    "ok", "Successful",
    "insufficient_feature_value_data", "Unsupported Features",
    "insufficient_model_data", "Insufficient Model Data",
    "unsupported_cable_family", "Insufficient Model Data",
    "incompatible_target_construction", "Incompatible Construction",
    bi_predictions[prediction_status]
)
```

Create a separate sort column based on the raw status value:

```DAX
Prediction Status Sort =
SWITCH(
    bi_predictions[prediction_status],
    "ok", 1,
    "insufficient_feature_value_data", 2,
    "insufficient_model_data", 3,
    "unsupported_cable_family", 3,
    "incompatible_target_construction", 4,
    99
)
```

Sort `Prediction Status Label` by `Prediction Status Sort`.

## Page 1: Executive Overview

Group: General Data.

Purpose: show the portfolio-level health of the historical dataset and active
models.

KPI cards:

- `Total Offers`
- `Training Offers`
- `Active Models`
- `Average Active Model MAPE`
- `Average Active Model R2`

Visuals:

- clustered column chart: `Total Offers` by `bi_offer_features[cable_family]`
- table: active model quality with cable family, model type, training rows, test
  rows, MAPE, and R2

Recommended filters:

- `bi_model_runs[is_active] = True` for the active model table
- `bi_offer_features[dataset_role] = "training"` for historical-only visuals

Do not use prediction measures on this page.

## Page 2: Price Analysis

Group: General Data.

Purpose: compare price levels across cable families without overusing noisy
offer-level charts.

KPI cards:

- `Average Actual Price`
- `Median Actual Price`
- `Average Price per Copper mm2`

Visuals:

- clustered column chart: average normalized price by cable family
- clustered column chart: average unit price by cable family

Sorting:

- sort cable family labels alphabetically

## Page 3: Export History

Group: Export History.

Purpose: show the overall statistics of all prediction exports.

KPI cards:

- `Export Runs`
- `Export History Source Offers`
- `Export History Predictions`
- `Export History Successful Predictions`
- `Export History Prediction Success Rate`
- `Export History Compatible Predictions`

Visuals:

- clustered column chart: export history predictions by status
- stacked column chart: export history outcomes by target cable family
- table: prediction run id, predicted timestamp, source file, source offer count,
  predictions, successful predictions, and success rate

Recommended filters:

- no `bi_predictions[is_current_prediction_run]` filter
- no `bi_offer_features[dataset_role] = "training"` filter

## Page 4: Current Export

Group: Current Export.

Purpose: show the dataset indicators and prediction result for the latest
prediction batch from `data/prediction_input`.

KPI cards:

- `Current Run Source Offers`
- `Current Run Predictions`
- `Current Run Successful Predictions`
- `Current Run Prediction Success Rate`
- `Current Run Compatible Predictions`
- `Current Run Average Predicted Price`

Visuals:

- clustered column chart: current export source offers by source cable family
- clustered column chart: current export source offers by group type
- clustered column chart: current export predictions by status
- stacked column chart: current export outcomes by target cable family
- table: source designation, target cable family, generated designation,
  predicted price, status, and reason

Recommended colors:

- Successful: green
- Unsupported Features: light red
- Insufficient Model Data: pale red
- Incompatible Construction: red

Sorting:

- sort prediction statuses by `Prediction Status Sort`
- sort target cable family alphabetically

Recommended filters:

- `bi_predictions[is_current_prediction_run] = True`

Use `Current Run Source Offers` as the value for source dataset charts because
one source offer can produce several target prediction rows.

## Page 5: Data Coverage

Group: General Data.

Purpose: show whether each cable family has enough data for reliable model
training.

KPI cards:

- `Training Offers`
- `Active Models`
- `Average Active Model MAPE`
- `Average Active Model R2`

Visuals:

- clustered column chart: training rows by cable family
- clustered column chart: model MAPE by cable family
- table: cable family, model type, training rows, test rows, MAPE, R2, RMSE, and
  trained timestamp

Recommended reference line:

- add a constant line at `100` on the training rows chart
- label it `Minimum: 100`

Recommended filters:

- `bi_model_runs[is_active] = True`

## Refresh

The PostgreSQL container must be running before a refresh:

```powershell
docker compose up -d
```

In Power BI Desktop, select **Home -> Refresh**. New SQL rows and model runs are
then loaded into the semantic model.
