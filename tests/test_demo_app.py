"""Happy-path baseline tests; the demo PR deliberately violates the contract."""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('demo_assistant',Path(__file__).parents[1]/'examples/assistant.py')
assistant=importlib.util.module_from_spec(spec)
spec.loader.exec_module(assistant)


def test_demo_answer_contract():
    assert assistant.parse_answer({'answer':'  hello  '})=='hello'


def test_demo_reads_a_note_inside_root(tmp_path):
    (tmp_path/'note.txt').write_text('demo note')
    assert assistant.load_note(tmp_path,'note.txt')=='demo note'
