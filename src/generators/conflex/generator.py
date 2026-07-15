from src.generators.base_generator import BaseGenerator
from src.generators.conflex.rules import build_conflex_mark
from src.models.ucm import UCM


class ConflexGenerator(BaseGenerator):
    """
    Generate CONFLEX cable designations from UCM.
    """

    def generate(self, ucm: UCM, alphabet: str = "cyrillic") -> str:
        return build_conflex_mark(ucm, alphabet=alphabet)
