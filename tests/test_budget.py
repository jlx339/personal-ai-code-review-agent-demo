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
