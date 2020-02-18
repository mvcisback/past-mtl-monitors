from __future__ import annotations

from typing import Callable, Coroutine, List, Tuple, Union, Mapping
from intervaltree import IntervalTree

import attr

Time = float
Robustness = Union[float]

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
        Combines child monitors using min. If values are {1, -1} for True
        and False resp., then this corresponds to logical And.
        """
        return apply([self, other], lambda _, xs: min(xs))

    def __or__(self, other: MonitorFact) -> MonitorFact:
        """
        Combines child monitors using min. If values are {1, -1} for True
        and False resp., then this corresponds to logical Or.
        """
        return apply([self, other], lambda _, xs: max(xs))

    def __neg__(self) -> MonitorFact:
        """Negates result of child monitors."""
        def op(_, vals):
            assert len(vals) == 1
            return -vals[0]

        return apply([self], op)

    def __invert__(self) -> MonitorFact:
        """Negates result of child monitors."""
        return -self

    def implies(self, other: MonitorFact) -> MonitorFact:
        """Monitors if child monitor self implies child monitor other."""
        return (~self) | other

    def __eq__(self, other: MonitorFact) -> MonitorFact:
        """Monitors if child monitors self and other return same values."""
        return self.implies(other) & other.implies(self)

    def hist(self, start=0, end=oo) -> MonitorFact:
        """
        Monitors if the child monitor was historically true over the
        interval [t-end, t-start] where t is the current time.
        """
        def factory():
            window = MinSlidingWindow(itvl=(start, end))
            child_monitor = self.monitor()

            time, child_input = yield
            while True:
                val = child_monitor.send((time, child_input))
                time, child_input = yield window.update(time, val)

        return MonitorFact(factory)

    def once(self, start=0, end=oo) -> MonitorFact:
        """
        Monitors if the child monitor was once true in the
        interval [t-end, t-start] where t is the current time.
        """
        return ~((~self).hist(start, end))

    def since(self, other: MonitorFact) -> MonitorFact:
        """
        Monitors the minimum value since the last time
        other's value was greater than 0.

        Note: other's value is assumed to have been previously
        greater than zero when the monitor starts.
        """
        def factory():
            left, right = self.monitor(), other.monitor()

            closest = oo
            payload = yield
            while True:
                val_l, val_r = left.send(payload), right.send(payload)
                if val_r > 0:
                    closest = oo
                elif val_l < closest:
                    closest = val_l

                payload = yield closest

        return MonitorFact(factory)


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
    time: Time = -oo

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
