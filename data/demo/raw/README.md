# Demo Raw Data

Place anonymized demo input files here when preparing the repository for GitHub.

This folder is intended for public portfolio data only. Do not place original
commercial invoices, supplier files, customer names, invoice numbers, contract
numbers, real prices, or personal data in this folder.

Recommended demo file names:

```text
ATOMKIP-KU.csv
CONFLEX.csv
MK.csv
TOFLEX.csv
```

Recommended CSV columns:

```text
source_file;invoice_number;invoice_date;product_description;length_km;unit_price_excl_vat;comment
```

Anonymization rules:

- replace customer and supplier names with neutral labels;
- replace invoice numbers with generated values such as `DEMO-0001`;
- shift or generalize dates if needed;
- keep cable designations structurally realistic;
- scale or perturb prices if real price levels are sensitive;
- remove comments that contain names, project references, or contract details.

The production/private folders remain ignored by Git:

```text
data/raw
data/archiv
data/processed
data/prediction_input
data/prediction_output
data/database
reports/tables
```
