from dataclasses import dataclass
from typing import Optional

from src.models.enums import ArmorType, ConductorMaterial, FillerMaterial
from src.models.enums import InsulationMaterial, ScreenType, SheathMaterial


@dataclass
class UCM:
    """
    Universal Cable Model.

    Manufacturer-independent representation of a cable construction.
    Parsers convert manufacturer-specific cable marks into this schema.
    Generators convert this schema back into manufacturer-specific cable marks.
    """

    # Source / identification
    source_file: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    product_description: Optional[str] = None
    unit_price_excl_vat: Optional[float] = None
    length_km: Optional[float] = None
    comment: Optional[str] = None

    # Structural Features
    cable_family: Optional[str] = None
    core_groups: Optional[int] = None
    group_type: Optional[str] = None
    cross_section_mm2: Optional[float] = None
    cross_section_designation: Optional[str] = None
    conductor_flexibility_class: Optional[int] = None
    conductor_material: Optional[str] = None

    # Materials
    insulation_material: Optional[str] = None
    mica_tape_layers: Optional[int] = None
    individual_screen: Optional[str] = None
    filler_material: Optional[str] = None
    bedding_under_screen: Optional[bool] = None
    overall_screen: Optional[str] = None
    sheath_material: Optional[str] = None
    armor_type: Optional[str] = None
    water_blocking: Optional[bool] = None

    # Performance Features
    flame_retardant: Optional[bool] = None
    fire_resistant: Optional[bool] = None
    low_smoke: Optional[bool] = None
    low_toxicity: Optional[bool] = None
    halogen_free: Optional[bool] = None
    cold_resistant: Optional[bool] = None
    uv_resistant: Optional[bool] = None
    oil_resistant: Optional[bool] = None
    chemical_resistant: Optional[bool] = None
    rated_voltage_v: Optional[int] = None
    intrinsically_safe: Optional[bool] = None
    explosive_area_application: Optional[bool] = None
    sheath_color: Optional[str] = None

    # Derived Features
    total_conductors: Optional[int] = None
    copper_area_mm2: Optional[float] = None

    def finalize_features(self) -> None:
        """
        Fill explicit defaults for ML features and derived values.
        """

        if self.conductor_material is None:
            self.conductor_material = ConductorMaterial.CU.value

        if self.mica_tape_layers is None:
            self.mica_tape_layers = 0

        if self.individual_screen is None:
            self.individual_screen = ScreenType.NONE.value

        if self.filler_material is None:
            self.filler_material = self._infer_filler_material()

        if self.bedding_under_screen is None:
            self.bedding_under_screen = False

        if self.overall_screen is None:
            self.overall_screen = ScreenType.NONE.value

        if self.armor_type is None:
            self.armor_type = ArmorType.NONE.value

        if self.water_blocking is None:
            self.water_blocking = False

        if self.intrinsically_safe is None:
            self.intrinsically_safe = False

        if self.explosive_area_application is None:
            self.explosive_area_application = False

        if self.sheath_color is None:
            self.sheath_color = "blue" if self.intrinsically_safe else "black"

        for field_name in self._boolean_feature_names():
            if getattr(self, field_name) is None:
                setattr(self, field_name, False)

        self.calculate_derived_features()

    def _infer_filler_material(self) -> Optional[str]:
        if self.sheath_material == SheathMaterial.PVC.value:
            return FillerMaterial.PVC.value

        if self.sheath_material == SheathMaterial.HALOGEN_FREE.value:
            return FillerMaterial.HALOGEN_FREE.value

        if self.insulation_material == InsulationMaterial.PVC.value:
            return FillerMaterial.PVC.value

        if self.insulation_material == InsulationMaterial.HALOGEN_FREE.value:
            return FillerMaterial.HALOGEN_FREE.value

        return None

    def _boolean_feature_names(self) -> list[str]:
        return [
            "flame_retardant",
            "fire_resistant",
            "low_smoke",
            "low_toxicity",
            "halogen_free",
            "cold_resistant",
            "uv_resistant",
            "oil_resistant",
            "chemical_resistant",
            "intrinsically_safe",
            "explosive_area_application",
        ]

    def calculate_derived_features(self) -> None:
        group_size = {
            "core": 1,
            "pair": 2,
            "triple": 3,
            "quad": 4,
            "quint": 5,
        }

        if self.core_groups is not None and self.group_type in group_size:
            self.total_conductors = self.core_groups * group_size[self.group_type]

        if self.total_conductors is not None and self.cross_section_mm2 is not None:
            self.copper_area_mm2 = self.total_conductors * self.cross_section_mm2
