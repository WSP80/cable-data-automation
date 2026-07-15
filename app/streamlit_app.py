from __future__ import annotations

from io import StringIO
from pathlib import Path
import sys
from typing import Any

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(PROJECT_ROOT))

from scripts.export_ucm import build_ucm_from_source, load_manufacturer_config
from scripts.predict_prices import MODEL_PATH, predict_ucm_frame_all_models
from src.parsers.registry import PARSERS
from src.pricing import load_price_model_catalog


STATUS_LABELS = {
    "ok": "Successful",
    "insufficient_feature_value_data": "Unsupported Features",
    "insufficient_model_data": "Insufficient Model Data",
    "incompatible_target_construction": "Incompatible Construction",
    "generation_failed": "Generation Failed",
    "missing_cable_family": "Missing Cable Family",
}

STATUS_COLORS = {
    "Successful": "#DCFCE7",
    "Unsupported Features": "#FFFFFF",
    "Insufficient Model Data": "#FFFFFF",
    "Incompatible Construction": "#FFFFFF",
    "Generation Failed": "#FFFFFF",
    "Missing Cable Family": "#FFFFFF",
}

DISPLAY_COLUMNS = [
    "source_row_number",
    "product_description",
    "target_cable_family",
    "generated_designation",
    "model_price_excl_vat",
    "status_label",
]

DISPLAY_NAMES = {
    "source_row_number": "Row",
    "product_description": "Source Mark",
    "target_cable_family": "Target Family",
    "generated_designation": "Generated Mark",
    "model_price_excl_vat": "Predicted Price",
    "status_label": "Status",
}


st.set_page_config(
    page_title="Cable Price Intelligence",
    layout="wide",
)


@st.cache_resource
def load_runtime() -> tuple[dict[str, dict[str, Any]], Any]:
    config = load_manufacturer_config(PROJECT_ROOT / "config" / "manufacturers.json")
    catalog = load_price_model_catalog(PROJECT_ROOT / MODEL_PATH)
    return config, catalog


def decode_upload(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1251"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise UnicodeError("Uploaded file must be encoded as UTF-8 or Windows-1251.")


def load_prediction_source_from_text(text: str) -> pd.DataFrame:
    source = pd.read_csv(StringIO(text), sep=";")

    if "product_description" in source.columns:
        return source

    descriptions = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not descriptions:
        raise ValueError("Uploaded file contains no cable designations.")

    return pd.DataFrame({"product_description": descriptions})


def run_prediction(
    source: pd.DataFrame,
    manufacturer: str,
    config: dict[str, dict[str, Any]],
    catalog: Any,
) -> pd.DataFrame:
    parser_name = str(config[manufacturer]["parser"])
    ucm_frame = build_ucm_from_source(source, PARSERS[parser_name])
    result = predict_ucm_frame_all_models(ucm_frame, catalog, config)
    result["status_label"] = result["prediction_status"].map(
        STATUS_LABELS
    ).fillna(result["prediction_status"])
    return result


def prediction_report_csv(result: pd.DataFrame) -> bytes:
    output = StringIO()
    grouped = list(result.groupby("source_row_number", sort=False))

    for group_index, (_, group) in enumerate(grouped):
        group.to_csv(
            output,
            sep=";",
            index=False,
            header=group_index == 0,
            lineterminator="\n",
        )

        if group_index < len(grouped) - 1:
            output.write("\n")

    return output.getvalue().encode("utf-8-sig")


def status_style(row: pd.Series) -> list[str]:
    color = STATUS_COLORS.get(str(row.get("Status")), "#FFFFFF")
    return [f"background-color: {color}" for _ in row]


def format_price(value: Any) -> str:
    if pd.isna(value):
        return ""

    return f"{float(value):,.2f}"


def render_metrics(result: pd.DataFrame) -> None:
    source_offers = int(result["source_row_number"].nunique())
    predictions = len(result)
    successful = int(result["model_price_excl_vat"].notna().sum())
    success_rate = successful / predictions if predictions else 0
    average_price = result["model_price_excl_vat"].dropna().mean()

    first, second, third, fourth, fifth = st.columns(5)
    first.metric("Source Offers", source_offers)
    second.metric("Predictions", predictions)
    third.metric("Successful", successful)
    fourth.metric("Success Rate", f"{success_rate:.0%}")
    fifth.metric(
        "Avg Predicted Price",
        "" if pd.isna(average_price) else f"{average_price:,.2f}",
    )


def filter_result(result: pd.DataFrame) -> pd.DataFrame:
    target_options = sorted(result["target_cable_family"].dropna().unique())
    status_options = sorted(result["status_label"].dropna().unique())
    source_options = result["product_description"].dropna().unique().tolist()

    target_filter, source_filter, status_filter = st.columns([1.2, 2.8, 1.4])

    selected_targets = target_filter.multiselect(
        "Target Family",
        target_options,
        default=target_options,
    )
    selected_sources = source_filter.multiselect(
        "Source Mark",
        source_options,
        default=source_options,
    )
    selected_statuses = status_filter.multiselect(
        "Status",
        status_options,
        default=status_options,
    )

    return result[
        result["target_cable_family"].isin(selected_targets)
        & result["product_description"].isin(selected_sources)
        & result["status_label"].isin(selected_statuses)
    ].copy()


def render_result_table(result: pd.DataFrame) -> None:
    table = result[DISPLAY_COLUMNS].rename(columns=DISPLAY_NAMES)
    table["Predicted Price"] = table["Predicted Price"].map(format_price)
    styled = table.style.apply(status_style, axis=1)
    st.dataframe(
        styled,
        use_container_width=True,
        hide_index=True,
    )


def infer_manufacturer(file_name: str, manufacturers: list[str]) -> str | None:
    stem = Path(file_name).stem.upper()

    for manufacturer in manufacturers:
        if stem == manufacturer.upper():
            return manufacturer

    for manufacturer in sorted(manufacturers, key=len, reverse=True):
        if manufacturer.upper() in stem:
            return manufacturer

    return None


def main() -> None:
    st.title("Cable Price Intelligence")
    st.caption("Predict cable prices from manufacturer designations via UCM.")

    try:
        config, catalog = load_runtime()
    except FileNotFoundError as error:
        st.error(str(error))
        st.stop()

    manufacturers = list(config)
    uploaded_file = st.file_uploader(
        "Upload a CSV or text file with cable designations",
        type=["csv", "txt"],
    )

    if uploaded_file is None:
        st.info(
            "Upload a manufacturer file without prices. The file name defines "
            "the parser."
        )
        st.stop()

    manufacturer = infer_manufacturer(uploaded_file.name, manufacturers)
    if manufacturer is None:
        st.error(
            "Source manufacturer could not be inferred from the file name. "
            f"Use one of these manufacturer codes in the file name: {', '.join(manufacturers)}."
        )
        st.stop()

    st.text_input(
        "Source Manufacturer",
        value=manufacturer,
        disabled=True,
    )

    if st.button("Run Prediction", type="primary", use_container_width=False):
        try:
            text = decode_upload(uploaded_file.getvalue())
            source = load_prediction_source_from_text(text)
            st.session_state["prediction_result"] = run_prediction(
                source,
                manufacturer,
                config,
                catalog,
            )
            st.session_state["prediction_file_name"] = uploaded_file.name
        except Exception as error:  # noqa: BLE001
            st.error(str(error))
            st.stop()

    result = st.session_state.get("prediction_result")

    if result is None:
        st.stop()

    render_metrics(result)
    filtered = filter_result(result)
    render_result_table(filtered)

    st.download_button(
        "Download priced CSV",
        data=prediction_report_csv(result),
        file_name=f"{Path(st.session_state['prediction_file_name']).stem}_PRICED.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
