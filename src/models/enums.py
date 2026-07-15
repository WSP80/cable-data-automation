"""
Universal Cable Model (UCM)
Engineering Enumerations
"""

from enum import Enum


# ==========================================================
# Structural Features
# ==========================================================

class GroupType(str, Enum):
    CORE = "core"
    PAIR = "pair"
    TRIPLE = "triple"
    QUAD = "quad"
    QUINT = "quint"


class ConductorMaterial(str, Enum):
    CU = "Cu"
    CU_TINNED = "Cu_tinned"


# ==========================================================
# Materials
# ==========================================================

class InsulationMaterial(str, Enum):
    PVC = "PVC"
    HALOGEN_FREE = "Halogen-free polymer compound"
    XLPO = "Cross-linked polyolefin (XLPO)"
    EPR = "Ethylene propylene rubber (EPR)"
    CERAMIFIABLE_SILICONE = "Ceramifiable silicone rubber"


class ScreenType(str, Enum):
    NONE = "None"
    ALUMINUM_FOIL = "Aluminum foil"
    COPPER_FOIL = "Copper foil"
    COPPER_BRAID = "Copper wire braid"
    TINNED_COPPER_BRAID = "Tinned copper wire braid"
    COMBINED = "Combined (aluminum foil + tinned copper wire braid)"


class FillerMaterial(str, Enum):
    PVC = "PVC"
    HALOGEN_FREE = "Halogen-free polymer compound"


class SheathMaterial(str, Enum):
    PVC = "PVC"
    HALOGEN_FREE = "Halogen-free polymer compound"


class ArmorType(str, Enum):
    NONE = "None"
    GALVANIZED_STEEL_WIRE_BRAID = "Galvanized steel wire braid"
    GALVANIZED_STEEL_WIRE_ARMOR = "Galvanized steel wire armor"
    GALVANIZED_STEEL_TAPE_ARMOR = "Galvanized steel tape armor"
