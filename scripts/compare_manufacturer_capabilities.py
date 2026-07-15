from pathlib import Path
from datetime import datetime

import pandas as pd


OUTPUT_PATH = Path("reports/tables/manufacturer_feature_capabilities.csv")


CAPABILITIES = {
    "cable_family": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "ATOMKIP-KU",
        "conflex_values": "CONFLEX",
        "note": "Manufacturer identity changes by target mark.",
    },
    "core_groups": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "integer",
        "conflex_values": "integer",
        "note": "Both marks encode number of cores or groups.",
    },
    "group_type": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "core,pair,triple,quad",
        "conflex_values": "core,pair,triple,quad",
        "note": "UCM supports quint; these two manufacturers currently map core,pair,triple,quad.",
    },
    "cross_section_mm2": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "numeric",
        "conflex_values": "numeric",
        "note": "Both marks encode conductor cross-section.",
    },
    "cross_section_designation": {
        "atomkip": "formatting",
        "conflex": "formatting",
        "atomkip_values": "text",
        "conflex_values": "text",
        "note": "Formatting can differ, but numeric meaning is preserved.",
    },
    "conductor_flexibility_class": {
        "atomkip": "supported",
        "conflex": "implicit/default",
        "atomkip_values": "1,2,3,5",
        "conflex_values": "5",
        "atomkip_to_conflex": "partial",
        "conflex_to_atomkip": "lossless_or_rule_based",
        "note": "CONFLEX assumes class 5 unless explicitly extended.",
    },
    "conductor_material": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "Cu,Cu_tinned",
        "conflex_values": "Cu,Cu_tinned",
        "note": "Both can encode tinned conductor.",
    },
    "insulation_material": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "PVC,halogen_free,XLPO,EPR,ceramifiable_silicone",
        "conflex_values": "PVC,halogen_free,XLPO,EPR",
        "atomkip_to_conflex": "partial",
        "conflex_to_atomkip": "lossless_or_rule_based",
        "note": "CONFLEX has no mapped ceramifiable silicone token.",
    },
    "mica_tape_layers": {
        "atomkip": "derived/partial",
        "conflex": "not_encoded",
        "atomkip_values": "0,1,2",
        "conflex_values": "",
        "atomkip_to_conflex": "lossy",
        "conflex_to_atomkip": "not_relevant",
        "note": "FR can be encoded, but exact mica tape layer count is not mark-stable.",
    },
    "individual_screen": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "none,aluminum_foil,copper_braid,copper_foil,combined",
        "conflex_values": "none,aluminum_foil,copper_braid,copper_foil,combined",
        "note": "CONFLEX encodes individual screen after a parenthesized group, for example 2x(2x0,5)ef.",
    },
    "filler_material": {
        "atomkip": "derived",
        "conflex": "derived",
        "atomkip_values": "PVC,halogen_free",
        "conflex_values": "PVC,halogen_free",
        "note": "Inferred from insulation/sheath, not directly encoded.",
    },
    "bedding_under_screen": {
        "atomkip": "not_encoded",
        "conflex": "not_encoded",
        "atomkip_values": "",
        "conflex_values": "",
        "note": "UCM field is not represented in either current mark generator.",
    },
    "overall_screen": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "none,aluminum_foil,copper_braid,copper_foil,tinned_copper_braid,combined",
        "conflex_values": "none,aluminum_foil,copper_braid,copper_foil,tinned_copper_braid,combined",
        "note": "CONFLEX has more detailed combined variants than current UCM preserves.",
    },
    "sheath_material": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "PVC,halogen_free",
        "conflex_values": "PVC,halogen_free",
        "note": "Both marks encode sheath material.",
    },
    "armor_type": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "none,steel_wire_braid,steel_tape",
        "conflex_values": "none,steel_wire_braid,steel_tape",
        "note": "Both marks encode K/B armor families.",
    },
    "water_blocking": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks have a water-blocking token.",
    },
    "flame_retardant": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode ng(A).",
    },
    "fire_resistant": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode FR.",
    },
    "low_smoke": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode LS.",
    },
    "low_toxicity": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode low toxicity as LTx.",
    },
    "halogen_free": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode HF or halogen-free material.",
    },
    "cold_resistant": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode HL.",
    },
    "uv_resistant": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both marks encode UV.",
    },
    "oil_resistant": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "Both mark systems have M for oil resistance.",
    },
    "chemical_resistant": {
        "atomkip": "supported",
        "conflex": "not_encoded",
        "atomkip_values": "true,false",
        "conflex_values": "",
        "atomkip_to_conflex": "lossy",
        "conflex_to_atomkip": "not_relevant",
        "note": "ATOMKIP AS has no current CONFLEX equivalent.",
    },
    "rated_voltage_v": {
        "atomkip": "supported",
        "conflex": "supported/default",
        "atomkip_values": "explicit voltage",
        "conflex_values": "explicit voltage, default 300",
        "note": "CONFLEX uses 300 V when voltage is absent.",
    },
    "intrinsically_safe": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "ATOMKIP uses i, CONFLEX uses Ex-i.",
    },
    "explosive_area_application": {
        "atomkip": "supported",
        "conflex": "supported",
        "atomkip_values": "true,false",
        "conflex_values": "true,false",
        "note": "ATOMKIP uses Vz, CONFLEX uses Ex.",
    },
    "sheath_color": {
        "atomkip": "supported",
        "conflex": "implicit/default",
        "atomkip_values": "text color",
        "conflex_values": "black, blue for Ex-i",
        "atomkip_to_conflex": "partial",
        "conflex_to_atomkip": "lossless_or_rule_based",
        "note": "CONFLEX does not preserve arbitrary color text like ATOMKIP.",
    },
    "total_conductors": {
        "atomkip": "derived",
        "conflex": "derived",
        "atomkip_values": "integer",
        "conflex_values": "integer",
        "note": "Derived from core_groups and group_type.",
    },
    "copper_area_mm2": {
        "atomkip": "derived",
        "conflex": "derived",
        "atomkip_values": "numeric",
        "conflex_values": "numeric",
        "note": "Derived from total_conductors and cross_section_mm2.",
    },
}


LOSSLESS_STATUSES = {
    "supported",
    "supported/default",
    "formatting",
    "derived",
}


def classify_conversion(source_status: str, target_status: str) -> str:
    if source_status in {"not_encoded", "not_implemented", "derived"}:
        return "not_relevant"

    if target_status in LOSSLESS_STATUSES:
        return "lossless_or_rule_based"

    if target_status in {"implicit/default", "supported/default"}:
        return "partial"

    if target_status == "derived/partial":
        return "partial"

    return "lossy"


def build_report() -> pd.DataFrame:
    rows = []

    for feature, data in CAPABILITIES.items():
        atomkip_status = data["atomkip"]
        conflex_status = data["conflex"]
        rows.append(
            {
                "feature": feature,
                "atomkip": atomkip_status,
                "conflex": conflex_status,
                "atomkip_values": data["atomkip_values"],
                "conflex_values": data["conflex_values"],
                "atomkip_to_conflex": classify_conversion(
                    atomkip_status,
                    conflex_status,
                )
                if "atomkip_to_conflex" not in data
                else data["atomkip_to_conflex"],
                "conflex_to_atomkip": classify_conversion(
                    conflex_status,
                    atomkip_status,
                )
                if "conflex_to_atomkip" not in data
                else data["conflex_to_atomkip"],
                "note": data["note"],
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    report = build_report()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_PATH

    try:
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")
    except PermissionError:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = OUTPUT_PATH.with_name(
            f"{OUTPUT_PATH.stem}_{timestamp}{OUTPUT_PATH.suffix}"
        )
        report.to_csv(output_path, sep=";", index=False, encoding="utf-8-sig")

    lossy = report[
        (report["atomkip_to_conflex"] == "lossy")
        | (report["conflex_to_atomkip"] == "lossy")
        | (report["atomkip_to_conflex"] == "partial")
        | (report["conflex_to_atomkip"] == "partial")
    ]

    print(f"features: {len(report)}")
    print(f"lossy_or_partial_features: {len(lossy)}")
    print(f"output_file: {output_path}")
    print(lossy[["feature", "atomkip", "conflex", "atomkip_to_conflex", "conflex_to_atomkip"]].to_string(index=False))


if __name__ == "__main__":
    main()
