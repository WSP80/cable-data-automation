from src.models.enums import InsulationMaterial
from src.parsers.atomkip.rules import extract_mica_tape_layers
from src.parsers.atomkip.parser import AtomkipParser


FRHF_MARK = (
    "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
    "\u0418\u043c\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-FRHF-\u0432 "
    "10\u04453\u04451,0\u043b\u043a\u043b3 690\u0412"
)

HF_MARK = (
    "\u0410\u0422\u041e\u041c\u041a\u0418\u041f-\u041a\u0423"
    "\u0418\u043c\u041f\u041e\u043c\u041f\u043d\u0433(\u0410)-HF-\u0432 "
    "10\u04453\u04451,0\u043b\u043a\u043b3 690\u0412"
)


def test_atomkip_parser_sets_two_mica_tape_layers_for_fr_by_default():
    ucm = AtomkipParser().parse(FRHF_MARK)

    assert ucm.fire_resistant is True
    assert ucm.mica_tape_layers == 2


def test_atomkip_parser_sets_one_mica_tape_layer_from_comment():
    ucm = AtomkipParser().parse(FRHF_MARK, comment="FR = 1")

    assert ucm.fire_resistant is True
    assert ucm.mica_tape_layers == 1


def test_atomkip_parser_sets_zero_mica_tape_layers_without_fr():
    ucm = AtomkipParser().parse(HF_MARK)

    assert ucm.fire_resistant is False
    assert ucm.mica_tape_layers == 0


def test_atomkip_parser_sets_zero_mica_tape_layers_for_ceramifiable_silicone():
    mica_tape_layers = extract_mica_tape_layers(
        FRHF_MARK,
        InsulationMaterial.CERAMIFIABLE_SILICONE.value,
    )

    assert mica_tape_layers == 0
