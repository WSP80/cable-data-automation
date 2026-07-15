# Cable Price Intelligence

Cable Price Intelligence is a portfolio project for parsing manufacturer cable
designations, converting them into a Universal Cable Model (UCM), training
price-prediction models, and presenting prediction results in Power BI and a
Streamlit interface.

The project focuses on a realistic industrial data workflow:

- Power Query exports supplier data into normalized CSV files.
- Python parsers convert manufacturer designations into UCM features.
- Python generators convert UCM features back into manufacturer designations.
- A separate price model is trained per cable family.
- PostgreSQL stores current UCM data, model runs, and prediction history.
- Power BI reads curated SQL views.
- Streamlit provides a lightweight upload-and-predict interface.

## Supported Cable Families

The current implementation supports these cable families:

- `ATOMKIP-KU`
- `CONFLEX`
- `MK`
- `TOFLEX-KU`

Parsers and generators support both Cyrillic marks and transliterated Latin
marks where the manufacturer grammar allows it. Generated prediction marks are
written in transliterated form for easier cross-system handling.

## Architecture

```mermaid
flowchart LR
    A["Raw supplier files"] --> B["Power Query"]
    B --> C["Processed CSV files"]
    C --> D["Parser"]
    D --> E["Universal Cable Model"]
    E --> F["PostgreSQL"]
    F --> G["HistGradientBoosting models"]
    G --> H["Price predictions"]
    F --> I["Power BI SQL views"]
    H --> I
    I --> J["Power BI report"]
    G --> K["Streamlit app"]
```

## Repository Structure

```text
app/                 Streamlit prediction UI
config/              Manufacturer configuration and feature dictionaries
docs/                Runbooks for execution, Power BI, and GitHub sync
power_bi/            Power BI report, theme, and DAX assets
power_query/         Excel Power Query / VBA export workbook
scripts/             Pipeline commands for export, training, and prediction
sql/                 PostgreSQL views for Power BI
src/                 Parsers, generators, UCM models, database, and pricing code
tests/               Automated tests
data/demo/raw/       Public anonymized demo input files
```

Generated and private folders are intentionally excluded from Git:

```text
data/raw/
data/archiv/
data/processed/
data/prediction_input/
data/prediction_output/
data/database/
artifacts/models/
reports/tables/
```

## Data Privacy

Commercial source data must not be committed. The local folders `data/raw/` and
`data/archiv/` are ignored by Git and should remain private. Only anonymized demo
files from `data/demo/raw/` are intended for GitHub.

Before publishing, always review staged files with:

```powershell
git diff --cached --name-only
```

## Installation

Install dependencies from the project root:

```powershell
uv sync
```

Start PostgreSQL:

```powershell
docker compose up -d
```

Set the database connection in the current PowerShell terminal:

```powershell
$env:DATABASE_URL = "postgresql+psycopg://cable:cable@localhost:5432/cable_intelligence"
```

If numerical libraries fail with an OpenBLAS memory allocation error, limit
thread usage before running Python scripts:

```powershell
$env:OPENBLAS_NUM_THREADS = "1"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:NUMEXPR_NUM_THREADS = "1"
```

## Full Pipeline From Processed CSV Files

Use this sequence after Power Query has exported cleaned files into
`data/processed/`:

```powershell
cd D:\Weiterbildung\6.PortfolioProject

docker compose up -d

$env:DATABASE_URL = "postgresql+psycopg://cable:cable@localhost:5432/cable_intelligence"

.venv\Scripts\python.exe scripts\export_ucm.py
.venv\Scripts\python.exe scripts\init_database.py
.venv\Scripts\python.exe scripts\import_ucm_to_database.py
.venv\Scripts\python.exe scripts\train_models_from_database.py
.venv\Scripts\python.exe scripts\predict_prices_from_database.py
.venv\Scripts\python.exe scripts\create_power_bi_views.py
```

Expected processed inputs:

```text
data/processed/ATOMKIP-KU.csv
data/processed/CONFLEX.csv
data/processed/MK.csv
data/processed/TOFLEX.csv
```

Missing manufacturer files are skipped, so the pipeline can run on partial
datasets.

## Prediction Input

Files without prices go into:

```text
data/prediction_input/
```

The file name must contain a supported source manufacturer code, for example:

```text
ATOMKIP-KU.csv
CONFLEX.csv
MK.csv
TOFLEX.csv
```

Prediction output is written to:

```text
data/prediction_output/
```

The output includes generated manufacturer marks, predicted prices, prediction
status, rejection reasons, construction descriptions, and compatibility notes.

## Streamlit Interface

Run the Streamlit app after the model artifact has been trained:

```powershell
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

The app allows a user to upload a CSV or TXT file with cable designations, infer
the source manufacturer from the file name, run predictions, and download the
priced CSV.

## Power BI

Power BI connects to PostgreSQL:

```text
Server:   localhost:5432
Database: cable_intelligence
User:     cable
Password: cable
```

Import these views:

```text
bi_offer_features
bi_model_runs
bi_predictions
```

The current views expose the latest training load, active models, and latest
prediction run. Historical views are also available for long-term analysis:

```text
bi_offer_features_history
bi_model_runs_history
bi_prediction_history
```

The report setup is documented in `docs/power_bi_report.md`.

## Model Logic

The main model is `HistGradientBoostingRegressor` from scikit-learn. A separate
model is trained for each cable family. Prediction validity is guarded by data
coverage rules:

- at least 100 priced rows per cable family;
- at least 30 rows for each checked categorical feature value;
- `copper_area_mm2` and `total_conductors` are always included;
- cross-section extrapolation is allowed;
- unsupported or underrepresented constructions are retained with a rejection
  reason instead of a predicted price.

## Tests

Run the automated test suite:

```powershell
.venv\Scripts\python.exe -m pytest
```

## GitHub Publishing Checklist

1. Keep `data/raw/` unchanged and private.
2. Keep `data/archiv/` private and ignored.
3. Commit only anonymized demo files from `data/demo/raw/`.
4. Do not commit generated model artifacts, processed commercial CSV files,
   prediction batches, local databases, or generated report tables.
5. Use `docs/github_sync.md` for the final staging and commit workflow.
