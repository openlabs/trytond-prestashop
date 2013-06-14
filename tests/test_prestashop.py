# -*- coding: utf-8 -*-
"""
    test_prestashop

    Test Prestashop integration with tryton.

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import sys
import os
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from datetime import datetime
DIR = os.path.abspath(os.path.normpath(os.path.join(__file__,
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
from trytond.config import CONFIG
CONFIG['data_path'] = '.'
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
    root_xml_path = os.path.join(
        os.path.split(os.path.abspath(__file__))[0], 'xml', PS_VERSION
    )

    file_path = os.path.join(root_xml_path, resource, str(filename)) + '.xml'

    return objectify.fromstring(open(file_path).read()).getchildren()[0]


class BaseTestCase(unittest.TestCase):
    "Base Test case"

    def setUp(self):
        "Setup"
        trytond.tests.test_tryton.install_module('prestashop')
        self.PrestashopSite = POOL.get('prestashop.site')
        self.Party = POOL.get('party.party')
        self.Address = POOL.get('party.address')
        self.ContactMechanism = POOL.get('party.contact_mechanism')
        self.Company = POOL.get('company.company')
        self.Currency = POOL.get('currency.currency')
        self.CurrencyRate = POOL.get('currency.currency.rate')
        self.ProductTemplate = POOL.get('product.template')
        self.Product = POOL.get('product.product')
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
        self.Country.create([
            {
                'name': 'France',
                'code': 'FR',
            }, {
                'name': 'United States',
                'code': 'US'
            }
        ])

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
            create_chart.transition_create_properties()

            self.Party.write(
                [self.Party(self.company_party)], {
                    'account_payable': payable.id,
                    'account_receivable': receivable.id,
                }
            )
            self.site, = self.PrestashopSite.create([{
                'url': 'Some URL',
                'key': 'A key',
                'default_account_expense': self.get_account_by_kind('expense').id,
                'default_account_revenue': self.get_account_by_kind('revenue').id,
                'company': self.company.id,
                'default_warehouse': self.Location.search(
                    [('type', '=', 'warehouse')], limit=1
                )[0].id,
                'timezone': 'UTC',
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
                self.PrestashopSite.test_connection([self.site])

            txn.cursor.rollback()

    def test_0020_setup_site(self):
        """Test the setup of site which imports languages and order states
        for mapping
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            self.assertEqual(len(self.LangPrestashop.search([])), 0)
            self.assertEqual(len(self.PrestashopOrderState.search([])), 0)

            with Transaction().set_context(ps_test=True):
                self.PrestashopSite.setup_site([self.site])

            self.assertTrue(len(self.LangPrestashop.search([])) > 0)
            self.assertTrue(len(self.PrestashopOrderState.search([])) > 0)

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
