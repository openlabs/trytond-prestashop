# -*- coding: utf-8 -*-
"""
    test_sale

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from decimal import Decimal
import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT

from test_prestashop import get_objectified_xml, BaseTestCase


class TestSale(BaseTestCase):
    "Test Order > Sale integration"

    def test_0010_order_import(self):
        """Test Order import
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                self.User.get_preferences(context_only=True),
                current_channel=self.channel.id, ps_test=True,
            ):
                self.setup_channels()

                self.channel.get_prestashop_client()

                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.channel.id)
                ])), 0)
                self.assertEqual(len(self.Party.search([
                    ('channel', '=', self.channel.id)
                ])), 0)
                self.assertEqual(len(self.Address.search([
                    ('party.channel', '=', self.channel.id)
                ])), 0)
                self.assertEqual(len(self.ContactMechanism.search([])), 0)

                order_data = get_objectified_xml('orders', 1)

                self.Sale.find_or_create_using_ps_data(order_data)
                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.channel.id)
                ])), 1)
                self.assertEqual(len(self.Party.search([
                    ('channel', '=', self.channel.id)
                ])), 1)
                self.assertEqual(len(self.Address.search([
                    ('party.channel', '=', self.channel.id)
                ])), 1)
                self.assertEqual(len(self.ContactMechanism.search([])), 3)

                # Try importing the same sale again, it should NOT create a
                # new one.
                self.Sale.find_or_create_using_ps_data(order_data)
                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.channel.id)
                ])), 1)

                sale, = self.Sale.search([
                    ('channel', '=', self.channel.id)
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
                # Sale should not be created under alt_channel
                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.alt_channel.id)
                ])), 0)

                # Creating the order again should blow up with a usererror
                # due to sql constraints
                self.assertRaises(
                    UserError,
                    self.Sale.create_using_ps_data, order_data
                )

    def test_0013_order_import_delivered(self):
        """Import an order that has been delivered on PS
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                self.User.get_preferences(context_only=True),
                current_channel=self.channel.id, ps_test=True,
            ):
                self.setup_channels()

                order_data = get_objectified_xml('orders', 1)

                sale = self.Sale.find_or_create_using_ps_data(order_data)

                self.assertEqual(sale.state, 'done')

    def test_0016_order_import_canceled(self):
        """Import an order which was canceled on PS
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                self.User.get_preferences(context_only=True),
                current_channel=self.channel.id, ps_test=True,
            ):
                self.setup_channels()

                order_data = get_objectified_xml('orders', 2)

                sale = self.Sale.find_or_create_using_ps_data(order_data)

                self.assertEqual(sale.state, 'cancel')

    def test_0020_order_import_from_prestashop(self):
        """Test Order import from prestashop
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                self.User.get_preferences(context_only=True),
                current_channel=self.channel.id, ps_test=True,
            ):
                self.setup_channels()

                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.channel.id)
                ])), 0)

                self.channel.import_prestashop_orders()

                self.assertEqual(len(self.Sale.search([
                    ('channel', '=', self.channel.id)
                ])), 1)

    def test_0030_check_prestashop_exception_order_total(self):
        """
        Check if exception is created when order total does not match
        """
        ChannelException = POOL.get('channel.exception')

        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                self.User.get_preferences(context_only=True),
                current_channel=self.channel.id, ps_test=True,
            ):
                self.setup_channels()

                order_data = get_objectified_xml('orders', 1)

                order_data.total_paid_tax_excl = 100

                self.assertFalse(ChannelException.search([]))

                sale = self.Sale.find_or_create_using_ps_data(order_data)

                self.assertNotEqual(
                    sale.total_amount, order_data.total_paid_tax_excl
                )

                self.assertTrue(sale.has_channel_exception)

                self.assertTrue(ChannelException.search([]))

                self.assertNotEqual(sale.state, 'done')


def suite():
    "Prestashop Sale test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestSale)
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
