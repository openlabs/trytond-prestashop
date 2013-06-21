# -*- coding: utf-8 -*-
"""
    prestashop

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from datetime import datetime

import pytz
import requests
import pystashop
from mockstashop import MockstaShopWebservice
from trytond.model import ModelSQL, ModelView, fields
from trytond.pyson import Eval
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.wizard import Wizard, StateView, Button


__all__ = [
    'Site', 'ImportWizardView', 'ImportWizard',
    'ExportWizardView', 'ExportWizard',
    'ConnectionWizardView', 'ConnectionWizard',
]
TIMEZONES = [(x, x) for x in pytz.common_timezones]


class Site(ModelSQL, ModelView):
    "Prestashop Site"
    __name__ = 'prestashop.site'
    _rec_name = 'url'

    #: The URL of prestashop site
    url = fields.Char('URL', required=True)

    #: The webservices key for access to site
    key = fields.Char('Key', required=True)

    #: Company to which this site is linked
    company = fields.Many2One('company.company', 'Company', required=True)

    #: Last time at which the orders were imported from prestashop
    last_order_import_time = fields.DateTime('Last order import time')

    #: Last time at which the orders were exported to prestashop
    last_order_export_time = fields.DateTime('Last order export time')

    #: Used to set expense account while creating products.
    default_account_expense = fields.Property(fields.Many2One(
        'account.account', 'Account Expense', domain=[
            ('kind', '=', 'expense'),
            ('company', '=', Eval('context', {}).get('company', 0)),
        ], required=True
    ))

    #: Used to set revenue account while creating products.
    default_account_revenue = fields.Property(fields.Many2One(
        'account.account', 'Account Revenue', domain=[
            ('kind', '=', 'revenue'),
            ('company', '=', Eval('context', {}).get('company', 0)),
        ], required=True
    ))

    #: Imported Sale Orders are created in this warehouse.
    default_warehouse = fields.Many2One(
        'stock.location', 'Warehouse', domain=[('type', '=', 'warehouse')],
        required=True
    )

    #: The timezone set on prestashop site
    #: The orders imported will bear time in this timezone and that will need
    #: to be converted to UTC
    #: Also in order to determine what orders are to be imported, we need
    #: to convert UTC to this timezone to ensure correct time interval
    timezone = fields.Selection(
        TIMEZONES, 'Timezone', translate=False, required=True
    )

    #: Allowed languages to be synced for the site
    languages = fields.One2Many(
        'prestashop.site.lang', 'site', 'Languages'
    )

    #: The mapping between prestashop order states and tryton sale states
    order_states = fields.One2Many(
        'prestashop.site.order_state', 'site', 'Order States'
    )

    #: Set this to True to handle invoicing in tryton and get invoice info
    #: TODO: A provision to be implemented in future versions
    #: Also handle multiple payment methods where each will have different
    #: journal and account setups
    handle_invoice = fields.Boolean('Handle Invoicing ?')

    @classmethod
    def __setup__(cls):
        super(Site, cls).__setup__()
        cls._error_messages.update({
            'prestashop_settings_missing':
            'Prestashop webservice settings are incomplete.',
            'multiple_sites':
            'Test connection can be done for only one site at a time.',
            'wrong_url_n_key': 'Connection Failed! Please check URL and Key',
            'wrong_url': 'Connection Failed! The URL provided is wrong',
            'languages_not_imported':
            'Import the languages before importing order states',
            'order_states_not_imported': 'Import the order states before '
            'importing/exporting orders'
        })
        cls._buttons.update({
            'test_connection': {},
            'import_languages': {},
            'import_order_states': {},
            'import_orders': {},
            'export_orders': {},
        })

    def get_prestashop_client(self):
        """
        Returns an authenticated instance of the Prestashop client

        :return: Prestashop client object
        """
        if not all([self.url, self.key]):
            self.raise_user_error('prestashop_settings_missing')

        if Transaction().context.get('ps_test'):
            return MockstaShopWebservice('Some URL', 'A Key')

        return pystashop.PrestaShopWebservice(self.url, self.key)

    @classmethod
    @ModelView.button
    def import_languages(cls, sites):
        """Import Languages from remote and try to link them to tryton
        languages

        :param sites: List of sites for which the languages are to be imported
        :returns: List of languages created
        """
        SiteLanguage = Pool().get('prestashop.site.lang')

        if len(sites) != 1:
            cls.raise_user_error('multiple_sites')
        site = sites[0]

        # Set this site in context
        with Transaction().set_context(prestashop_site=site.id):

            client = site.get_prestashop_client()
            languages = client.languages.get_list(display='full')

            new_records = []
            for lang in languages:
                # If the language already exists in `Languages`, skip and do
                # not create it again
                if SiteLanguage.search_using_ps_id(lang.id.pyval):
                    continue
                new_records.append(
                    SiteLanguage.create_using_ps_data(lang)
                )

        return new_records

    @classmethod
    @ModelView.button
    def import_order_states(cls, sites):
        """Import Order States from remote and try to link them to tryton
        order states

        :returns: List of order states created
        """
        SiteOrderState = Pool().get('prestashop.site.order_state')

        if len(sites) != 1:
            cls.raise_user_error('multiple_sites')
        site = sites[0]

        # Set this site to context
        with Transaction().set_context(prestashop_site=site.id):

            # If site languages don't exist, then raise an error
            if not site.languages:
                cls.raise_user_error('languages_not_imported')

            client = site.get_prestashop_client()
            order_states = client.order_states.get_list(display='full')

            new_records = []
            for state in order_states:
                # If this order state already exists for this site, skip and do
                # not create it again
                if SiteOrderState.search_using_ps_id(state.id.pyval):
                    continue

                new_records.append(
                    SiteOrderState.create_using_ps_data(state)
                )

        return new_records

    @classmethod
    @ModelView.button_action('prestashop.wizard_prestashop_connection')
    def test_connection(cls, sites):
        """Test Prestashop connection and display appropriate message to user
        """
        if len(sites) != 1:
            cls.raise_user_error('multiple_sites')
        site = sites[0]
        try:
            client = site.get_prestashop_client()

            # Try getting the list of shops
            # If it fails with prestashop error, then raise error
            client.shops.get_list()
        except pystashop.PrestaShopWebserviceException:
            cls.raise_user_error('wrong_url_n_key')
        except (
            requests.exceptions.MissingSchema,
            requests.exceptions.ConnectionError
        ):
            cls.raise_user_error('wrong_url')

    @classmethod
    def import_orders_from_prestashop(cls, sites=None):
        """Import orders from prestashop

        :param sites: The list of sites from which the orders are to be
                      imported

        ..note:: This method is usually called by the cron
        """
        # TODO: In future it should be possible to call each site separately.
        if not sites:
            sites = cls.search([
                ('company', '=', Transaction().context.get('company'))
            ])

        for site in sites:
            site.import_orders_from_prestashop_site()

    @classmethod
    @ModelView.button_action('prestashop.wizard_prestashop_import')
    def import_orders(cls, sites=None):
        """Dummy button to fire up the wizard for import of orders

        :param sites: The list of sites from which the orders are to be
                      imported
        """
        pass

    def import_orders_from_prestashop_site(self):
        """Import orders for the current site from prestashop
        Import only those orers which are updated after the
        `last order import time` as set in the prestashop configuration

        :returns: The list of active records of sales imported
        """
        Sale = Pool().get('sale.sale')
        Site = Pool().get('prestashop.site')

        if not self.order_states:
            self.raise_user_error('order_states_not_imported')

        # Localize to the site timezone
        utc_time_now = datetime.utcnow()
        site_tz = pytz.timezone(self.timezone)
        time_now = site_tz.normalize(pytz.utc.localize(utc_time_now))
        client = self.get_prestashop_client()

        with Transaction().set_context(prestashop_site=self.id):
            if self.last_order_import_time:
                # In tryton all time stored is in UTC
                # Convert the last import time to timezone of the site
                last_order_import_time = site_tz.normalize(
                    pytz.utc.localize(self.last_order_import_time)
                )
                orders_to_import = client.orders.get_list(
                    filters={
                        'date_upd': '{0},{1}'.format(
                            last_order_import_time.strftime(
                                '%Y-%m-%d %H:%M:%S'
                            ),
                            time_now.strftime('%Y-%m-%d %H:%M:%S')
                        )
                    }, date=1, display='full'
                )
            else:
                # FIXME: This wont scale if there are thousands of orders
                orders_to_import = client.orders.get_list(display='full')

            Site.write([self], {
                'last_order_import_time': utc_time_now
            })
            sales_imported = []
            for order in orders_to_import:
                sales_imported.append(Sale.find_or_create_using_ps_data(order))

        return sales_imported

    @classmethod
    def export_orders_to_prestashop(cls, sites=None):
        """Export order status to prestashop

        :param sites: The list of sites to which the orders are to be
                      exported

        ..note:: This method is usually called by the cron
        """
        if not sites:
            sites = cls.search([
                ('company', '=', Transaction().context.get('company'))
            ])

        for site in sites:
            site.export_orders_to_prestashop_for_site()

    @classmethod
    @ModelView.button_action('prestashop.wizard_prestashop_export')
    def export_orders(cls, sites=None):
        """Dummy button to fire up the wizard for export of orders

        :param sites: The list of sites to which the orders are to be
                      exported
        """
        pass

    def export_orders_to_prestashop_site(self):
        """Export order status to prestashop current site
        Export only those orders which are modified after the
        `last order export time` as set in the prestashop configuration.

        :returns: The list of active records of sales exported
        """
        Sale = Pool().get('sale.sale')
        Site = Pool().get('prestashop.site')
        Move = Pool().get('stock.move')

        if not self.order_states:
            self.raise_user_error('order_states_not_imported')

        time_now = datetime.utcnow()

        with Transaction().set_context(prestashop_site=self.id):
            if self.last_order_export_time:
                # Sale might not get updated for state changes in the related
                # shipments.
                # So first get the moves for outgoing shipments which are \
                # executed after last import time.
                moves = Move.search([
                    ('write_date', '>=', self.last_order_export_time),
                    ('sale.prestashop_site', '=', self.id),
                    ('shipment', 'like', 'stock.shipment.out%')
                ])
                sales_to_export = Sale.search(['OR', [
                    ('write_date', '>=', self.last_order_export_time),
                    ('prestashop_site', '=', self.id),
                ], [
                    ('id', 'in', map(int, [m.sale for m in moves]))
                ]])
            else:
                sales_to_export = Sale.search([
                    ('prestashop_site', '=', self.id),
                ])

            Site.write([self], {
                'last_order_export_time': time_now
            })

            for sale in sales_to_export:
                sale.export_status_to_ps()

        return sales_to_export


class ConnectionWizardView(ModelView):
    'Prestashop Connection Wizard View'
    __name__ = 'prestashop.connection.wizard.view'


class ConnectionWizard(Wizard):
    'Prestashop Connection Wizard'
    __name__ = 'prestashop.connection.wizard'

    start = StateView(
        'prestashop.connection.wizard.view',
        'prestashop.prestashop_connection_wizard_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, data):
        """Test the connection and show the user appropriate message

        :param data: Wizard data
        """
        return {}


class ImportWizardView(ModelView):
    'Prestashop Import Wizard View'
    __name__ = 'prestashop.import.wizard.view'

    orders_imported = fields.Integer('Orders Imported', readonly=True)


class ImportWizard(Wizard):
    'Prestashop Import Wizard'
    __name__ = 'prestashop.import.wizard'

    start = StateView(
        'prestashop.import.wizard.view',
        'prestashop.prestashop_import_wizard_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, fields):
        """Import the orders and display a confirmation message to the user

        :param fields: Wizard fields
        """
        Site = Pool().get('prestashop.site')

        site = Site(Transaction().context['active_id'])

        default = {
            'orders_imported': len(
                site.import_orders_from_prestashop_site()
            )}

        return default


class ExportWizardView(ModelView):
    'Prestashop Export Wizard View'
    __name__ = 'prestashop.export.wizard.view'

    orders_exported = fields.Integer('Orders Exported', readonly=True)


class ExportWizard(Wizard):
    'Prestashop Export Wizard'
    __name__ = 'prestashop.export.wizard'

    start = StateView(
        'prestashop.export.wizard.view',
        'prestashop.prestashop_export_wizard_view_form',
        [
            Button('Ok', 'end', 'tryton-ok'),
        ]
    )

    def default_start(self, fields):
        """Export the orders and display a confirmation message to the user

        :param fields: Wizard fields
        """
        Site = Pool().get('prestashop.site')

        site = Site(Transaction().context['active_id'])

        default = {
            'orders_exported': len(
                site.export_orders_to_prestashop_site()
            )}

        return default
