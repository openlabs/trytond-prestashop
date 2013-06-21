# -*- coding: utf-8 -*-
"""
    sale

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from datetime import datetime
from decimal import Decimal

import pytz

from trytond.model import ModelSQL, ModelView, fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Sale', 'SaleLine', 'SiteOrderState']
__metaclass__ = PoolMeta


class SiteOrderState(ModelSQL, ModelView):
    """Prestashop Site map with tryton order states

    This model enables the user to configure the corresponding order states in
    tryton for the order states on prestashop
    """
    __name__ = 'prestashop.site.order_state'
    _rec_name = 'prestashop_state'

    site = fields.Many2One(
        'prestashop.site', 'Prestashop Site', readonly=True,
        ondelete='CASCADE',
    )
    prestashop_id = fields.Integer('Prestashop ID', required=True)
    prestashop_state = fields.Char(
        'Prestashop Order State', required=True, readonly=True, translate=True,
    )
    order_state = fields.Selection([
        ('sale.confirmed', 'Sale - Confirmed'),
        ('sale.processing', 'Sale - Processing'),
        ('sale.done', 'Sale - Done'),
        ('sale.cancel', 'Sale - Canceled'),
        ('shipment.waiting', 'Shipment - Waiting'),
        ('shipment.sent', 'Shipment - Sent'),
    ], 'Order State')

    import_orders = fields.Boolean('Import Orders in this state')   # TODO
    invoice_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('shipment', 'On Shipment Sent'),
        ], 'Invoice Method',
    )
    shipment_method = fields.Selection([
            ('manual', 'Manual'),
            ('order', 'On Order Processed'),
            ('invoice', 'On Invoice Paid'),
        ], 'Shipment Method',
    )

    @staticmethod
    def default_import_orders():
        "Return True"
        return True

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        "Setup"
        super(SiteOrderState, cls).__setup__()
        cls._sql_constraints += [
            (
                'prestashop_id_site_uniq', 'UNIQUE(prestashop_id, site)',
                'Prestashop State must be unique for a prestashop site'
            )
        ]

    @classmethod
    def search_using_ps_id(cls, prestashop_id):
        """Search for a order state using the given ps_id in the current site

        :param prestashop_id: Prestashop ID for the order state
        :returns: Site order state record found or None
        """
        site_order_states = cls.search([
            ('prestashop_id', '=', prestashop_id),
            ('site', '=', Transaction().context.get('prestashop_site'))
        ])

        return site_order_states and site_order_states[0] or None

    @classmethod
    def get_tryton_state(cls, name):
        """Get the tryton state corresponding to the prestashop state
        as per the predefined logic
        This method currently expects the value of name to be in US English.

        :param name: Name of the PS state

        :returns: A dictionary of tryton state and shipment and invoice methods
        """
        # Map the tryton states according to the order states from
        # prestashop The user can later configure this according to his
        # needs.
        if name in ('Shipped', 'Delivered'):
            return {
                'order_state': 'shipment.sent',
                'invoice_method': 'manual',
                'shipment_method': 'manual'
            }
        elif name == 'Canceled':
            return {
                'order_state': 'sale.cancel',
                'invoice_method': 'manual',
                'shipment_method': 'manual'
            }
        elif name in (
            'Payment accepted', 'Payment remotely accepted',
        ):
            return {
                'order_state': 'sale.processing',
                'invoice_method': 'order',
                'shipment_method': 'invoice'
            }
        elif name == 'Preparation in progress':
            return {
                'order_state': 'sale.processing',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }
        else:
            return {
                'order_state': 'sale.confirmed',
                'invoice_method': 'order',
                'shipment_method': 'order'
            }

    @classmethod
    def create_using_ps_data(cls, state_data):
        """Create a record for the order state corresponding to state_data

        :param state_data: Objectified XML data for order state
        :return: Created record
        """
        Site = Pool().get('prestashop.site')
        SiteLanguage = Pool().get('prestashop.site.lang')

        site = Site(Transaction().context.get('prestashop_site'))

        # The name of a state can be in multiple languages
        # If the name is in more than one language, create the record with
        # name in first language (if a corresponding one exists on tryton) and
        # updates the rest of the names in different languages by switching the
        # language in context
        name_in_langs = state_data.name.getchildren()

        name_in_first_lang = name_in_langs.pop(0)
        site_lang = SiteLanguage.search_using_ps_id(
            int(name_in_first_lang.get('id'))
        )
        with Transaction().set_context(language=site_lang.language.code):
            vals = {
                'site': site.id,
                'prestashop_id': state_data.id.pyval,
                'prestashop_state': name_in_first_lang.pyval,
            }
            vals.update(cls.get_tryton_state(name_in_first_lang.pyval))
            site_order_state = cls.create([vals])[0]

        # If there is only lang, control wont go to this loop
        for name_in_lang in name_in_langs:
            # Write the name in other languages
            site_lang = SiteLanguage.search_using_ps_id(
                int(name_in_lang.get('id'))
            )
            if not site_lang:
                continue
            with Transaction().set_context(language=site_lang.language.code):
                cls.write([site_order_state], {
                    'prestashop_state': name_in_lang.pyval,
                })
        return site_order_state


class Sale:
    "Sale"
    __name__ = 'sale.sale'

    prestashop_id = fields.Integer('Prestashop ID', readonly=True)
    prestashop_site = fields.Many2One(
        'prestashop.site', 'Prestashop Site', readonly=True
    )

    @staticmethod
    def default_prestashop_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        "Setup"
        super(Sale, cls).__setup__()
        cls._sql_constraints += [
            (
                'prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, prestashop_site)',
                'Sale must be unique by prestashop id and site'
            )
        ]
        cls._error_messages.update({
            'prestashop_site_not_found':
            'Prestashop client not found in context'
        })

    @classmethod
    def find_or_create_using_ps_data(cls, order_record):
        """Look for the sale in tryton corresponding to the order_record.
        If found, return the same else create a new one and return that.

        :param product_record: Objectified XML record sent by pystashop
        :returns: Active record of created sale
        """
        sale = cls.get_order_using_ps_data(order_record)

        if not sale:
            sale = cls.create_using_ps_data(order_record)

        return sale

    @classmethod
    def create_using_ps_data(cls, order_record):
        """Create an order from the order record sent by prestashop client

        :param order_record: Objectified XML record sent by pystashop
        :returns: Active record of created sale
        """
        Party = Pool().get('party.party')
        Address = Pool().get('party.address')
        ContactMechanism = Pool().get('party.contact_mechanism')
        Line = Pool().get('sale.line')
        PrestashopSite = Pool().get('prestashop.site')
        Currency = Pool().get('currency.currency')
        SiteOrderState = Pool().get('prestashop.site.order_state')

        site = PrestashopSite(Transaction().context.get('prestashop_site'))
        client = site.get_prestashop_client()

        if not client:
            cls.raise_user_error('prestashop_site_not_found')

        party = Party.find_or_create_using_ps_data(
            client.customers.get(order_record.id_customer.pyval)
        )

        # Get the sale date and convert the time to UTC from the application
        # timezone set on site
        sale_time = datetime.strptime(
            order_record.date_add.pyval, '%Y-%m-%d %H:%M:%S'
        )
        site_tz = pytz.timezone(site.timezone)
        sale_time_utc = pytz.utc.normalize(site_tz.localize(sale_time))

        inv_address = Address.find_or_create_for_party_using_ps_data(
            party,
            client.addresses.get(order_record.id_address_invoice.pyval),
        )
        ship_address = Address.find_or_create_for_party_using_ps_data(
            party,
            client.addresses.get(order_record.id_address_delivery.pyval),
        )
        sale_data = {
            'reference': str(order_record.id.pyval),
            'description': order_record.reference.pyval,
            'sale_date': sale_time_utc.date(),
            'party': party.id,
            'invoice_address': inv_address.id,
            'shipment_address': ship_address.id,
            'warehouse': site.default_warehouse and site.default_warehouse.id \
                or None,
            'prestashop_id': order_record.id.pyval,
            'currency': Currency.get_using_ps_id(
                order_record.id_currency.pyval
            ),
        }

        ps_order_state = SiteOrderState.search_using_ps_id(
            order_record.current_state.pyval
        )

        sale_data['invoice_method'] = ps_order_state.invoice_method
        sale_data['shipment_method'] = ps_order_state.shipment_method

        lines_data = []
        for order_line in order_record.associations.order_rows.iterchildren():
            lines_data.append(
                Line.get_line_data_using_ps_data(order_line)
            )

        if Decimal(str(order_record.total_shipping)):
            lines_data.append(
                Line.get_shipping_line_data_using_ps_data(
                order_record
            ))
        if Decimal(str(order_record.total_discounts)):
            lines_data.append(
                Line.get_discount_line_data_using_ps_data(
                order_record
            ))

        sale_data['lines'] = [('create', lines_data)]

        sale, = cls.create([sale_data])

        assert sale.total_amount == Decimal(str(
            order_record.total_paid_tax_excl)), 'The order total do not match'

        sale.process_state_using_ps_data(ps_order_state)

        return sale

    def process_state_using_ps_data(self, order_state):
        """Process Sale state as per the current state

        :param order_state: Site order state corresponding to ps order state
        """
        Sale = Pool().get('sale.sale')
        Invoice = Pool().get('account.invoice')

        client = self.prestashop_site.get_prestashop_client()

        # Cancel the order if its cancelled on prestashop
        if order_state.order_state == 'sale.cancel':
            Sale.cancel([self])
            return

        # Confirm and process the order in any other case
        Sale.quote([self])
        Sale.confirm([self])

        if order_state.order_state != 'sale.confirmed':
            Sale.process([self])

    @classmethod
    def get_order_using_ps_data(cls, order_record):
        """Find an existing order in Tryton which matches the details
        of this order_record. By default it just matches the prestashop_id.

        :param order_record: Objectified XML record sent by prestashop
        :returns: Active record if a sale is found else None
        """
        sales = cls.search([
            ('prestashop_id', '=', order_record.id.pyval),
            ('prestashop_site', '=', Transaction().context.get(
                'prestashop_site')
            )
        ])

        return sales and sales[0] or None

    def export_status_to_ps(self):
        """Update the status of this order in prestashop based on the order
        state in Tryton.

        """
        SiteOrderState = Pool().get('prestashop.site.order_state')

        client = self.prestashop_site.get_prestashop_client()
        def get_state(state_id):
            "Returns the id of prestashop state corresponding to tryton state"
            return client.order_states.get_list(
                filters={'id': state_id}, as_ids=True
            )[0]

        # Get the corresponding PS state from site order states as the state
        # of state
        site_order_state = SiteOrderState.search([
            ('order_state', '=', 'sale.' + self.state)
        ])
        if not site_order_state:
            return
        else:
            prestashop_state = get_state(site_order_state[0].prestashop_id)

        order = client.orders.get(self.prestashop_id)
        order.current_state = prestashop_state
        result = client.orders.update(order.id, order)

        return result.order


class SaleLine:
    "Sale Line"
    __name__ = 'sale.line'

    @classmethod
    def get_line_data_using_ps_data(cls, order_row_record):
        """Create the sale line from the order_row_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        Product = Pool().get('product.product')
        Template = Pool().get('product.template')
        PrestashopSite = Pool().get('prestashop.site')

        site = PrestashopSite(Transaction().context.get('prestashop_site'))
        client = site.get_prestashop_client()

        # If the product sold is a variant, then get product from
        # product.product
        if order_row_record.product_attribute_id.pyval != 0:
            product = Product.get_product_using_ps_id(
                order_row_record.product_attribute_id.pyval
            ) or Product.find_or_create_using_ps_data(
                client.combinations.get(
                    order_row_record.product_attribute_id.pyval
                )
            )
        else:
            template = Template.get_template_using_ps_id(
                order_row_record.product_id.pyval
            ) or Template.find_or_create_using_ps_data(
                client.products.get(
                    order_row_record.product_id.pyval
                )
            )
            product = template.products[0]

        order_details = client.order_details.get(order_row_record.id.pyval)

        # FIXME: The number of digits handled in unit price should actually
        # from sale currency but the sale is not created yet.
        # We dont have order_data from prestashop either in this method.
        # How to do it? Use global variable or a class variable?
        return {
            'quantity': order_details.product_quantity.pyval,
            'product': product.id,
            'unit': product.sale_uom.id,
            'unit_price': Decimal(str(
                order_details.unit_price_tax_excl
            )).quantize(Decimal(10) ** - site.company.currency.digits),
            'description': order_details.product_name.pyval,
        }

    @classmethod
    def get_taxes_data_using_ps_data(cls, order_record):
        """Create taxes using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        # TODO: Handle taxes and create taxes on sale lines
        pass

    @classmethod
    def get_shipping_line_data_using_ps_data(cls, order_record):
        """Create shipping line using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        PrestashopSite = Pool().get('prestashop.site')

        site = PrestashopSite(Transaction().context.get('prestashop_site'))
        return {
            'quantity': 1,
            'unit_price': Decimal(str(
                order_record.total_shipping_tax_excl
            )).quantize(Decimal(10) ** - site.company.currency.digits),
            'description': 'Shipping Cost [Excl tax]',
        }

    @classmethod
    def get_discount_line_data_using_ps_data(cls, order_record):
        """Create discount line using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        PrestashopSite = Pool().get('prestashop.site')

        site = PrestashopSite(Transaction().context.get('prestashop_site'))
        return {
            'quantity': 1,
            'unit_price': -Decimal(str(
                order_record.total_discounts_tax_excl
            )).quantize(Decimal(10) ** - site.company.currency.digits),
            'description': 'Discount',
        }
