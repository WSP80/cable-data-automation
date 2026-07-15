import pandas as pd

from src.descriptions import DescriptionRule
from src.descriptions import describe_ucm_features
from src.descriptions import describe_ucm_frame
from src.descriptions import load_description_dictionary
from src.descriptions import transliterate_designation


def test_load_description_dictionary_preserves_workbook_order():
    rules = load_description_dictionary()

    assert rules[0] == DescriptionRule("cable_family", "Cable Family")
    assert rules[1] == DescriptionRule(
        "insulation_material",
        "Insulation Material",
    )
    assert rules[-1] == DescriptionRule("rated_voltage_v", "Rated Voltage (V)")


def test_describe_ucm_features_uses_dictionary_order_and_skips_empty_values():
    dictionary = [
        DescriptionRule("individual_screen", "Individual Screen"),
        DescriptionRule("overall_screen", "Overall Screen"),
        DescriptionRule("fire_resistant", "Fire Resistant"),
        DescriptionRule("low_smoke", "Low Smoke"),
        DescriptionRule("core_groups", "Core Groups"),
        DescriptionRule("unknown_feature", "Unknown Feature"),
    ]
    features = {
        "core_groups": 2,
        "individual_screen": "None",
        "overall_screen": "Aluminum foil",
        "fire_resistant": True,
        "low_smoke": False,
        "unknown_feature": "",
        "rated_voltage_v": 300,
    }

    description = describe_ucm_features(features, dictionary)

    assert description.splitlines() == [
        "Overall Screen: Aluminum foil",
        "Fire Resistant",
        "Core Groups: 2",
    ]


def test_describe_ucm_frame_adds_multiline_description_column():
    dictionary = [
        DescriptionRule("cable_family", "Cable Family"),
        DescriptionRule("uv_resistant", "UV Resistant"),
        DescriptionRule("rated_voltage_v", "Rated Voltage (V)"),
    ]
    frame = pd.DataFrame(
        [
            {
                "product_description": "АТОМКИП-КУВВнг(А)-LS 2х2х1,0кл5 690В",
                "cable_family": "ATOMKIP-KU",
                "uv_resistant": "True",
                "rated_voltage_v": 690,
            },
            {
                "product_description": "MKVVng(A)-LS 2x2x1,0 300",
                "cable_family": "MK",
                "uv_resistant": "False",
                "rated_voltage_v": None,
            },
        ]
    )

    result = describe_ucm_frame(frame, dictionary)

    assert result.loc[0, "construction_description"] == (
        "ATOMKIP-KUVVng(A)-LS 2x2x1,0kl5 690V\n"
        "Cable Family: ATOMKIP-KU\n"
        "UV Resistant\n"
        "Rated Voltage (V): 690"
    )
    assert result.loc[1, "construction_description"] == (
        "MKVVng(A)-LS 2x2x1,0 300\n"
        "Cable Family: MK"
    )


def test_transliterate_designation_uses_family_specific_rules():
    mark = "ТОФЛЕКС КУВЭаВнг(А)-LS 2х2х0,75 - 300"

    assert transliterate_designation(mark, "TOFLEX-KU") == (
        "TOFLEX KUVEaVng(A)-LS 2x2x0,75 - 300"
    )
