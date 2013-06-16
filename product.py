# -*- coding: utf-8 -*-
"""
    product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from decimal import Decimal

from trytond.model import ModelSQL, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Product', 'Template', 'TemplatePrestashop', 'ProductPrestashop']
__metaclass__ = PoolMeta


class TemplatePrestashop(ModelSQL):
    """Product Template - Prestashop site store

    A template can be available on more than one sites on prestashop as product
    This model keeps a record of a template's association with a site and the
    ID of product on that site
    """
    __name__ = 'product.template.prestashop'

    #: The ID of corresponding product for this template on prestashop
    prestashop_id = fields.Integer(
        'Prestashop ID', readonly=True, required=True
    )

    #: The prestashop site
    site = fields.Many2One(
        'prestashop.site', 'Prestashop Site', readonly=True, required=True
    )

    #: Product template in tryton
    template = fields.Many2One(
        'product.template', 'Product Template', readonly=True, required=True
    )

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        "Setup"
        super(TemplatePrestashop, cls).__setup__()
        cls._sql_constraints += [
            ('prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, site)',
                'Template must be unique by prestashop id and site'
            )
        ]


class Template:
    """Product Template

    Prestashop has products and combinations where products can be compared to
    templates in tryton and combinations can be compared to products in tryton.
    We create a template in tryton for the product in prestashop and a product
    each for the combinations in prestashop. Here the `prestashop_ids` on
    template refers to the product_ids from prestashop product and
    `prestashop_combination_id` on product in tryton refers to the
    combination_id from prestashop.

    For the product in tryton created against the product in prestashop, the
    `prestashop_combination_id` is kept as 0 (ZERO).
    """
    __name__ = 'product.template'

    prestashop_ids = fields.One2Many(
        'product.template.prestashop', 'template', 'Prestashop IDs',
        readonly=True
    )

    @classmethod
    def find_or_create_using_ps_data(cls, product_record):
        """Look for the template in tryton corresponding to the product_record.
        If found, return the same else create a new one and return that.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created template
        """
        pass

    @classmethod
    def create_using_ps_data(cls, product_record):
        """Create a template from the product record sent by prestashop client

        ..note:: Product name and description from product record are stored a
        level deeper than other values. They are stored under a language
        object under name and description objects.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created template
        """
        pass

    @classmethod
    def get_template_using_ps_data(cls, product_record):
        """Find an existing template in Tryton which matches the details
        of this product_record. This search is made in the
        TemplatePrestashop store.

        By default, it matches the prestashop_id and site.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record if a template is found else None
        """
        pass

    @classmethod
    def get_template_using_ps_id(cls, product_record_id):
        """Find an existing template in Tryton which matches the
        product_record_id. This search is made in the
        TemplatePrestashop store.

        By default, it matches the prestashop_id and site.

        :param product_record_id: Product ID on prestashop
        :returns: Active record if a template is found else None
        """
        pass


class ProductPrestashop(ModelSQL):
    """Product Variant - Prestashop site store

    A product variant can be available on more than one sites on prestashop
    as combination. Combination IDs on prestashop are unique throughout
    the site.
    This model keeps a record of a variant's association with a site and the
    ID of combination on that site
    """
    __name__ = 'product.product.prestashop'

    #: The ID of corresponding combination for this product on prestashop
    prestashop_combination_id = fields.Integer(
        'Prestashop Combination ID', readonly=True, required=True
    )

    #: The prestashop site
    site = fields.Many2One(
        'prestashop.site', 'Prestashop Site', readonly=True, required=True
    )

    #: Product/Variant in tryton
    product = fields.Many2One(
        'product.product', 'Product Variant', readonly=True, required=True
    )

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        "Setup"
        super(ProductPrestashop, cls).__setup__()
        cls._error_messages.update({
            'duplicate_combination': ('Combination with id '
                '"%(combination_id)s" exists for template "%(template)s" '
                'in %(site)s'),
            'duplicate_combination_across_site': ('Combination with id '
                '"%(combination_id)s" exists in site "%(site)s"'),
        })

    @classmethod
    def validate(cls, records):
        """Checks that the combination_id for a product is unique within a
        template.

        :param records: List of active records
        """
        super(TypeTemplate, cls).validate(records)
        for record in records:
            record.check_combination()

    def check_combination(self):
        """Performs two checks

        1. Checks that this combination is unique within the template.
        2. Checks that this combination is unique throughout the site if
           the combination id from prestashop is non zero.
        """
        # Check that this combination is unique within the template
        if len(ProductPrestashop.search([
                ('prestashop_combination_id', '=',
                    self.prestashop_combination_id),
                ('site', '=', self.site),
                ('product.template', '=', self.product.template)
            ])) > 1:
            self.raise_user_error(
                'duplicate_combination', {
                    'combination_id': self.prestashop_combination_id,
                    'template': self.product.template.name,
                    'site': self.site.url,
                }
            )
        # Check that this combination is unique throughout the site if
        # the combination id from prestashop is non zero
        if self.prestashop_combination_id != 0 and \
            len(ProductPrestashop.search([
                ('prestashop_combination_id', '=',
                    self.prestashop_combination_id),
                ('site', '=', self.site),
            ])) > 1:
            self.raise_user_error(
                'duplicate_combination_across_site', {
                    'combination_id': self.prestashop_combination_id,
                    'site': self.site.url,
                }
            )
        return True


class Product:
    "Product Variant"
    __name__ = 'product.product'

    prestashop_combination_ids = fields.One2Many(
        'product.product.prestashop', 'product', 'Prestashop Combination IDs',
    )

    @staticmethod
    def default_prestashop_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def find_or_create_using_ps_data(cls, combination_record):
        """Look for the variant in tryton corresponding to the
        combination_record.
        If found, return the same else create a new one and return that.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created variant
        """
        pass

    @classmethod
    def create_using_ps_data(cls, combination_record):
        """Create a variant from the product record sent by prestashop client

        First look if this product already exists. If yes, it returns the same.
        Else create a new one. This search process is delegated to
        `get_product_using_ps_data`.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created product
        """
        pass

    @classmethod
    def get_product_using_ps_data(cls, combination_record):
        """Find an existing product in Tryton which matches the details
        of this combination_record.
        By default, it matches the prestashop_combination_id and site.

        :param combination_record: Objectified XML record sent by pystashop
        :returns: Active record if a product is found else None
        """
        pass

    @classmethod
    def get_product_using_ps_id(cls, combination_record_id):
        """Find an existing product in Tryton which matches the
        combination_record_id.
        By default, it matches the prestashop_combination_id and site.

        :param combination_record_id: Combination ID on prestashop
        :returns: Active record if a product is found else None
        """
        pass
