from src.generators.base_generator import BaseGenerator
from src.generators.mk.rules import build_mk_mark
from src.models.ucm import UCM


class MKGenerator(BaseGenerator):
    """
    Generate MK cable designations from UCM.
    """

    def generate(self, ucm: UCM, alphabet: str = "cyrillic") -> str:
        return build_mk_mark(ucm, alphabet=alphabet)
