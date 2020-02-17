.. past-mtl-monitors documentation master file, created by
   sphinx-quickstart on Sat Feb 15 20:50:58 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

past-mtl-monitors
=================

.. toctree::
   :maxdepth: 2
   :caption: Contents:

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


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
