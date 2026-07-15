from src.generators.base_generator import BaseGenerator
from src.generators.toflex.rules import build_toflex_mark
from src.models.ucm import UCM


class ToflexGenerator(BaseGenerator):
    """
    Generate TOFLEX cable designations from UCM.
    """

    def generate(self, ucm: UCM, alphabet: str = "cyrillic") -> str:
        return build_toflex_mark(ucm, alphabet=alphabet)
