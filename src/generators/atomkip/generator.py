from src.generators.base_generator import BaseGenerator
from src.generators.atomkip.rules import build_atomkip_mark
from src.models.ucm import UCM


class AtomkipGenerator(BaseGenerator):
    """
    Generate ATOMKIP cable designations from UCM.
    """

    def generate(self, ucm: UCM, alphabet: str = "cyrillic") -> str:
        return build_atomkip_mark(ucm, alphabet=alphabet)
