import io
import base64
import json
import zipfile
import pytest
from ai_review.publish import load_verified_report, publish_selected
from ai_review.schemas import ReviewReport, Finding, Evidence
from ai_review.github import ApiError


def report():
    f=Finding('correctness','high','Wrong result','app.py',1,1,[Evidence('app.py',1,1,'x=1')],impact='Wrong result',explanation='Concrete bug',verification_status='supported',inline_eligible=True,id='aabbccddeeff')
    return ReviewReport('me/demo',1,'a'*40,'b'*40,report_id='c'*20,reviewer_sha='d'*40,run_id='42',findings=[f])


class PublishClient:
    def __init__(self): self.posts=[];self.head='a'*40;self.reviews=[]
    def get(self,path):
        if '/contents/' in path:
            return dict(type='file',encoding='base64',size=4,content=base64.b64encode(b'x=1\n').decode())
        if path.endswith('/pulls/1'):
            return {'head':{'sha':self.head,'repo':{'full_name':'me/demo'}},'state':'open','user':{'type':'User'},'base':{'repo':{'full_name':'me/demo'}}}
        if path.endswith('/actions/runs/42'):
            return {'id':42,'event':'pull_request_target','status':'completed','conclusion':'success','head_sha':'a'*40,'head_branch':'demo/review-sample','path':'.github/workflows/analyze.yml','repository':{'full_name':'me/demo'}, 'pull_requests':[{'number':1,'base':{'ref':'main','sha':'d'*40},'head':{'sha':'a'*40}}], 'referenced_workflows':[{'path':'me/demo/.github/workflows/review-job.yml@'+'d'*40,'sha':'d'*40,'ref':'refs/heads/main'}]}
        if path.endswith('/actions/runs/42/artifacts'):
            return {'artifacts':[{'id':9,'name':'ai-review-42','expired':False,'size_in_bytes':2000}]}
        if path.endswith('/repos/me/demo'):
            return {'default_branch':'main'}
        raise AssertionError(path)
    def pages(self,path):
        if path.endswith('/reviews'): return self.reviews
        if path.endswith('/files'): return [{'filename':'app.py','status':'modified','patch':'@@ -0,0 +1 @@\n+x=1'}]
        raise AssertionError(path)
    def request(self,method,path,data):
        self.posts.append(data)
        return {'id':99}
    def download_artifact(self,path):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,'w') as z:
            z.writestr('report.json',report().to_json())
        return buf.getvalue()


def test_publish_selected_binds_commit_and_never_approves():
    c=PublishClient()
    result=publish_selected(c,report(),['aabbccddeeff'])
    assert result.status=='posted'
    assert c.posts[0]['event']=='COMMENT'
    assert c.posts[0]['commit_id']=='a'*40
    assert c.posts[0]['comments'][0]['line']==1


def test_reject_stale_empty_unknown_and_unverified():
    c=PublishClient();c.head='e'*40
    with pytest.raises(ValueError): publish_selected(c,report(),['aabbccddeeff'])
    assert not c.posts
    for ids in ([], ['unknown']):
        with pytest.raises(ValueError): publish_selected(PublishClient(),report(),ids)
    r=report();r.findings[0].verification_status='unverified'
    with pytest.raises(ValueError): publish_selected(PublishClient(),r,['aabbccddeeff'])


def test_repeat_publication_is_skipped():
    c=PublishClient()
    c.reviews=[{'body':'<!-- ai-review:cccccccccccccccccccc:aabbccddeeff -->', 'commit_id':'a'*40, 'user':{'login':'github-actions[bot]','type':'Bot'}}]
    assert publish_selected(c,report(),['aabbccddeeff']).status=='skipped'
    assert not c.posts


def test_artifact_provenance_and_schema():
    c=PublishClient()
    assert load_verified_report(c,'me/demo','42','.github/workflows/analyze.yml').head_sha=='a'*40
    with pytest.raises(ValueError): load_verified_report(c,'me/demo','42','.github/workflows/evil.yml')


def test_archive_traversal_is_rejected():
    c=PublishClient()
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z: z.writestr('../report.json',report().to_json())
    c.download_artifact=lambda _:buf.getvalue()
    with pytest.raises(ValueError): load_verified_report(c,'me/demo','42','.github/workflows/analyze.yml')


def test_ambiguous_post_checks_reviews_before_returning():
    c=PublishClient()
    def write(method,path,data):
        c.reviews.append({'id':99,'body':data['body'],'commit_id':'a'*40,'user':{'login':'github-actions[bot]','type':'Bot'}})
        raise ApiError(0)
    c.request=write
    assert publish_selected(c,report(),['aabbccddeeff']).status=='posted'


def test_foreign_review_marker_cannot_suppress_publication():
    c=PublishClient()
    c.reviews=[{'body':'<!-- ai-review:cccccccccccccccccccc:aabbccddeeff -->',
        'commit_id':'a'*40,'user':{'login':'unrelated-user','type':'User'}}]
    assert publish_selected(c,report(),['aabbccddeeff']).status=='posted'


def test_base_side_evidence_goes_into_review_body():
    c=PublishClient();r=report()
    f=r.findings[0];f.source='base';f.inline_eligible=False
    f.evidence[0].source='base'
    c.pages=lambda path: [] if path.endswith('/reviews') else [{'filename':'app.py','status':'modified','patch':'@@ -1,2 +1 @@\n-x=1\n print(1)'}]
    result=publish_selected(c,r,[f.id])
    assert result.status=='posted'
    assert not c.posts[0].get('comments')
    assert 'app.py:1' in c.posts[0]['body']


def test_pr_target_run_uses_base_revision_not_pr_head_as_reviewer_identity():
    c=PublishClient()
    original=c.get
    def get(path):
        if path.endswith('/actions/runs/42'):
            return {'id':42,'event':'pull_request_target','status':'completed','conclusion':'success',
                'head_sha':'a'*40,'head_branch':'demo/review-sample','path':'.github/workflows/analyze.yml',
                'repository':{'full_name':'me/demo'},
                'pull_requests':[{'number':1,'base':{'ref':'main','sha':'d'*40},'head':{'sha':'a'*40}}],
                'referenced_workflows':[{'path':'me/demo/.github/workflows/review-job.yml@'+'d'*40,
                    'sha':'d'*40,'ref':'refs/heads/main'}]}
        return original(path)
    c.get=get
    assert load_verified_report(c,'me/demo','42','.github/workflows/analyze.yml').reviewer_sha=='d'*40


def test_run_pr_base_can_be_older_than_the_trusted_worker_revision():
    c=PublishClient()
    original=c.get
    def get(path):
        value=original(path)
        if path.endswith('/actions/runs/42'):
            value['pull_requests'][0]['base']['sha']='b'*40
        return value
    c.get=get
    assert load_verified_report(c,'me/demo','42','.github/workflows/analyze.yml').reviewer_sha=='d'*40
