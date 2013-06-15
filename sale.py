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
        """
        # Map the tryton states according to the order states from
        # prestashop The user can later configure this according to his
        # needs.
        if name in ('Shipped', 'Delivered'):
            return 'shipment.sent'
        elif name == 'Canceled':
            return 'sale.cancel'
        elif name in (
            'Payment accepted', 'Payment remotely accepted',
            'Preparation in progress'
        ):
            return 'sale.processing'
        else:
            return 'sale.confirmed'

    @classmethod
    def create_site_order_state_using_ps_data(cls, state_data):
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
            site_order_state = cls.create([{
                'site': site.id,
                'prestashop_id': state_data.id.pyval,
                'prestashop_state': name_in_first_lang.pyval,
                'order_state': cls.get_tryton_state(name_in_first_lang.pyval),
            }])[0]

        # If there is only lang, control wont go to this loop
        for name_in_lang in name_in_langs:
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
        pass

    @classmethod
    def create_using_ps_data(cls, order_record):
        """Create an order from the order record sent by prestashop client

        :param order_record: Objectified XML record sent by pystashop
        :returns: Active record of created sale
        """
        pass

    def process_state_using_ps_data(self, order_state):
        """Process Sale state as per the current state

        :param order_state: State of order on prestashop
        """
        pass

    @classmethod
    def get_order_using_ps_data(cls, order_record):
        """Find an existing order in Tryton which matches the details
        of this order_record. By default it just matches the prestashop_id.

        :param order_record: Objectified XML record sent by prestashop
        :returns: Active record if a sale is found else None
        """
        pass

    def export_status_to_ps(self):
        """Update the status of this order in prestashop based on the order
        state in Tryton.

        """
        pass


class SaleLine:
    "Sale Line"
    __name__ = 'sale.line'

    @classmethod
    def get_line_data_using_ps_data(cls, order_row_record):
        """Create the sale line from the order_row_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        pass

    @classmethod
    def get_taxes_data_using_ps_data(cls, order_record):
        """Create taxes using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        pass

    @classmethod
    def get_shipping_line_data_using_ps_data(cls, order_record):
        """Create shipping line using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        pass

    @classmethod
    def get_discount_line_data_using_ps_data(cls, order_record):
        """Create discount line using details order_record

        :param order_row_record: Objectified XML record sent by pystashop
        :returns: Sale line dictionary of values
        """
        pass
