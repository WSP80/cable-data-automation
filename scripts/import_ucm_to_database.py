from pathlib import Path
import sys
from uuid import uuid4

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.database import CableRepository, create_database_engine


INPUT_DIR = Path("data/processed")


def main() -> None:
    repository = CableRepository(create_database_engine())
    repository.create_schema()
    input_paths = sorted(INPUT_DIR.glob("*_UCM.csv"))

    if not input_paths:
        raise FileNotFoundError(f"No UCM files found in {INPUT_DIR}")

    load_run_id = str(uuid4())
    repository.start_current_load("training")

    for input_path in input_paths:
        frame = pd.read_csv(
            input_path,
            sep=";",
            encoding="utf-8-sig",
        )
        _, inserted = repository.store_ucm_frame(
            frame,
            dataset_role="training",
            source_dataset=input_path.name,
            load_run_id=load_run_id,
        )
        print(
            f"{input_path.name}: {inserted} inserted, "
            f"{len(frame) - inserted} already stored"
        )

    print(f"training_load_run_id: {load_run_id}")


if __name__ == "__main__":
    main()
