Past MTL Monitors
=================
A library for creating past metric temporal logic monitors.

[![Build Status](https://cloud.drone.io/api/badges/mvcisback/past-mtl-monitors/status.svg)](https://cloud.drone.io/mvcisback/past-mtl-monitors)
[![Documentation Status](https://readthedocs.org/projects/past-mtl-monitors/badge/?version=latest)](https://past-mtl-monitors.readthedocs.io/en/latest/?badge=latest)
[![codecov](https://codecov.io/gh/mvcisback/past-mtl-monitors/branch/master/graph/badge.svg)](https://codecov.io/gh/mvcisback/past-mtl-monitors)
[![PyPI version](https://badge.fury.io/py/past-mtl-monitors.svg)](https://badge.fury.io/py/past-mtl-monitors)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)


<!-- markdown-toc start - Don't edit this section. Run M-x markdown-toc-generate-toc again -->
**Table of Contents**

- [Past MTL Monitors](#past-mtl-monitors)
- [Installation](#installation)
- [Usage](#usage)

<!-- markdown-toc end -->


# Installation

If you just need to use `past-mtl-monitors`, you can just run:

`$ pip install past-mtl-monitors`

For developers, note that this project uses the
[poetry](https://poetry.eustace.io/) python package/dependency
management tool. Please familarize yourself with it and then
run:

`$ poetry install`

# Usage

The primary entry point to the `past-mtl-monitors` package is the
`atom` function. This exposes a monitor factory which can be combined
with other monitor factories to create complex property monitors.

Under the hood, these monitor factories are just wrappers around
python coroutines that expect a `(time, val)` pair, where time is a
`float` and `val` is a mapping from strings to robustness values
(`float`).

**Note** `past-mtl-monitors` only implements a quantitative semantics
where a value greater than 0 implies sat and a value less than 0
implies unsat.

Thus if one would like to use Boolean semantics, use `1` for `True` and
`-1` for `False`.

```python
from past_mtl_monitors import atom

x, y, z = atom('x'), atom('y'), atom('z')

# Monitor that historically, x has been equal to y.
monitor = (x == y).hist().monitor()

#                    time         values
assert monitor.send((0    , {'x': 1, 'y': 1}))  ==  1   # sat
assert monitor.send((1.1  , {'x': 1, 'y': -1})) == -1   # unsat
assert monitor.send((1.5  , {'x': 1, 'y': 1}))  == -1   # unsat

monitor2 = x.once().monitor()  # Monitor's x's maximum value.
assert monitor2.send((0 , {'x': -10, 'y': 1})) == -10
assert monitor2.send((0 , {'x': 100, 'y': 2})) == 100
assert monitor2.send((0 , {'x': -100, 'y': -1})) == 100

# Monitor that x & y have been true since the last
# time that z held for 3 time units.
monitor3 = (x & y).since(z.hist(0, 3)).monitor()
```
