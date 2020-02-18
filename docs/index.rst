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


Example Usage::

   from past_mtl_monitors import atom
   
   x, y = atom('x'), atom('y')
   monitor = (x & ~y.hist()).monitor()

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
=========
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

      return MonitorFact


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
