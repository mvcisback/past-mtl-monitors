from __future__ import annotations

from collections import deque
from typing import Callable, Coroutine, List, Tuple, Union, Mapping, NamedTuple
from typing import Deque

import attr

Time = float
Robustness = Union[float, bool]

Data = Mapping[str, Robustness]
Monitor = Coroutine[Tuple[Time, Data], Robustness, Robustness]
Merger = Callable[[Time, List[Robustness]], Robustness]

Factory = Callable[[], Monitor]

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


@attr.s(auto_attribs=True, frozen=True, cmp=False)
class MonitorFact:
    _factory: Factory

    def monitor(self) -> Monitor:
        _monitor = self._factory()
        next(_monitor)
        return _monitor

    def __and__(self, other: MonitorFact) -> MonitorFact:
        """
        Combines child monitors using logical AND or MIN depending
        of Boolean or Real values.
        """
        return apply([self, other], lambda _, xs: min(xs))

    def __or__(self, other: MonitorFact) -> MonitorFact:
        """
        Combines child monitors using logical OR or MAX depending
        of Boolean or Real values.
        """
        return apply([self, other], lambda _, xs: max(xs))

    def __invert__(self) -> MonitorFact:
        """Inverts result of child monitors."""
        def op(_, vals):
            assert len(vals) == 1
            val = vals[0]
            return not val if isinstance(val, bool) else -val
        return apply([self], op)

    def hist(self, start=0, end=oo) -> MonitorFact:
        """
        Monitors if the child monitor was historically true over the
        interval.
        """
        raise NotImplementedError

    def once(self, start=0, end=oo) -> MonitorFact:
        """
        Monitors if the child monitor was once true in the
        interval.
        """
        return ~((~self).hist(start, end))

    def since(self, other: MonitorFact) -> MonitorFact:
        """
        Monitors if the self's monitor has held since the
        other was last true (non-inclusive).
        """
        raise NotImplementedError


def atom(var: str) -> MonitorFact:
    """Main entry point to monitor construction DSL.

    Takes a variable name and produces a monitor factory.
    """
    def factory():
        time, data = yield
        while True:
            assert var in data, f"Variable {var} is missing from {data}."
            time2, data = yield data[var]
            assert time2 > time, "Time must be ordered."
            time = time2

    return MonitorFact(factory)


def to_itvl(time, start, end):
    raise NotImplementedError


@attr.s(frozen=True, auto_attribs=True)
class MaxIntervalQueue:
    queue: Deque[Tuple[Time, Robustness]] = attr.ib(factory=deque)

    def peak(self) -> Robustness:
        return queue[0]

    def pop(self) -> Robustness:
        return queue.pop()

    def push(self, val: Robustness):
        queue.appendleft(val)

        
def _hist_op_factory(start, end):
    def create_op():
        queue = MaxIntervalQueue()

        def op(time, val):
            nonlocal queue

            # left, right = to_itvl(time, start, end)
            # tree.addi(left, right, val)


    return create_op
