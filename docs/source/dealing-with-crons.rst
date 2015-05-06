Dealing with Tryton Crons
=========================

.. _accessing-crons:

Accessing Crons
---------------

| ``Menu: Administration > Scheduler > Scheduled Actions``

    .. image:: images/crons.png
        :width: 900

The following fields in a Cron decide when the cron runs and these can be
modified as per your need.

    .. image:: images/cron.png
        :width: 900

* **Interval Number and Interval Unit:** These fields together make up the
  interval duration of this cron. By default, it is set to `1 Day`.
  This means that the cron runs once in a day. You could increase or
  decrease the frequency by changing `Interval Number`, `Interval Unit`.

* **Next Call:** Indicates the date and time in which the cron will run
  the next time. You could change this time if you want to prepone or delay
  the execution of cron.
