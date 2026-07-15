# GitHub Sync Runbook

This runbook describes how to prepare the repository for GitHub without
committing private commercial data.

## 1. Prepare Anonymized Demo Data

Put public demo files into:

```text
data/demo/raw
```

Do not commit files from:

```text
data/raw
data/archiv
data/processed
data/prediction_input
data/prediction_output
data/database
artifacts/models
reports/tables
```

## 2. Check Ignored Private Data

Run:

```powershell
git status --short --ignored data
```

Private folders should appear as ignored entries. Demo files in `data/demo/raw`
should appear as normal untracked files before staging.

## 3. Review Public Files Before Staging

Run:

```powershell
git status --short
git diff --stat
```

For new public data files, inspect the content manually before staging.

## 4. Stage Only Public Project Files

Example:

```powershell
git add README.md docs src scripts sql config app tests pyproject.toml uv.lock docker-compose.yml .env.example .gitignore
git add data/demo/raw
```

Avoid `git add .` until all private-data ignore rules have been verified.

## 5. Final Pre-Commit Safety Check

Run:

```powershell
git diff --cached --stat
git diff --cached --name-only
```

Make sure staged files do not include private raw data, processed commercial
datasets, prediction batches, local databases, or trained model artifacts.

## 6. Commit

Run:

```powershell
git commit -m "Add cable price intelligence pipeline"
```

## 7. Push to GitHub

Run:

```powershell
git push origin main
```

If authentication is requested, use GitHub authentication through your local Git
Credential Manager or a personal access token.
