# -*- coding: utf-8 -*-
"""
    party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Party', 'Address', 'ContactMechanism']
__metaclass__ = PoolMeta


class Party:
    "Party"
    __name__ = 'party.party'

    prestashop_id = fields.Integer('Prestashop ID', readonly=True)
    prestashop_site = fields.Many2One(
        'prestashop.site', 'Prestashop Site', readonly=True
    )

    @classmethod
    def __setup__(cls):
        "Setup"
        super(Party, cls).__setup__()
        cls._sql_constraints += [
            ('prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, prestashop_site)',
                'Party must be unique by prestashop id and site'
            )
        ]

    @staticmethod
    def default_prestashop_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def find_or_create_using_ps_data(cls, customer_record):
        """Look for the party in tryton corresponding to the customer_record.
        If found, return the same else create a new one and return that.

        :param customer_record: Objectified XML record sent by pystashop
        :returns: Active record of created party
        """
        pass

    @classmethod
    def create_using_ps_data(cls, customer_record):
        """Create a party from the customer record sent by prestashop client.

        :param customer_record: Objectified XML record sent by pystashop
        :returns: Active record of created party
        """
        pass

    @classmethod
    def get_party_using_ps_data(cls, customer_record):
        """Find a party in Tryton which matches the details
        of this customer_record.
        By default it just matches the prestashop_id and site

        :param customer_record: Objectified XML record sent by prestashop
        :returns: Active record if a party is found else None
        """
        pass


class Address:
    "Address"
    __name__ = 'party.address'

    prestashop_id = fields.Integer('Prestashop ID', readonly=True)
    prestashop_site = fields.Function(
        fields.Many2One('prestashop.site', 'Prestashop Site', readonly=True),
        'get_prestashop_site'
    )

    def get_prestashop_site(self, name):
        """Return the site from the party as site on party is site on address

        :param name: Name of the field
        """
        return self.party.prestashop_site and self.party.prestashop_site.id \
                or None

    @classmethod
    def find_or_create_for_party_using_ps_data(
            cls, party, address_record):
        """Look for the address in tryton corresponding to the address_record.
        If found, return the same else create a new one and return that.

        :param address_record: Objectified XML record sent by pystashop
        :param party: Active Record of Party
        :returns: Active record of created address
        """
        pass

    @classmethod
    def create_for_party_using_ps_data(cls, party, address_record):
        """Create address from the address record given and link it to the
        party.

        :param address_record: Objectified XML record sent by pystashop
        :param party: Active Record of Party
        :returns: Active record of created address
        """
        pass

    def match_with_ps_data(self, address_record):
        """Match the current address with the address_record.
        Match all the fields of the address, i.e., streets, city, subdivision
        and country. For any deviation in any field, returns False.

        :param address_record: Objectified XML record sent by pystashop
        :returns: True if address found else False
        """
        pass


class ContactMechanism:
    "Contact Mechanism"
    __name__ = 'party.contact_mechanism'

    @classmethod
    def find_or_create_using_dict(cls, data):
        """Find or create the contact mechanisms sent in data.

        :param data: A list of dictionaries in the format:
            [{
                'party': <Party ID>,
                'type': '<type of mechanism>',
                'value': '<value to be created>'
            }]
        :returns: Active records of created/found records
        """
        pass
