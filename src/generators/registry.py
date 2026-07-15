from src.generators.atomkip.generator import AtomkipGenerator
from src.generators.mk.generator import MKGenerator
from src.generators.toflex.generator import ToflexGenerator
from src.generators.conflex.generator import ConflexGenerator


GENERATORS = {

    "atomkip": AtomkipGenerator(),

    "mk": MKGenerator(),

    "toflex": ToflexGenerator(),

    "conflex": ConflexGenerator()

}