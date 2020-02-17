import hypothesis.strategies as st
import pytest
from hypothesis import given

from past_mtl_monitors import atom
from past_mtl_monitors.monitors import MinSlidingWindow


@given(st.lists(st.booleans(), min_size=1))
def test_atom(vals):
    monitor = atom('x').monitor()
    for i, val in enumerate(vals):
        assert monitor.send((i, {'x': val})) == val

    with pytest.raises(AssertionError):
        monitor.send((0, {'x': val}))


@given(st.lists(st.booleans(), min_size=1))
def test_neg(vals):
    x = atom('x')
    monitor = (~x).monitor()
    monitor2 = (~(~x)).monitor()

    for i, val in enumerate(vals):
        assert monitor.send((i, {'x': val})) == (not val)
        assert monitor2.send((i, {'x': val})) == val



@given(st.lists(st.tuples(st.booleans(), st.booleans()), min_size=1))
def test_and(vals):
    x, y = map(atom, ['x','y'])
    vals = [{'x': x, 'y': y} for x, y in vals]

    x_and_y = (x & y).monitor()
    for i, val in enumerate(vals):
        assert x_and_y.send((i, val)) == val['x'] & val['y']


@given(st.lists(st.tuples(st.booleans(), st.booleans()), min_size=1))
def test_or(vals):
    x, y = map(atom, ['x','y'])
    vals = [{'x': x, 'y': y} for x, y in vals]

    x_or_y = (x | y).monitor()
    x_or_y2 = (~(~x & ~y)).monitor()

    for i, val in enumerate(vals):
        assert x_or_y.send((i, val)) == x_or_y2.send((i, val))


def test_min_window_inf():
    window = MinSlidingWindow()

    assert len(window.tree.all_intervals) == 1
    assert window.time == 0
    assert window.min() == float('inf')

    window.update(1, 2)
    assert len(window.tree.all_intervals) == 1
    assert window.time == 1
    assert window.min() == 2

    window2 = MinSlidingWindow(itvl=(2, float('inf')))

    assert len(window.tree.all_intervals) == 1
    assert window2.time == 0
    assert window2.min() == float('inf')

    window2.update(1, 2)
    assert len(window2.tree.all_intervals) == 2
    assert window2.time == 1
    assert window2.min() == float('inf')

    window2.update(3, 5)
    assert window2.min() == 2



@given(st.lists(st.booleans(), min_size=1))
def test_hist_once_no_horizon(vals):
    hx = atom('x').hist().monitor()
    ox = atom('x').once().monitor()
    vals = [{'x': x} for x in vals]

    prevh, prevo = True, False
    for i, val in enumerate(vals):
        prevh, prevo = (val['x'] & prevh), (val['x'] | prevo)
        assert hx.send((i, val)) == prevh
        assert ox.send((i, val)) == prevo

