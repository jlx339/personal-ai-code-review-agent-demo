import pytest
from ai_review.budget import RequestBudget, BudgetExceeded
from ai_review.config import Settings


def test_budget_spaces_requests_and_refuses_thirteenth():
    now=[0.0]
    def sleep(seconds): now[0]+=seconds
    b=RequestBudget(Settings(),clock=lambda:now[0],sleeper=sleep)
    for _ in range(12): b.admit()
    assert now[0] == 55
    with pytest.raises(BudgetExceeded): b.admit()
    assert b.calls == 12


def test_model_specific_spacing_survives_calls_to_another_model():
    now=[0.0]
    b=RequestBudget(Settings(),clock=lambda:now[0],sleeper=lambda seconds:now.__setitem__(0,now[0]+seconds))
    b.admit('strong',12.5)
    b.admit('light',5)
    b.admit('strong',12.5)
    assert now[0]==12.5
    assert b.calls==3


def test_specialists_cannot_consume_reserved_verification_requests():
    b=RequestBudget(Settings(),clock=lambda:0,sleeper=lambda _:None)
    for _ in range(9): b.admit(reserve=3)
    with pytest.raises(BudgetExceeded): b.admit(reserve=3)
    assert b.calls==9
    for _ in range(3): b.admit()
    assert b.calls==12
