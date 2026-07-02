# Cable Price Intelligence

## Project Overview

**Cable Price Intelligence** is an end-to-end data analytics project designed to automate the collection, transformation, normalization, analysis, and forecasting of industrial cable prices from multiple manufacturers.

The project integrates **Power Query**, **VBA**, **Python**, and **Power BI** into a unified analytics pipeline that converts heterogeneous invoice data into structured datasets suitable for feature engineering, machine learning, and business intelligence.

The primary goals are:

- automate invoice data extraction from multiple file formats;
- standardize product information across different manufacturers;
- identify technically comparable cable constructions;
- analyze historical pricing behaviour;
- compare manufacturer price levels;
- forecast future cable prices using machine learning models.

---

# Project Objectives

- Build a fully automated ETL pipeline.
- Import invoice data from Excel, PDF and CSV files.
- Standardize invoice datasets.
- Normalize cable constructions into comparable technical features.
- Generate feature datasets for machine learning.
- Perform exploratory data analysis.
- Compare prices across manufacturers.
- Develop predictive pricing models.
- Create interactive Power BI dashboards.

---

# Technology Stack

### ETL

- Power Query
- VBA
- Excel

### Data Processing

- Python
- Pandas
- NumPy

### Machine Learning

- Scikit-learn

### Visualization

- Power BI
- Matplotlib

### Version Control

- Git
- GitHub
- Visual Studio Code

---

# Project Architecture

```text
                Excel
                  │
                PDF
                  │
                CSV
                  │
                  ▼
        Power Query ETL
                  │
                  ▼
     Standardized Invoice Data
                  │
                  ▼
        Automated CSV Export
                  │
                  ▼
      Python Feature Engineering
                  │
                  ▼
 Cable Construction Normalization
                  │
                  ▼
     Exploratory Data Analysis
                  │
                  ▼
     Machine Learning Models
                  │
                  ▼
        Power BI Dashboard
```

---

# Project Workflow

## Phase 1 — Data Collection

Collect invoice data from multiple manufacturers.

Supported source formats:

- Excel invoices
- PDF invoices
- CSV exports

---

## Phase 2 — ETL Pipeline

Power Query automatically:

- imports source files;
- extracts invoice information;
- standardizes the data structure;
- merges multiple source formats;
- prepares datasets for analysis.

A VBA automation layer:

- refreshes all Power Query queries;
- cleans the output directory;
- exports standardized CSV datasets;
- provides an ETL Control Panel with execution logs.

---

## Phase 3 — Product Normalization

Manufacturer-specific Python modules transform product descriptions into standardized technical features.

Examples:

- number of cores
- pair count
- conductor cross-section
- conductor class
- shielding
- insulation material
- fire performance
- voltage rating
- climate category

The result is a unified feature table that enables direct comparison of technically equivalent cable constructions from different manufacturers.

---

## Phase 4 — Exploratory Data Analysis

- price distribution
- historical price trends
- manufacturer comparison
- outlier detection
- statistical summaries

---

## Phase 5 — Machine Learning

Predictive models are trained to estimate cable prices based on extracted technical characteristics.

Potential algorithms include:

- Linear Regression
- Random Forest
- Gradient Boosting
- XGBoost

---

## Phase 6 — Business Intelligence

Interactive Power BI dashboards provide:

- manufacturer price comparison;
- historical price dynamics;
- forecasted prices;
- market overview;
- product-level analytics.

---

# Current Status

- ✅ Automated ETL pipeline
- ✅ Excel invoice import
- ✅ PDF invoice import
- ✅ CSV import
- ✅ VBA ETL automation
- ✅ Standardized CSV export
- 🔄 Product normalization (in progress)
- ⏳ Feature engineering
- ⏳ Machine learning
- ⏳ Power BI dashboard

---

# Repository Structure

```text
Cable-Price-Intelligence/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── power_query/
│
├── src/
│
├── notebooks/
│
├── reports/
│
├── dashboard/
│
├── README.md
│
└── requirements.txt
```