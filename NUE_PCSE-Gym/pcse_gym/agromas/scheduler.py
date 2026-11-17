"""One shared execution-day DVS scheduler for modular and single-agent policies."""
from datetime import timedelta
import copy
import math


class ThreeStageScheduler:
    windows = ((.20,.55),(.55,.82),(.82,1.00))

    def __init__(self, budget, initial_base_n=0., min_days=14):
        if not math.isfinite(budget) or not 0 <= initial_base_n <= budget or min_days < 14:
            raise ValueError('Invalid seasonal fertilizer budget or spacing')
        self.budget=float(budget)
        self.initial_base_n=float(initial_base_n)
        self.min_days=min_days
        self.reset()

    def reset(self):
        self.cumulative=self.initial_base_n
        self.completed=set()
        self.last_positive=None
        self.last_check=None
        self.events=[]

    def eligible(self, day, dvs):
        if not math.isfinite(dvs) or not -1 <= dvs <= 3:
            raise ValueError('Invalid DVS')
        if self.last_check is not None and day < self.last_check:
            raise ValueError('Non-monotonic execution date')
        self.last_check=day
        for i,(lo,hi) in enumerate(self.windows):
            if i not in self.completed and (dvs>hi if i==2 else dvs>=hi):
                self.completed.add(i)
                self.events.append(dict(stage=i+1,date=day.isoformat(),dose=0.,reason='missed_window'))
        for i,(lo,hi) in enumerate(self.windows):
            if i not in self.completed and lo <= dvs <= hi:
                if self.last_positive is not None and day-self.last_positive < timedelta(days=self.min_days):
                    return None
                return i+1
        return None

    def preview(self, execution_day, observed_dvs):
        """Non-mutating pre-action check using the planned physical execution date."""
        probe=copy.copy(self)
        probe.completed=set(self.completed)
        probe.events=list(self.events)
        return probe.eligible(execution_day,observed_dvs)

    def execute(self, day, dvs, dose, expected_stage=None):
        if not math.isfinite(dose) or dose<0:
            raise ValueError('Invalid dose')
        stage=self.eligible(day,dvs)
        if stage is None or (expected_stage is not None and stage != expected_stage):
            return 0.
        if dose > self.budget-self.cumulative+1e-8:
            raise ValueError('Dose exceeds remaining budget')
        self.completed.add(stage-1)
        self.cumulative+=dose
        if dose>0:
            self.last_positive=day
        self.events.append(dict(stage=stage,date=day.isoformat(),dose=float(dose),reason='chosen'))
        return float(dose)
