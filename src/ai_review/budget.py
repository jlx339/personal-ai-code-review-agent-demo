"""Single request counter shared by specialists, repairs, retries, and verifier."""
import time


class BudgetExceeded(RuntimeError):
    pass


class RequestBudget:
    def __init__(self,settings,clock=time.monotonic,sleeper=time.sleep):
        self.settings,self.clock,self.sleeper=settings,clock,sleeper
        self.calls=0
        self.last=None
        self.usage=[]

    def admit(self):
        if self.calls>=self.settings.max_requests:
            raise BudgetExceeded('Model request budget exhausted')
        now=self.clock()
        if self.last is not None:
            self.sleeper(max(0,self.settings.request_interval-(now-self.last)))
        self.last=self.clock()
        self.calls+=1

    def summary(self):
        def total(key):
            values=[x.get(key) for x in self.usage]
            return sum(values) if values and all(v is not None for v in values) and len(values)==self.calls else None
        return dict(requests=self.calls,input_tokens=total('input_tokens'),output_tokens=total('output_tokens'))
