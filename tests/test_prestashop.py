# -*- coding: utf-8 -*-
"""
    test_prestashop

    Test Prestashop integration with tryton.

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import os
import pkg_resources
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import datetime
DIR = os.path.abspath(
    os.path.normpath(os.path.join(
        __file__,
        '..', '..', '..', '..', '..', 'trytond')))
if os.path.isdir(DIR):
    sys.path.insert(0, os.path.dirname(DIR))

from lxml import objectify
import unittest

import trytond
import trytond.tests.test_tryton
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT, \
    test_view, test_depends
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.config import config
config.set('database', 'path', '/tmp')
PS_VERSION = '1.5'


def get_objectified_xml(resource, filename):
    """Reads the xml file from the filesystem and returns the objectified xml

    On filesystem, the files are kept in this format:
        xml----
              |
              version----
                        |
                        resource----
                                   |
                                   filename

    :param resource: The prestashop resource for which the file has to be
                     fetched. It is same as the folder name in which the files
                     are kept.
    :param filename: The name of the file to be fethced without `.xml`
                     extension. It will be an integer value
    :returns: Objectified XML of the file read.
    """
    root_xml_folder = pkg_resources.resource_filename('mockstashop', 'xml')
    root_xml_path = os.path.join(root_xml_folder, PS_VERSION)

    file_path = os.path.join(root_xml_path, resource, str(filename)) + '.xml'

    return objectify.fromstring(open(file_path).read()).getchildren()[0]


class BaseTestCase(unittest.TestCase):
    "Base Test case"

    def setUp(self):
        "Setup"
        trytond.tests.test_tryton.install_module('prestashop')
        self.SaleChannel = POOL.get('sale.channel')
        self.Party = POOL.get('party.party')
        self.Address = POOL.get('party.address')
        self.ContactMechanism = POOL.get('party.contact_mechanism')
        self.Company = POOL.get('company.company')
        self.Currency = POOL.get('currency.currency')
        self.CurrencyRate = POOL.get('currency.currency.rate')
        self.ProductTemplate = POOL.get('product.template')
        self.SaleChannel = POOL.get('sale.channel')
        self.TemplatePrestashop = POOL.get('product.template.prestashop')
        self.Product = POOL.get('product.product')
        self.Category = POOL.get('product.category')
        self.ProductPrestashop = POOL.get('product.product.prestashop')
        self.PriceList = POOL.get('product.price_list')
        self.Uom = POOL.get('product.uom')
        self.Sale = POOL.get('sale.sale')
        self.Location = POOL.get('stock.location')
        self.Country = POOL.get('country.country')
        self.Subdivision = POOL.get('country.subdivision')
        self.Lang = POOL.get('ir.lang')
        self.CountryPrestashop = POOL.get('country.country.prestashop')
        self.SubdivisionPrestashop = POOL.get('country.subdivision.prestashop')
        self.LangPrestashop = POOL.get('prestashop.site.lang')
        self.PrestashopOrderState = POOL.get('prestashop.site.order_state')

        self.FiscalYear = POOL.get('account.fiscalyear')
        self.Sequence = POOL.get('ir.sequence')
        self.SequenceStrict = POOL.get('ir.sequence.strict')

        self.AccountTemplate = POOL.get('account.account.template')
        self.Account = POOL.get('account.account')
        self.CreateChartAccount = POOL.get(
            'account.create_chart', type="wizard"
        )
        self.PaymentTerm = POOL.get('account.invoice.payment_term')
        self.User = POOL.get('res.user')
        self.ModelField = POOL.get('ir.model.field')
        self.Property = POOL.get('ir.property')

    def _create_pricelists(self):
        """
        Create the pricelists
        """
        # Setup the pricelists
        user_price_list, = self.PriceList.create([{
            'name': 'PL 1',
            'company': self.company.id,
            'lines': [
                ('create', [{
                    'formula': 'unit_price * %s' % Decimal('1.10')
                }])
            ],
        }])
        return user_price_list.id

    def setup_defaults(self):
        "Setup defaults"
        self.usd, = self.Currency.create([{
            'name': 'United Stated Dollar',
            'code': 'USD',
            'symbol': 'USD',
        }])
        self.CurrencyRate.create([{
            'rate': Decimal("1.0"),
            'currency': self.usd.id,
        }])
        [fr, us] = self.Country.create([
            {
                'name': 'France',
                'code': 'FR',
            }, {
                'name': 'United States',
                'code': 'US'
            }
        ])

        self.Subdivision.create([{
            'name': 'Alabama',
            'code': 'US-AL',
            'country': us.id,
            'type': 'state',
        }])

        with Transaction().set_context(company=None):
            self.company_party, = self.Party.create([{
                'name': 'Openlabs',
            }])

            self.company, = self.Company.create([{
                'party': self.company_party.id,
                'currency': self.usd.id,
            }])
        self.User.write([self.User(USER)], {
            'main_company': self.company.id,
            'company': self.company.id,
        })

        date = datetime.utcnow().date()

        with Transaction().set_context(
            self.User.get_preferences(context_only=True)
        ):
            invoice_sequence, = self.SequenceStrict.create([{
                'name': '%s' % date.year,
                'code': 'account.invoice',
                'company': self.company.id,
            }])
            fiscal_year, = self.FiscalYear.create([{
                'name': '%s' % date.year,
                'start_date': date + relativedelta(month=1, day=1),
                'end_date': date + relativedelta(month=12, day=31),
                'company': self.company.id,
                'post_move_sequence': self.Sequence.create([{
                    'name': '%s' % date.year,
                    'code': 'account.move',
                    'company': self.company.id,
                }])[0].id,
                'out_invoice_sequence': invoice_sequence.id,
                'in_invoice_sequence': invoice_sequence.id,
                'out_credit_note_sequence': invoice_sequence.id,
                'in_credit_note_sequence': invoice_sequence.id,
            }])
            self.FiscalYear.create_period([fiscal_year])

            account_template, = self.AccountTemplate.search(
                [('parent', '=', None)]
            )

            session_id, _, _ = self.CreateChartAccount.create()
            create_chart = self.CreateChartAccount(session_id)
            create_chart.account.account_template = account_template
            create_chart.account.company = self.company
            create_chart.transition_create_account()
            revenue, = self.Account.search([
                ('kind', '=', 'revenue'),
                ('company', '=', self.company.id),
            ])
            receivable, = self.Account.search([
                ('kind', '=', 'receivable'),
                ('company', '=', self.company.id),
            ])
            payable, = self.Account.search([
                ('kind', '=', 'payable'),
                ('company', '=', self.company.id),
            ])
            expense, = self.Account.search([
                ('kind', '=', 'expense'),
                ('company', '=', self.company.id),
            ])
            create_chart.properties.company = self.company
            create_chart.properties.account_receivable = receivable
            create_chart.properties.account_payable = payable
            create_chart.properties.account_revenue = revenue
            create_chart.properties.account_expense = expense
            create_chart.transition_create_properties()
            category, = self.Category.create([{
                'name': 'Test Category',
            }])
            self.Party.write(
                [self.Party(self.company_party)], {
                    'account_payable': payable.id,
                    'account_receivable': receivable.id,
                }
            )
            uom, = self.Uom.search([('symbol', '=', 'u')])
            shipping_product_template, = self.ProductTemplate.create([{
                'name': 'Test Carrier Product',
                'category': category.id,
                'type': 'service',
                'salable': True,
                'sale_uom': uom,
                'list_price': Decimal('10'),
                'cost_price': Decimal('5'),
                'default_uom': uom,
                'cost_price_method': 'fixed',
                'account_revenue': self.get_account_by_kind('revenue').id,
                'products': [
                    ('create', self.ProductTemplate.default_products())
                ]
            }])
            warehouse, = self.Location.search([
                ('type', '=', 'warehouse')
            ], limit=1)
            self.payment_term, = self.PaymentTerm.create([{
                'name': 'Direct',
                'lines': [('create', [{'type': 'remainder'}])]
            }])
            self.price_list = self._create_pricelists()
            self.channel, self.alt_channel = self.SaleChannel.create([{
                'name': 'Channel 1',
                'warehouse': warehouse.id,
                'company': self.company.id,
                'source': 'prestashop',
                'prestashop_url': 'Some URL',
                'prestashop_key': 'A key',
                'currency': self.company.currency.id,
                'price_list': self.price_list,
                'invoice_method': 'manual',
                'shipment_method': 'manual',
                'prestashop_shipping_product':
                    shipping_product_template.products[0].id,
                'prestashop_timezone': 'UTC',
                'payment_term': self.payment_term,
            }, {
                'name': 'Channel 2',
                'warehouse': warehouse.id,
                'company': self.company.id,
                'source': 'prestashop',
                'prestashop_url': 'Some URL 2',
                'prestashop_key': 'A key 2',
                'currency': self.company.currency.id,
                'price_list': self.price_list,
                'invoice_method': 'manual',
                'shipment_method': 'manual',
                'payment_term': self.payment_term,
                'prestashop_shipping_product':
                    shipping_product_template.products[0].id,
                'prestashop_timezone': 'UTC',
            }])

            model_field, = self.ModelField.search([
                ('name', '=', 'account_revenue'),
                ('model.model', '=', 'product.template'),
            ], order=[], limit=1)

            self.Property.create([{
                'value': '%s,%s' % (
                    'account.account', self.get_account_by_kind('revenue').id
                ),
                'res': None,
                'field': model_field.id,
            }])

            self.PaymentTerm.create([{
                'name': 'Direct',
                'lines': [('create', [{'type': 'remainder'}])]
            }])

    def get_account_by_kind(self, kind, company=None, silent=True):
        """Returns an account with given spec

        :param kind: receivable/payable/expense/revenue
        :param silent: dont raise error if account is not found
        """
        Account = POOL.get('account.account')
        Company = POOL.get('company.company')

        if company is None:
            company, = Company.search([], limit=1)

        accounts = Account.search([
            ('kind', '=', kind),
            ('company', '=', company.id)
        ], limit=1)
        if not accounts and not silent:
            raise Exception("Account not found")
        return accounts[0] if accounts else False

    def setup_channels(self):
        "Setup channels"
        self.SaleChannel.import_prestashop_languages([self.channel])
        self.SaleChannel.import_prestashop_order_states([self.channel])
        self.SaleChannel.import_prestashop_languages([self.alt_channel])
        self.SaleChannel.import_prestashop_order_states([self.alt_channel])


class TestPrestashop(BaseTestCase):
    "Test Prestashop integration"

    def test0005views(self):
        '''
        Test views.
        '''
        test_view('prestashop')

    def test0006depends(self):
        '''
        Test depends.
        '''
        test_depends()

    def test_0010_test_connection(self):
        """Test the test connection button
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(ps_test=True):
                self.SaleChannel.test_prestashop_connection([self.channel])
                self.SaleChannel.test_prestashop_connection([self.alt_channel])

            txn.cursor.rollback()

    def test_0020_import_language(self):
        """Test the import of language
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                ps_test=True, current_channel=self.channel.id
            ):
                # No language imported yet
                self.assertEqual(
                    self.LangPrestashop.search_using_ps_id(1), None
                )

                # Import a language
                # This is english language with code just as `en`
                lang_data = get_objectified_xml('languages', 1)
                lang = self.LangPrestashop.create_using_ps_data(
                    lang_data
                )

                self.assertEqual(
                    self.LangPrestashop.search_using_ps_id(1).id, lang.id
                )
                self.assertEqual(
                    lang.language.code, 'en_US'
                )

                # Import another language
                # This is french with code as fr-FR
                lang_data = get_objectified_xml('languages', 2)
                lang = self.LangPrestashop.create_using_ps_data(
                    lang_data
                )

                self.assertEqual(
                    self.LangPrestashop.search_using_ps_id(2).id, lang.id
                )
                self.assertEqual(
                    lang.language.code, 'fr_FR'
                )

                self.assertEqual(
                    len(self.LangPrestashop.get_channel_languages()), 2
                )

    def test_0030_import_prestashop_order_states(self):
        """Test the import of order states
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                ps_test=True, current_channel=self.channel.id
            ):
                self.SaleChannel.import_prestashop_languages([self.channel])
                # No state imported yet
                self.assertEqual(
                    self.PrestashopOrderState.search_using_ps_id(1), None
                )

                # Create a state
                state_data = get_objectified_xml('order_states', 1)
                state = self.PrestashopOrderState.\
                    create_using_ps_data(
                        state_data
                    )

                self.assertEqual(
                    self.PrestashopOrderState.search_using_ps_id(1).id,
                    state.id
                )
                self.assertEqual(
                    state.order_state, 'sale.confirmed'
                )

                with Transaction().set_context(language='en_US'):
                    state = self.PrestashopOrderState(state.id)
                    self.assertEqual(
                        state.prestashop_state, 'Awaiting cheque payment'
                    )
                with Transaction().set_context(language='fr_FR'):
                    state = self.PrestashopOrderState(state.id)
                    self.assertEqual(
                        state.prestashop_state, 'Awaits cheque paymento'
                    )

    def test_0040_setup_channel(self):
        """
        Test the setup of channel which imports languages and order states
        for mapping
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            self.assertEqual(len(self.LangPrestashop.search([])), 0)
            self.assertEqual(len(self.PrestashopOrderState.search([])), 0)

            with Transaction().set_context(ps_test=True):
                self.assertRaises(
                    UserError,
                    self.SaleChannel.import_prestashop_order_states,
                    [self.channel]
                )

                self.SaleChannel.import_prestashop_languages([self.channel])

                self.assertTrue(len(self.LangPrestashop.search([])) > 0)

                self.SaleChannel.import_prestashop_order_states([self.channel])

                self.assertTrue(len(self.PrestashopOrderState.search([])) > 0)

            txn.cursor.rollback()

    def test_0050_setup_multi_channel(self):
        """Test the setup of multiple channels where import of languages and
        order states should be correct according to channel
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            # No record exists for any channel
            self.assertEqual(len(self.LangPrestashop.search([])), 0)
            self.assertEqual(len(self.PrestashopOrderState.search([])), 0)

            with Transaction().set_context(ps_test=True):

                # Same behaviour by both channel when no order states are there
                self.assertRaises(
                    UserError,
                    self.SaleChannel.import_prestashop_order_states,
                    [self.channel]
                )
                self.assertRaises(
                    UserError,
                    self.SaleChannel.import_prestashop_order_states,
                    [self.alt_channel]
                )

                # Import languages for first channel, the second one should
                # still raise an user error as before
                self.SaleChannel.import_prestashop_languages([self.channel])

                self.assertTrue(len(self.LangPrestashop.search([
                    ('channel', '=', self.channel.id)
                ])) > 0)

                with Transaction().set_context(
                    current_channel=self.channel.id
                ):
                    self.assertEqual(
                        self.Lang.get_using_ps_id(1).code, 'en_US'
                    )

                self.assertTrue(len(self.LangPrestashop.search([
                    ('channel', '=', self.alt_channel.id)
                ])) == 0)
                self.assertRaises(
                    UserError,
                    self.SaleChannel.import_prestashop_order_states,
                    [self.alt_channel]
                )

                # Languages cannot be imported again for first channel but for
                # second it can be imported
                self.SaleChannel.import_prestashop_languages([self.alt_channel])

                # Import order states for first channel only
                self.SaleChannel.import_prestashop_order_states([self.channel])

                self.assertTrue(len(self.PrestashopOrderState.search([
                    ('channel', '=', self.channel.id)
                ])) > 0)
                self.assertTrue(len(self.PrestashopOrderState.search([
                    ('channel', '=', self.alt_channel.id)
                ])) == 0)

            txn.cursor.rollback()


def suite():
    "Prestashop test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestPrestashop)
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
