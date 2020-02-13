from __future__ import annotations

from typing import Callable, Coroutine, List, Tuple, Union, Mapping, NamedTuple

import attr
from discrete_signals import signal


Time = float
Robustness = Union[float, bool]
Data = Mapping[str, Robustness]
Monitor = Coroutine[Tuple[Time, Data], Robustness, Robustness]
Merger = Callable[[Time, List[Robustness]], Robustness]
oo = float('inf')


def apply(facts: List[MonitorFact], op: Merger) -> MonitorFact:
    """Create monitor from binary operator."""
    def factory():
        monitors = [f.monitor() for f in facts]
        payload = yield
        while True:
            vals = [m.send(payload) for m in monitors]
            payload = yield op(payload[0], vals)
    return MonitorFact(factory)


@attr.s(auto_attribs=True, frozen=True)
class MonitorFact:
    factory: Callable[[], Monitor]

    def monitor(self) -> Monitor:
        _monitor = self.factory()
        next(_monitor)
        return _monitor

    def __and__(self, other: MonitorFact) -> MonitorFact:
        return apply([self, other], lambda _, xs: min(xs))

    def __or__(self, other: MonitorFact) -> MonitorFact:
        return apply([self, other], lambda _, xs: max(xs))

    def __invert__(self) -> MonitorFact:
        def op(_, vals):
            assert len(vals) == 1
            val = vals[0]
            return ~val if isinstance(val, bool) else -val
        return apply([self], op)

    def hist(self, start=0, end=oo) -> MonitorFact:
        """
        Monitors if the parent monitor was historically true over the
        interval.
        """
        assert start < end
        def create_factory():
            if start == 0 and end == oo:
                prev = True
                def op(_, val):
                    assert len(val) == 1
                    nonlocal prev
                    prev = min(prev, val[0])
                    return prev
            else:
                buff = signal([], start=0, end=0)
                def op(time, val):
                    nonlocal buff
                    buff @= signal([(time, val)], start=time, end=time+1)
                    buff = buff[time - start:time - end]
                    return min(v[None] for v in buff.values())

            return apply([self], op)
        return MonitorFact(create_factory().factory)


    def once(self, start=0, end=oo) -> MonitorFact:
        return ~((~self).hist(start, end))

    def vyest(self, other: MonitorFact) -> MonitorFact:
        pass

    def since(self, other: MonitorFact) -> MonitorFact:
        pass

def atom(var):
    def factory():
        time, data = yield
        while True:
            assert var in data, f"Variable {var} is missing from {data}."
            time2, data = yield data[var]
            assert time2 > time, "Time must be ordered."
            time = time2

    return MonitorFact(factory)
