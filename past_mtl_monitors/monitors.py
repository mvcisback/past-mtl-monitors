from __future__ import annotations

from typing import Callable, Coroutine, List, Tuple, Union, Mapping
from intervaltree import IntervalTree

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


def _init_tree():
    tree = IntervalTree()
    tree.addi(-oo, oo, oo)  # Starts off with -oo signal.
    return tree


@attr.s(auto_attribs=True)
class MinSlidingWindow:
    tree: IntervalTree = attr.ib(factory=_init_tree)
    itvl: Tuple[Time, Time] = (0, oo)
    time: Time = 0

    def __getitem__(self, t: Time) -> Robustness:
        itvls = self.tree[t]
        assert len(itvls) == 1
        return list(itvls)[0].data

    def min(self) -> Robustness:
        """Returns minimum robustness at the current time."""
        return self[self.time - self.itvl[0]]

    def step(self, t: Time) -> Robustness:
        """Advances time to t."""
        self.time = t

        if self.itvl[1] != oo:
            self.tree.chop(-oo, t - self.itvl[1])
        else:
            self.tree.chop(-oo, t - self.itvl[0])


    def push(self, t: Time, val: Robustness) -> Robustness:
        """Adds (t, val) to the window without advancing time."""
        if val > self[t]:
            return
        self.tree.chop(t, oo)
        self.tree.addi(t, oo, val)

    def update(self, t: Time, val: Robustness) -> Robustness:
        """Performs three actions:
          1. Push: Adds (t, val) to window.
          2. Step: Updates time to t.
          3. Min: Returns the minimum value in the window at time t.
        """
        assert t > self.time
        self.push(t, val)
        self.step(t)
        return self.min()

        
def _hist_op_factory(start, end):
    def create_op():
        window = MinSlidingWindow()

        def op(time, val):
            nonlocal window
            return window.update(time, val)

    return create_op
