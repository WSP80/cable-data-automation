from scripts.export_ucm import export_manufacturer_ucm


def test_export_manufacturer_ucm_skips_missing_input_file(tmp_path):
    result = export_manufacturer_ucm(
        "MK",
        "mk",
        input_dir=tmp_path,
    )

    assert result is None
