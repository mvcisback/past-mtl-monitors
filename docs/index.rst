.. past-mtl-monitors documentation master file, created by
   sphinx-quickstart on Sat Feb 15 20:50:58 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

past-mtl-monitors
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

A library for creating past metric temporal logic monitors.


Basic Usage::

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

Installation
------------

If you just need to use `past-mtl-monitors`, you can just run::

 $ pip install past-mtl-monitors

For developers, note that this project uses the
[poetry](https://poetry.eustace.io/) python package/dependency
management tool. Please familarize yourself with it and then
run::

 $ poetry install

API
---

The past-mtl-monitor API centers around the MonitorFactory type with
atom as the primary entrypoint into the API.

.. autofunction:: past_mtl_monitors.atom

.. autoclass:: past_mtl_monitors.monitors.MonitorFact
   .. automethod:: past_mtl_monitors.monitors.MonitorFact.__and__
   .. automethod:: past_mtl_monitors.monitors.MonitorFact.__or__
   .. automethod:: past_mtl_monitors.monitors.MonitorFact.hist
   .. automethod:: past_mtl_monitors.monitors.MonitorFact.once
   .. automethod:: past_mtl_monitors.monitors.MonitorFact.since


Extending
---------

The `MonitorFact` type is a simple wrapper around python
co-routines. This makes is easy to write your own monitors that
integrate well with the `past-mtl-monitor` library. For example:
consider the following monitor which aggregates the child's monitor's
results::

  from past_mtl_monitors import MonitorFact


  def aggregate_monitor(child_factory):
      """Sums the child values using piecewise constant interpolation."""

      def avg_factory():
          child_monitor = child_factory.monitor()
          payload = (time, _) = yield    # Get initial payload.
                                         # payload = (time, child input).

          total = prev_val = 0
          while True:
              child_val = child_monitor.send(payload)

              prev_time = time
              payload = (time, _) = yield total
              
              total += prev_val * (time - prev_time)
              prev_val = child_val

      return MonitorFact(avg)


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
