# -*- coding: utf-8 -*-
"""
    test_product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT

from test_prestashop import get_objectified_xml, BaseTestCase


class TestParty(BaseTestCase):
    """Test Customer > Party integration
    """

    def test_0010_party_import(self):
        """Test Party import
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    prestashop_site=self.site.id, ps_test=True
                ):
                self.setup_sites()

                client = self.site.get_prestashop_client()

                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.ContactMechanism.search([])), 0)

                # Create a party using prestashop data
                customer_data = get_objectified_xml('customers', 1)
                party = self.Party.create_using_ps_data(customer_data)
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.ContactMechanism.search([])), 1)

                # Assert that the language set on party is same as the language
                # in site languages
                self.assertEqual(
                    party.lang,
                    self.Lang.get_using_ps_id(customer_data.id_lang.pyval)
                )

                # Try importing the same party, it should NOT create a
                # new one.
                party = self.Party.find_or_create_using_ps_data(
                    customer_data
                )
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.ContactMechanism.search([])), 1)

                # Create the same party, it should NOT create a new one
                # Instead, it should blow up with a UserError sue to sql
                # constraints
                self.assertRaises(
                    UserError,
                    self.Party.create_using_ps_data, customer_data
                )

                # Search for the same party in tryton using a different method
                # It should return the same party
                self.assertEqual(
                    party.id,
                    self.Party.get_party_using_ps_data(customer_data).id
                )

            with Transaction().set_context(
                    prestashop_site=self.site_alt.id, ps_test=True
                ):
                client = self.site_alt.get_prestashop_client()

                # Nothing should be linked to site_alt
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site_alt.id)
                ])), 0)

                # Create a party using prestashop data
                customer_data = get_objectified_xml('customers', 1)
                party = self.Party.create_using_ps_data(customer_data)
                self.assertEqual(len(self.Party.search([
                    ('prestashop_site', '=', self.site_alt.id)
                ])), 1)

    def test_0020_address_import_n_matching(self):
        """Test address import and pattern matching
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT) as txn:
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                    prestashop_site=self.site.id, ps_test=True
                ):
                self.setup_sites()

                client = self.site.get_prestashop_client()

                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.ContactMechanism.search([])), 0)
                self.assertEqual(len(self.CountryPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)

                # Create a party
                party = self.Party.find_or_create_using_ps_data(
                    get_objectified_xml('customers', 1)
                )

                # Create an address using prestashop data

                # This address has a country but not a state
                # So, it should proceed without breaking and creating a
                # cache record for country
                address_data = get_objectified_xml('addresses', 2)
                address = self.Address.create_for_party_using_ps_data(
                    party, address_data
                )
                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site.id)
                ])), 2)
                self.assertEqual(len(self.ContactMechanism.search([])), 3)
                self.assertEqual(len(self.CountryPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)

                # Make sure the country cached is the right one
                ps_country_id = address_data.id_country.pyval
                self.assertEqual(
                    self.Country.get_using_ps_id(ps_country_id).id,
                    address.country.id
                )

                # Find or create the same address, it should not create a new
                # one
                address = \
                    self.Address.find_or_create_for_party_using_ps_data(
                        party, get_objectified_xml('addresses', 2)
                    )
                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site.id)
                ])), 2)
                self.assertEqual(len(self.ContactMechanism.search([])), 3)
                self.assertEqual(len(self.CountryPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)

                # Test with an exactly same address with same ID
                self.assertTrue(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2001))
                )

                # Test with a nearly same address with same ID and street2
                # missing
                self.assertFalse(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2002))
                )

                # Test with a nearly same address with same ID and different
                # country
                self.assertFalse(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2003))
                )

                # Test with a nearly same address with same ID and non ascii
                # characters in name
                self.assertFalse(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2004))
                )

                # Test with a nearly same address with same ID and postcode
                # missing
                self.assertFalse(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2005))
                )

                # Test with a nearly same address with same ID and different
                # city
                self.assertFalse(
                    address.match_with_ps_data(
                        get_objectified_xml('addresses', 2006))
                )

                # No subdivision has been cached till now
                self.assertEqual(len(self.SubdivisionPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)

                state_data = get_objectified_xml('states', 1)
                #Cache a subdivision
                subdivision = self.Subdivision.cache_prestashop_id(1)
                self.assertEqual(len(self.SubdivisionPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)
                self.assertEqual(
                    self.Subdivision.get_using_ps_id(1).id, subdivision.id
                )

                # Nothing should be created under site_alt
                self.assertEqual(len(self.Address.search([
                    ('party.prestashop_site', '=', self.site_alt.id)
                ])), 0)
                self.assertEqual(len(self.CountryPrestashop.search([
                    ('site', '=', self.site_alt.id)
                ])), 0)


def suite():
    "Prestashop Party test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestParty)
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
