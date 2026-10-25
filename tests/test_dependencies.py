import json
from ai_review.dependencies import load_dependencies
from ai_review.context import build_context
from ai_review.config import Settings
from ai_review.schemas import ReviewSnapshot,ReviewRequest,FileSnapshot
from ai_review.tools import SnapshotTools


def test_imported_called_function_is_available_as_unchanged_supporting_context():
    source='from pkg.utils import get_tools\n\ndef run():\n    return get_tools()\n'
    helper='def get_tools():\n    return [ResearchComplete]\n\ndef unrelated():\n    return "ignored"\n'
    s=ReviewSnapshot(ReviewRequest('me','repo',1),'a'*40,'b'*40,{
        'pkg/app.py':FileSnapshot('pkg/app.py',source,added_lines=[4]),
        'pkg/utils.py':FileSnapshot('pkg/utils.py',helper,changed=False)})
    t=SnapshotTools(s,None,Settings())
    ranges=load_dependencies(s,t)
    data=json.loads(build_context(s,t.evidence,related_ranges=ranges))
    assert any('return [ResearchComplete]' in b['content'] for b in data['dependencies'])
    assert not any('unrelated' in b['content'] for b in data['dependencies'])
    assert not s.files['pkg/utils.py'].changed


def test_missing_external_import_does_not_invent_project_source():
    source='from external_sdk import missing\nx=missing()\n'
    s=ReviewSnapshot(ReviewRequest('me','repo',1),'a'*40,'b'*40,
        {'app.py':FileSnapshot('app.py',source,added_lines=[2])})
    assert load_dependencies(s,SnapshotTools(s,None,Settings()))=={}


def dependencies_for(source_path,statement,helpers):
    s=ReviewSnapshot(ReviewRequest('me','repo',1),'a'*40,'b'*40,
        {source_path:FileSnapshot(source_path,statement+'\nx=get_tools()\n',added_lines=[2])})
    s.files.update({p:FileSnapshot(p,'def get_tools():\n    return []\n',changed=False) for p in helpers})
    return load_dependencies(s,SnapshotTools(s,None,Settings()))


def test_relative_import_uses_its_package_instead_of_unrelated_root_file():
    assert set(dependencies_for('pkg/app.py','from .utils import get_tools',
        ['utils.py','pkg/utils.py']))=={'pkg/utils.py'}


def test_absolute_import_does_not_guess_a_sibling_module():
    assert dependencies_for('pkg/app.py','from utils import get_tools',['pkg/utils.py'])=={}


def test_package_exports_and_nested_source_roots_are_resolved():
    assert set(dependencies_for('pkg/app.py','from pkg import get_tools',
        ['pkg/__init__.py']))=={'pkg/__init__.py'}
    assert set(dependencies_for('vendor/project/src/pkg/app.py','from pkg.utils import get_tools',
        ['vendor/project/src/pkg/utils.py']))=={'vendor/project/src/pkg/utils.py'}
