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
        self.model_last={}
        self.model_calls={}

    def admit(self,model=None,interval=None,reserve=0):
        if type(reserve) is not int or not 0<=reserve<=self.settings.max_requests:
            raise ValueError('Invalid request reservation')
        if self.calls>=self.settings.max_requests-reserve:
            raise BudgetExceeded('Model request budget reserved for verification' if reserve else 'Model request budget exhausted')
        now=self.clock()
        delay=max(0,self.settings.request_interval-(now-self.last)) if self.last is not None else 0
        if model in self.model_last:
            delay=max(delay,(interval or self.settings.request_interval)-(now-self.model_last[model]))
        if delay:
            self.sleeper(delay)
        self.last=self.clock()
        if model:
            self.model_last[model]=self.last
            self.model_calls[model]=self.model_calls.get(model,0)+1
        self.calls+=1

    def summary(self):
        def total(key):
            values=[x.get(key) for x in self.usage]
            return sum(values) if values and all(v is not None for v in values) and len(values)==self.calls else None
        return dict(requests=self.calls,input_tokens=total('input_tokens'),output_tokens=total('output_tokens'),
            model_requests=dict(self.model_calls))
