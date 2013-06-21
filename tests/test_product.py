# -*- coding: utf-8 -*-
"""
    test_party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import unittest

import trytond.tests.test_tryton
from trytond.transaction import Transaction
from trytond.exceptions import UserError
from trytond.tests.test_tryton import DB_NAME, USER, CONTEXT

from test_prestashop import get_objectified_xml, BaseTestCase


class TestProduct(BaseTestCase):
    """Test Product > Template/variant integration
    """

    def test_0010_product_template_import(self):
        """Test Product Template import
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                prestashop_site=self.site.id, ps_test=True,
            ):
                self.setup_sites()

                self.assertEqual(len(self.ProductTemplate.search([])), 0)
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.Product.search([])), 0)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)

                product_data = get_objectified_xml('products', 1)
                template = self.ProductTemplate.find_or_create_using_ps_data(
                    product_data
                )
                # This should create a template and two variants where one
                # is created by template and other by this combination
                self.assertEqual(len(self.ProductTemplate.search([])), 1)
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.Product.search([])), 1)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)

                # Product name should be in english and french
                with Transaction().set_context(language='en_US'):
                    template = self.ProductTemplate(template.id)
                    self.assertEqual(
                        template.name, 'iPod Nano'
                    )
                with Transaction().set_context(language='fr_FR'):
                    template = self.ProductTemplate(template.id)
                    self.assertEqual(
                        template.name, 'iPod Nano French'
                    )

                # Product description should be in english only
                with Transaction().set_context(language='en_US'):
                    product_desc_en = self.Product(
                        template.products[0].id).description
                with Transaction().set_context(language='fr_FR'):
                    product_desc_fr = self.Product(
                        template.products[0].id).description
                self.assertEqual(product_desc_en, product_desc_fr)

                # Try creating the same product again, it should NOT create a
                # new one and blow with user error due to sql constraint
                self.assertRaises(
                    UserError,
                    self.ProductTemplate.create_using_ps_data, product_data
                )

                # Get template using prestashop data
                self.assertEqual(
                    template.id,
                    self.ProductTemplate.get_template_using_ps_data(
                        product_data
                    ).id
                )

                # Get template using prestashop ID
                self.assertEqual(
                    template.id,
                    self.ProductTemplate.get_template_using_ps_id(1).id
                )

                # Nothing should be created under site_alt
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site_alt.id)
                ])), 0)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site_alt.id)
                ])), 0)

    def test_0020_product_import(self):
        """Test Product import
        """
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            # Call method to setup defaults
            self.setup_defaults()

            with Transaction().set_context(
                prestashop_site=self.site.id, ps_test=True,
            ):
                self.setup_sites()

                self.assertEqual(len(self.ProductTemplate.search([])), 0)
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)
                self.assertEqual(len(self.Product.search([])), 0)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 0)

                product = self.Product.find_or_create_using_ps_data(
                    get_objectified_xml('combinations', 1)
                )
                # This should create a template and two variants where one
                # is created by template and other by this combination
                self.assertEqual(len(self.ProductTemplate.search([])), 1)
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site.id)
                ])), 1)
                self.assertEqual(len(self.Product.search([])), 2)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site.id)
                ])), 2)

                # Try importing the same product again, it should NOT create a
                # new one.
                self.Product.find_or_create_using_ps_data(
                    get_objectified_xml('combinations', 1)
                )
                self.assertEqual(len(self.Product.search([])), 2)

                # Test getting product using prestashop data
                self.assertEqual(
                    product.id,
                    self.Product.get_product_using_ps_data(
                        get_objectified_xml('combinations', 1)
                    ).id
                )

                # Test getting product using prestashop ID
                self.assertEqual(
                    product.id,
                    self.Product.get_product_using_ps_id(1).id
                )

                # Nothing should be created under site_alt
                self.assertEqual(len(self.TemplatePrestashop.search([
                    ('site', '=', self.site_alt.id)
                ])), 0)
                self.assertEqual(len(self.ProductPrestashop.search([
                    ('site', '=', self.site_alt.id)
                ])), 0)


def suite():
    "Prestashop Product test suite"
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(
        unittest.TestLoader().loadTestsFromTestCase(TestProduct)
    )
    return suite


if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
