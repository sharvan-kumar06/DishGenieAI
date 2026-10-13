#!/usr/bin/env python3
"""
Repeatable, idempotent import script for loading Cleaned Indian Recipes Dataset into SQLite.

Usage:
    python scripts/import_recipes.py
    python scripts/import_recipes.py --csv-path "path/to/Cleaned_Indian_Food_Dataset.csv"
    python scripts/import_recipes.py --db-path "path/to/dishgenie_recipes.db"
"""

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add backend directory to path so app modules can be imported
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.recipe_database import RecipeDatabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("importer")

DEFAULT_CANDIDATE_PATHS = [
    BACKEND_DIR / "data" / "Cleaned_Indian_Food_Dataset.csv",
    Path(os.path.expanduser("~")) / "Downloads" / "Cleaned_Indian_Food_Dataset.csv" / "Cleaned_Indian_Food_Dataset.csv",
    Path(os.path.expanduser("~")) / "Downloads" / "Cleaned_Indian_Food_Dataset.csv",
]


def find_default_csv_path() -> Path:
    """Finds existing CSV dataset from known local locations."""
    for p in DEFAULT_CANDIDATE_PATHS:
        if p.is_file():
            return p
    return DEFAULT_CANDIDATE_PATHS[0]


def import_recipes(csv_path: Path, db_path: Optional[Path] = None, batch_size: int = 500):
    """
    Reads dataset CSV and imports records into SQLite idempotently.
    Prevents duplicates on re-runs using the unique URL constraint.
    """
    if not csv_path.exists():
        logger.error(f"CSV file not found at: {csv_path.resolve()}")
        logger.error("Please provide valid --csv-path or place the dataset in backend/data/.")
        sys.exit(1)

    logger.info(f"Opening CSV dataset: {csv_path.resolve()} (Size: {csv_path.stat().st_size:,} bytes)")
    
    db = RecipeDatabase(str(db_path) if db_path else None)
    initial_count = db.count_recipes()
    logger.info(f"Existing recipes in database before import: {initial_count:,}")

    start_time = time.time()
    batch = []
    total_processed = 0
    total_inserted = 0
    total_skipped = 0

    with open(csv_path, mode="r", encoding="utf-8", errors="replace") as f:
        reader = csv.DictReader(f)
        
        # Verify required columns exist
        headers = reader.fieldnames or []
        cleaned_headers = [h.replace("\ufeff", "").strip() for h in headers]
        logger.info(f"Dataset columns found: {cleaned_headers}")

        for row in reader:
            # Clean BOM and whitespace from dictionary keys
            cleaned_row = {k.replace("\ufeff", "").strip(): v for k, v in row.items() if k is not None}
            batch.append(cleaned_row)
            total_processed += 1

            if len(batch) >= batch_size:
                inserted, skipped = db.insert_recipes_batch(batch)
                total_inserted += inserted
                total_skipped += skipped
                batch = []
                logger.info(
                    f"Processed {total_processed:,} rows | Inserted: {total_inserted:,} | Skipped/Duplicate: {total_skipped:,}"
                )

        # Process remainder batch
        if batch:
            inserted, skipped = db.insert_recipes_batch(batch)
            total_inserted += inserted
            total_skipped += skipped

    elapsed = time.time() - start_time
    final_count = db.count_recipes()

    logger.info("=" * 60)
    logger.info("IMPORT COMPLETE")
    logger.info(f"Time elapsed: {elapsed:.2f} seconds")
    logger.info(f"Total rows processed: {total_processed:,}")
    logger.info(f"New records inserted: {total_inserted:,}")
    logger.info(f"Skipped / Duplicates: {total_skipped:,}")
    logger.info(f"Final database record count: {final_count:,}")
    logger.info(f"Database location: {db.db_path.resolve()}")
    logger.info("=" * 60)

    return {
        "processed": total_processed,
        "inserted": total_inserted,
        "skipped": total_skipped,
        "final_count": final_count,
        "elapsed_seconds": elapsed,
    }


def main():
    parser = argparse.ArgumentParser(description="Idempotent CSV importer for DishGenie recipes database")
    parser.add_argument(
        "--csv-path",
        type=Path,
        default=find_default_csv_path(),
        help="Path to Cleaned_Indian_Food_Dataset.csv",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=None,
        help="Path to output SQLite database (default: backend/data/dishgenie_recipes.db)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=500,
        help="Batch transaction size for database inserts",
    )
    args = parser.parse_args()

    import_recipes(args.csv_path, args.db_path, args.batch_size)


if __name__ == "__main__":
    main()
