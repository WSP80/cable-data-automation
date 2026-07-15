from src.parsers.atomkip.parser import AtomkipParser
from src.parsers.conflex.parser import ConflexParser
from src.parsers.mk.parser import MKParser
from src.parsers.toflex.parser import ToflexParser

PARSERS = {

    "atomkip": AtomkipParser(),

    "conflex": ConflexParser(),

    "mk": MKParser(),

    "toflex": ToflexParser(),

}
