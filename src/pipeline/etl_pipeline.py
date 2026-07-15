from pathlib import Path

import pandas as pd


class ETLPipeline:
    """
    Loads standardized CSV files exported by Power Query / VBA.
    """

    def __init__(self, input_folder: str = "data/processed"):
        self.input_folder = Path(input_folder)

    def load_manufacturer_csv(self, file_name: str) -> pd.DataFrame:
        path = self.input_folder / file_name

        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return pd.read_csv(path, sep=";", encoding="utf-8")

    def load_all_csv(self) -> dict[str, pd.DataFrame]:
        data = {}

        for path in self.input_folder.glob("*.csv"):
            if path.stem.endswith("_UCM"):
                continue

            manufacturer = path.stem
            data[manufacturer] = pd.read_csv(
                path,
                sep=";",
                encoding="utf-8-sig",
            )

        return data
