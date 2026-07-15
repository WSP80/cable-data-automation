# Run Commands

This runbook lists the terminal commands for running the project after Power
Query has already exported cleaned CSV files into `data/processed`.

## Full Pipeline With PostgreSQL

Run these commands from PowerShell in the project root:

```powershell
cd D:\Weiterbildung\6.PortfolioProject

$env:DATABASE_URL='postgresql+psycopg://cable:cable@localhost:5432/cable_intelligence'
$env:OPENBLAS_NUM_THREADS="1"
$env:OMP_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"
$env:NUMEXPR_NUM_THREADS="1"

docker compose up -d
docker compose ps

.venv\Scripts\python.exe scripts\export_ucm.py

.venv\Scripts\python.exe scripts\audit_atomkip_processed.py
.venv\Scripts\python.exe scripts\audit_conflex_processed.py
.venv\Scripts\python.exe scripts\audit_mk_processed.py
.venv\Scripts\python.exe scripts\audit_toflex_processed.py

.venv\Scripts\python.exe scripts\init_database.py
.venv\Scripts\python.exe scripts\import_ucm_to_database.py

.venv\Scripts\python.exe scripts\train_models_from_database.py

.venv\Scripts\python.exe scripts\export_construction_descriptions.py

.venv\Scripts\python.exe scripts\predict_prices_from_database.py

.venv\Scripts\python.exe scripts\create_power_bi_views.py

.venv\Scripts\python.exe -m pytest -q
```

## Docker Fallback

If `docker` is not available in `PATH`, use the Docker Desktop CLI path:

```powershell
& 'C:\Users\wilms\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose up -d
& 'C:\Users\wilms\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe' compose ps
```

## Power BI Refresh

After the pipeline finishes, open the Power BI report and click:

```text
Aktualisieren
```

Power BI reads these PostgreSQL views:

- `bi_offer_features`
- `bi_model_runs`
- `bi_predictions`

## Streamlit Interface

Run Streamlit in a separate terminal:

```powershell
cd D:\Weiterbildung\6.PortfolioProject
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

## OpenBLAS Memory Error

If Python fails with an OpenBLAS memory allocation error, set these variables in
the same terminal before running Python commands:

```powershell
$env:OPENBLAS_NUM_THREADS="1"
$env:OMP_NUM_THREADS="1"
$env:MKL_NUM_THREADS="1"
$env:NUMEXPR_NUM_THREADS="1"
```

## Expected Input Files

Power Query should create cleaned manufacturer CSV files in:

```text
data/processed
```

Expected file names:

```text
ATOMKIP-KU.csv
CONFLEX.csv
MK.csv
TOFLEX.csv
```

Prediction input files without prices go into:

```text
data/prediction_input
```

Their file names must match configured manufacturers, for example:

```text
ATOMKIP-KU.csv
CONFLEX.csv
MK.csv
TOFLEX.csv
```
