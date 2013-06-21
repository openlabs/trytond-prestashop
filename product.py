# -*- coding: utf-8 -*-
"""
    product

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from decimal import Decimal

from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Product', 'Template', 'TemplatePrestashop', 'ProductPrestashop']
__metaclass__ = PoolMeta


class TemplatePrestashop(ModelSQL, ModelView):
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
            (
                'prestashop_id_site_uniq',
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
        template = cls.get_template_using_ps_data(product_record)

        if not template:
            template = cls.create_using_ps_data(product_record)

        return template

    @classmethod
    def create_using_ps_data(cls, product_record):
        """Create a template from the product record sent by prestashop client

        ..note:: Product name and description from product record are stored a
        level deeper than other values. They are stored under a language
        object under name and description objects.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created template
        """
        Product = Pool().get('product.product')
        Uom = Pool().get('product.uom')
        Site = Pool().get('prestashop.site')
        SiteLang = Pool().get('prestashop.site.lang')

        site = Site(Transaction().context.get('prestashop_site'))

        # The name of a product can be in multiple languages
        # If the name is in more than one language, create the record with
        # name in first language (if a corresponding one exists on tryton) and
        # updates the rest of the names in different languages by switching the
        # language in context
        # Same applies to description as well
        name_in_langs = product_record.name.getchildren()
        desc_in_langs = product_record.description.getchildren()

        name_in_first_lang = name_in_langs.pop(0)
        desc_in_first_lang = desc_in_langs[0]
        site_lang = SiteLang.search_using_ps_id(
            int(name_in_first_lang.get('id'))
        )

        # Product name and description can be in different first languages
        # So create the variant with description only if the first language is
        # same on both
        if name_in_first_lang.get('id') == desc_in_first_lang.get('id'):
            desc_in_first_lang = desc_in_langs.pop(0)
            variant_data = {
                'code': product_record.reference.pyval or None,
                'description': desc_in_first_lang.pyval,
                'prestashop_combination_ids': [('create', [{
                    'prestashop_combination_id': 0,
                }])]
            }
        else:
            variant_data = {
                'code': product_record.reference.pyval or None,
                'prestashop_combination_ids': [('create', [{
                    'prestashop_combination_id': 0,
                }])]
            }

        # For a product in prestashop, create a template and a product in
        # tryton.
        unit, = Uom.search([('name', '=', 'Unit')], limit=1)
        with Transaction().set_context(language=site_lang.language.code):
            template, = cls.create([{
                'name': name_in_first_lang.pyval,
                'list_price': Decimal(str(product_record.price)),
                'cost_price': Decimal(str(product_record.wholesale_price)),
                'salable': True,
                'default_uom': unit.id,
                'sale_uom': unit.id,
                'account_expense': site.default_account_expense.id,
                'account_revenue': site.default_account_revenue.id,
                'products': [('create', [variant_data])],
                'prestashop_ids': [('create', [{
                    'prestashop_id': product_record.id.pyval,
                }])]
            }])

        # If there is only lang for name, control wont go to this loop
        for name_in_lang in name_in_langs:
            # Write the name in other languages
            site_lang = SiteLang.search_using_ps_id(
                int(name_in_lang.get('id'))
            )
            if not site_lang:
                continue
            with Transaction().set_context(language=site_lang.language.code):
                cls.write([template], {
                    'name': name_in_lang.pyval,
                })

        # If there is only lang for description which has already been used,
        # control wont go to this loop
        for desc_in_lang in desc_in_langs:
            # Write the description in other languages
            site_lang = SiteLang.search_using_ps_id(
                int(desc_in_lang.get('id'))
            )
            if not site_lang:
                continue
            with Transaction().set_context(language=site_lang.language.code):
                Product.write(template.products, {
                    'description': desc_in_lang.pyval,
                })

        return template

    @classmethod
    def get_template_using_ps_data(cls, product_record):
        """Find an existing template in Tryton which matches the details
        of this product_record. This search is made in the
        TemplatePrestashop store.

        By default, it matches the prestashop_id and site.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record if a template is found else None
        """
        TemplatePrestashop = Pool().get('product.template.prestashop')

        records = TemplatePrestashop.search([
            ('prestashop_id', '=', product_record.id.pyval),
            ('site', '=', Transaction().context.get('prestashop_site'))
        ])

        return records and records[0].template or None

    @classmethod
    def get_template_using_ps_id(cls, product_record_id):
        """Find an existing template in Tryton which matches the
        product_record_id. This search is made in the
        TemplatePrestashop store.

        By default, it matches the prestashop_id and site.

        :param product_record_id: Product ID on prestashop
        :returns: Active record if a template is found else None
        """
        TemplatePrestashop = Pool().get('product.template.prestashop')

        records = TemplatePrestashop.search([
            ('prestashop_id', '=', product_record_id),
            ('site', '=', Transaction().context.get('prestashop_site'))
        ])

        return records and records[0].template or None


class ProductPrestashop(ModelSQL, ModelView):
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
            'duplicate_combination': (
                'Combination with id '
                '"%(combination_id)s" exists for template "%(template)s" '
                'in %(site)s'
            ),
            'duplicate_combination_across_site': (
                'Combination with id '
                '"%(combination_id)s" exists in site "%(site)s"'
            ),
        })

    @classmethod
    def validate(cls, records):
        """Checks that the combination_id for a product is unique within a
        template.

        :param records: List of active records
        """
        super(ProductPrestashop, cls).validate(records)
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
        if self.prestashop_combination_id != 0 and len(
            ProductPrestashop.search([
                ('prestashop_combination_id', '=',
                    self.prestashop_combination_id),
                ('site', '=', self.site),
            ]
            )
        ) > 1:
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

    @classmethod
    def find_or_create_using_ps_data(cls, combination_record):
        """Look for the variant in tryton corresponding to the
        combination_record.
        If found, return the same else create a new one and return that.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created variant
        """
        product = cls.get_product_using_ps_data(combination_record)
        if not product:
            product = cls.create_using_ps_data(combination_record)

        return product

    @classmethod
    def create_using_ps_data(cls, combination_record):
        """Create a variant from the product record sent by prestashop client

        First look if this product already exists. If yes, it returns the same.
        Else create a new one. This search process is delegated to
        `get_product_using_ps_data`.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created product
        """
        Template = Pool().get('product.template')
        PrestashopSite = Pool().get('prestashop.site')

        site = PrestashopSite(Transaction().context.get('prestashop_site'))
        client = site.get_prestashop_client()

        template = Template.find_or_create_using_ps_data(client.products.get(
            combination_record.id_product.pyval
        ))
        product, = cls.create([{
            'template': template.id,
            'code': combination_record.reference.pyval or None,
            'prestashop_combination_ids': [('create', [{
                'prestashop_combination_id': combination_record.id.pyval,
            }])]
        }])

        return product

    @classmethod
    def get_product_using_ps_data(cls, combination_record):
        """Find an existing product in Tryton which matches the details
        of this combination_record.
        By default, it matches the prestashop_combination_id and site.

        :param combination_record: Objectified XML record sent by pystashop
        :returns: Active record if a product is found else None
        """
        ProductPrestashop = Pool().get('product.product.prestashop')

        records = ProductPrestashop.search([
            ('prestashop_combination_id', '=', combination_record.id.pyval),
            ('site', '=', Transaction().context.get('prestashop_site'))
        ])

        return records and records[0].product or None

    @classmethod
    def get_product_using_ps_id(cls, combination_record_id):
        """Find an existing product in Tryton which matches the
        combination_record_id.
        By default, it matches the prestashop_combination_id and site.

        :param combination_record_id: Combination ID on prestashop
        :returns: Active record if a product is found else None
        """
        ProductPrestashop = Pool().get('product.product.prestashop')

        records = ProductPrestashop.search([
            ('prestashop_combination_id', '=', combination_record_id),
            ('site', '=', Transaction().context.get('prestashop_site'))
        ])

        return records and records[0].product or None
