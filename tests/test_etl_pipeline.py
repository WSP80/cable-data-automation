import pandas as pd

from src.pipeline.etl_pipeline import ETLPipeline


def test_etl_pipeline_loads_source_csv_and_ignores_ucm_outputs(tmp_path):
    source = pd.DataFrame([{"product_description": "MKV 2x1,0"}])
    source.to_csv(
        tmp_path / "MK.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )
    source.assign(cable_family="MK").to_csv(
        tmp_path / "MK_UCM.csv",
        sep=";",
        index=False,
        encoding="utf-8-sig",
    )

    loaded = ETLPipeline(str(tmp_path)).load_all_csv()

    assert list(loaded) == ["MK"]
    assert loaded["MK"]["product_description"].tolist() == ["MKV 2x1,0"]
