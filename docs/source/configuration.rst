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

Configuring Languages and Order States
--------------------------------------

Before proceeding with the import and export of orders, the languages and
order states must be mapped.

1. Click the `Import Languages` button to import all languages from
   prestashop to tryton. The system will try to intelligently match the
   languages on Tryton with the languages imported. Although it can always be
   configured as per the needs of the user.

.. note::
   Prestashop stores language codes in two formats, i.e., ISO 639‑1 2
   character codes and IETF language tags where the ISO 639‑1 2 character
   code can be combined with the ISO 3166-1 country 2 character code via
   hyphen(-). The default language codes used by prestashop does not seem
   to adhere to any of the above though. We take into consideration the
   IETF language tags based codes from prestashop and match with tryton.

   In short, the `Language Code` field on language settings for each
   language should have the value in the form
   `<2 character ISO Code>-<2 character ISO country code>`. For example,
   United States English becomes en-US and Great Britain English becomes
   en-GB. Similarly, French from France becomes fr-FR and Portuguese from
   Brazil becomes pt-BR

2. Click the `Import Order States` button to import all order states from
   prestashop to tryton. The system will map some of the default states with a
   predefined logic as explained below. Although it can always be configured as
   per the needs of the user.

+-----------------------------------+---------------------------------------+
|       Prestashop State(s)         |       Tryton State                    |
+===================================+=======================================+
|       Shipped /                   |                                       |
|       Delivered                   |       Shipment Sent                   |
+-----------------------------------+---------------------------------------+
|           Canceled                |       Sale Canceled                   |
+-----------------------------------+---------------------------------------+
|   Payment accepted /              |                                       |
|   Payment remotely accepted /     |       Sale Processing                 |
|   Preparation in progress /       |                                       |
+-----------------------------------+---------------------------------------+
|       Any other state             |       Sale Confirmed                  |
+-----------------------------------+---------------------------------------+

Understanding the Tryton States
-------------------------------

1. **Shipment Sent**: The sale in tryton will have a shipment created
   which will be completely processed and marked as sent.

2. **Sale Canceled**: Sale is canceled and cannot be processed further.

3. **Sale Processing**: The sale will have a shipment and an invoice but
   both will be left open for the user to process.

4. **Sale Confirmed**: Sale is in confirmed state with no shipment and
   invoice associated.

.. note::

  The Order States can only be imported only after languages are imported.

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
