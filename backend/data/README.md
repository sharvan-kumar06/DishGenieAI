# DishGenie Recipe Database Directory

This directory stores the local SQLite database and dataset files for DishGenie.

## Files
- `dishgenie_recipes.db`: Local SQLite database containing indexed, normalized Indian recipes with full-text search (FTS5).
- `Cleaned_Indian_Food_Dataset.csv` (optional local copy): Kaggle dataset downloaded from:
  https://www.kaggle.com/datasets/sooryaprakash12/cleaned-indian-recipes-dataset

## Quick Start Import Command
Run the import script from the `backend/` directory:
```bash
python scripts/import_recipes.py
```
Or specify an explicit CSV file path:
```bash
python scripts/import_recipes.py --csv-path "C:\path\to\Cleaned_Indian_Food_Dataset.csv"
```
The script is idempotent: running it multiple times will not create duplicate entries.
