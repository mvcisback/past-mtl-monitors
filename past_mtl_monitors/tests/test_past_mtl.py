import hypothesis.strategies as st
import pytest
from hypothesis import given

from past_mtl_monitors import atom


@given(st.lists(st.booleans(), min_size=1))
def test_atom(vals):
    monitor = atom('x').monitor()
    for i, val in enumerate(vals):
        assert monitor.send((i, {'x': val})) == val

    with pytest.raises(AssertionError):
        monitor.send((0, {'x': val}))


@given(st.lists(st.tuples(st.booleans(), st.booleans()), min_size=1))
def test_prop_logic(vals):
    x, y = map(atom, ['x','y'])
    x_and_y = (x & y).monitor()
    x_or_y = (x | y).monitor()
    not_x = (~x).monitor()

    vals = [{'x': x, 'y': y} for x, y in vals]

    for i, val in enumerate(vals):
        assert x_and_y.send((i, val)) == val['x'] & val['y']
        assert x_or_y.send((i, val)) == val['x'] | val['y']
        assert not_x.send((i, val)) == ~val['x']


@given(st.lists(st.booleans(), min_size=1))
def test_hist_once_no_horizon(vals):
    x = atom('x')
    hx = x.hist().monitor()
    ox = x.once().monitor()
    vals = [{'x': x} for x in vals]

    prevh, prevo = True, False
    for i, val in enumerate(vals):
        prevh, prevo = (val['x'] & prevh), (val['x'] | prevo)
        assert hx.send((i, val)) == prevo
        assert hx.send((i, val)) == prevh

