Configuring Prestashop settings
===============================

The module should be configured with the URL of the Prestashop
instance. A web services authentication key should also be provided.

.. _configure-prestashop-account:

Configure Prestashop account
----------------------------

.. _create-webservices-key:

Create Webservices Key
----------------------

The web services key can be obtained/created from the prestashop admin
panel.

1. Login to the admin panel

    .. image:: images/prestashop-admin.png
        :width: 900

2. Go to webservices configuration via Advanced parameters

    .. image:: images/webservices-menu.png
        :width: 900

3. A new key can be generated as shown below:

   | ``Step 1``

    .. image:: images/add-new-key.png
        :width: 900

   | ``Step 2``

    .. image:: images/create-new-key.png
        :width: 900

.. tip:: 

   Generate a random key for better security, instead of typing a key
   by yourself.

4. Make sure you set the required permissions for this key to access
   appropriate records.

.. _configure-settings-tryton:

Configure Settings in Tryton
----------------------------

| ``Menu: Sale > Configuration > Prestashop Sites``

    .. image:: images/tryton-new-site.png
        :width: 900

.. autoclass:: prestashop.prestashop.Site

.. autoattribute:: prestashop.prestashop.Site.url
.. autoattribute:: prestashop.prestashop.Site.key
.. autoattribute:: prestashop.prestashop.Site.company
.. autoattribute:: prestashop.prestashop.Site.last_order_import_time
.. autoattribute:: prestashop.prestashop.Site.last_order_export_time
.. autoattribute:: prestashop.prestashop.Site.default_account_expense
.. autoattribute:: prestashop.prestashop.Site.default_account_revenue
.. autoattribute:: prestashop.prestashop.Site.default_warehouse
.. autoattribute:: prestashop.prestashop.Site.timezone

.. tip::

  Click `Test Connection` button to make sure the url and key
  entered are correct and are able to access the prestashop instance.

.. tip::

  `Last order import time` indicates the last time at which the orders were
  last imported from Prestashop to Tryton.

.. tip::

  `Last order export time` indicates the last time at which the orders were
  last exported from Tryton to Prestashop.

.. _prestashop-crons:

Cron for importing orders from Prestashop
-----------------------------------------

:ref:`Learn how to access and deal with crons. <accessing-crons>`

There are two crons from managing import/export from/to prestashop.

    .. image:: images/crons.png
        :width: 900

+-----------------------------------+---------------------------------------+
|               Name                |               Function                |
+===================================+=======================================+
| :ref:`Import Prestashop Orders    | Periodically imports orders from      |
| <import-orders>`                  | prestashop and creates sale orders    |
|                                   | in Tryton.                            |
+-----------------------------------+---------------------------------------+
| :ref:`Export Prestashop Orders'   | Periodically exports status for sales |
| Status <export-orders>`           | which were imported by the first cron.|
+-----------------------------------+---------------------------------------+

.. tip::

  You need not change the time here to make a quick manual import. You could go
  back into :ref:`configuration <configure-prestashop-account>` and click on the
  Import button instead. Same concept applies for export as well.

.. tip::

  If the time of import/export just does not seem right to you, check your 
  timezone in the preferences. Tryton displays times in the timezone set in 
  the preferences of the user.
