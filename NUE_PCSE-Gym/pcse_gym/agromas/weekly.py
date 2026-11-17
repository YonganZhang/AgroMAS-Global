"""A weekly observation/action interval with action on its FIRST physical day.

A decision based on the current observation must not wait an additional week
before its execution guard. All arms share this exact next-day cadence. Native
PCSE integration/rate equations are unchanged; seven daily steps still advance.
"""
def advance_week(engine,dose):
    guard=getattr(engine,'_action_guard',None)
    if guard is None:raise ValueError('Explicit actual-date action guard required')
    due=True
    def gate(action,dvs,day):
        return guard(action,dvs,day) if due else 0.
    engine._action_guard=gate
    try:
        engine.run(days=1,action=dose)
        executed=float(engine._guard_executed_action)
        execution_date=engine.day.isoformat() if executed>0 else None
        due=False
        if not engine.terminated:engine.run(days=6,action=0)
        engine._guard_executed_action=executed
        return execution_date
    finally:
        engine._action_guard=guard
