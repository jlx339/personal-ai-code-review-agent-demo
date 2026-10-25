import pytest
from ai_review.model import ReviewModel, ModelError
from ai_review.budget import RequestBudget
from ai_review.config import Settings


def model(transport):
    return ReviewModel('private-key', Settings(), RequestBudget(Settings(),clock=lambda:0,sleeper=lambda _:None),transport)


def test_model_uses_native_tool_calls_and_output_cap():
    def transport(body):
        assert body['generationConfig']['maxOutputTokens'] == 4000
        assert body['tools'][0]['functionDeclarations'][0]['name'] == 'read_source'
        return 200, {'candidates':[{'content':{'role':'model','parts':[{'functionCall':{'name':'read_source','args':{'path':'a.py'}},'thoughtSignature':'opaque'}]}}],'usageMetadata':{'promptTokenCount':12,'candidatesTokenCount':5}}, {}
    result=model(transport).invoke([],tools=[{'name':'read_source','parameters':{'type':'object','properties':{}}}])
    assert result.message['parts'][0]['thoughtSignature'] == 'opaque'
    assert result.tool_calls[0]['name']=='read_source'
    assert result.usage['input_tokens']==12


def test_daily_quota_stops_without_retries_and_secrets_stay_hidden():
    m=model(lambda _: (429, {'error':{'message':'private-key daily limit exceeded'}}, {}))
    with pytest.raises(ModelError) as exc: m.invoke([])
    assert m.budget.calls == 1
    assert 'private-key' not in str(exc.value)


def test_transient_failure_retries_twice_and_stops():
    m=model(lambda _: (503,{},{}))
    with pytest.raises(ModelError): m.invoke([])
    assert m.budget.calls == 3


def test_auth_errors_do_not_retry():
    m=model(lambda _: (403,{},{}))
    with pytest.raises(ModelError): m.invoke([])
    assert m.budget.calls == 1


def test_missing_usage_is_unknown_and_text_is_extracted():
    m=model(lambda _: (200,{'candidates':[{'content':{'parts':[{'text':'hello'}]}}]},{}))
    r=m.invoke([])
    assert r.text=='hello' and r.usage['input_tokens'] is None


@pytest.mark.parametrize('envelope',[
    {'candidates':[{'content':{'parts':[None]}}]},
    {'candidates':[{'content':{'parts':[{'functionCall':{'name':'read_source','args':None}}]}}]},
    {'candidates':[{'content':{'parts':[{'text':'ok'}]}}],'usageMetadata':{'promptTokenCount':'oops'}},
])
def test_malformed_envelopes_become_model_error(envelope):
    m=model(lambda _: (200,envelope,{}))
    with pytest.raises(ModelError): m.invoke([])


def test_terminal_credential_error_stops_later_specialists_requests():
    m=model(lambda _: (403,{},{}))
    with pytest.raises(ModelError): m.invoke([])
    with pytest.raises(ModelError): m.invoke([])
    assert m.budget.calls==1


def test_reasoning_model_has_supported_thinking_level_and_shares_request_budget():
    seen=[]
    def transport(body):
        seen.append(body['generationConfig'])
        return 200,{'candidates':[{'content':{'parts':[{'text':'{}'}]}}]},{}
    m=model(transport);strong=m.for_model('gemini-3.8-flash')
    m.invoke([]);strong.invoke([])
    assert seen[0]['thinkingConfig']['thinkingLevel']=='MINIMAL'
    assert seen[1]['thinkingConfig']['thinkingLevel']=='LOW'
    assert seen[1]['maxOutputTokens']==8000
    assert m.budget.calls==2
    assert m.budget.summary()['model_requests']=={'gemini-3.5-flash-lite':1,'gemini-3.8-flash':1}


def test_model_routing_refuses_non_allowlisted_models():
    with pytest.raises(ValueError): model(lambda _:None).for_model('paid-arbitrary-model')


def test_previous_flash_reasoning_model_uses_low_thinking():
    def transport(body):
        assert body['generationConfig']['thinkingConfig']['thinkingLevel']=='LOW'
        return 200,{'candidates':[{'content':{'parts':[{'text':'{}'}]}}]},{}
    m=model(transport).for_model('gemini-3.6-flash')
    assert m.invoke([]).text=='{}'


def test_exhausted_provider_retries_stop_later_calls_in_the_same_run():
    m=model(lambda _: (503,{},{}))
    with pytest.raises(ModelError): m.invoke([])
    with pytest.raises(ModelError): m.invoke([])
    assert m.budget.calls==3


def test_same_model_can_reason_without_changing_ordinary_specialist_thinking():
    configs=[]
    def transport(body):
        configs.append(body['generationConfig'])
        return 200,{'candidates':[{'content':{'parts':[{'text':'{}'}]}}]},{}
    m=model(transport);reasoning=m.for_model('gemini-3.5-flash-lite',thinking_level='LOW')
    m.invoke([]);reasoning.invoke([])
    assert configs[0]['thinkingConfig']['thinkingLevel']=='MINIMAL'
    assert configs[1]['thinkingConfig']['thinkingLevel']=='LOW'
    assert configs[1]['maxOutputTokens']==8000
    assert m.budget.calls==2


def test_unsupported_minimal_thinking_is_rejected_before_flash38_request():
    with pytest.raises(ValueError): model(lambda _:None).for_model('gemini-3.8-flash',thinking_level='MINIMAL')
