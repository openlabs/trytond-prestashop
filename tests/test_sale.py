# -*- coding: utf-8 -*-
"""
    test_sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from decimal import Decimal
import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT

from test_prestashop import get_objectified_xml, BaseTestCase


class TestSale(BaseTestCase):
    "Test Order > Sale integration"

    def test_0010_order_import(self):
        """Test Order import
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    self.User.get_preferences(context_only=True),
                    prestashop_site=self.site.id, ps_test=True,
                ):
                self.setup_sites()

                client = self.site.get_prestashop_client()

                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.ContactMechanism.search([])), 0)

                order_data = get_objectified_xml('orders', 1)

                self.Sale.find_or_create_using_ps_data(order_data)
                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site.id)
                ])), 2)
                self.assertEqual(len(self.ContactMechanism.search([])), 3)

                # Try importing the same sale again, it should NOT create a
                # new one.
                self.Sale.find_or_create_using_ps_data(order_data)
                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)

                sale, = self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])

                # Test getting sale using prestashop data
                self.assertEqual(
                    sale.id,
                    self.Sale.get_order_using_ps_data(order_data).id
                )

                self.assertEqual(sale.state, 'done')

                self.assertEqual(
                    sale.total_amount,
                    Decimal(str(order_data.total_paid_tax_excl))
                )

                # Creating the order again should blow up with a usererror
                # due to sql constraints
                self.assertRaises(
                    UserError,
                    self.Sale.create_using_ps_data, order_data
                )

                # Sale should not be created under site_alt
                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site_alt.id)
                ])), 0)

    def test_0013_order_import_delivered(self):
        """Import an order that has been delivered on PS
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    self.User.get_preferences(context_only=True),
                    prestashop_site=self.site.id, ps_test=True,
                ):
                self.setup_sites()

                order_data = get_objectified_xml('orders', 1)

                sale = self.Sale.find_or_create_using_ps_data(order_data)

                self.assertEqual(sale.state, 'done')

    def test_0016_order_import_canceled(self):
        """Import an order which was canceled on PS
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    self.User.get_preferences(context_only=True),
                    prestashop_site=self.site.id, ps_test=True,
                ):
                self.setup_sites()

                order_data = get_objectified_xml('orders', 2)

                sale = self.Sale.find_or_create_using_ps_data(order_data)

                self.assertEqual(sale.state, 'cancel')

    def test_0020_order_import_from_site(self):
        """Test Order import from site
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    self.User.get_preferences(context_only=True),
                    prestashop_site=self.site.id, ps_test=True,
                ):
                self.setup_sites()

                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 0)

                self.site.import_orders_from_prestashop_site()

                self.assertEqual(len(self.Sale.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)


def suite():
    "Prestashop Sale test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestSale)
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
