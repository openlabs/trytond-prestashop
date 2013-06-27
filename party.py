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
        party = cls.get_party_using_ps_data(customer_record)

        if not party:
            party = cls.create_using_ps_data(customer_record)

        return party

    @classmethod
    def create_using_ps_data(cls, customer_record):
        """Create a party from the customer record sent by prestashop client.
        Also create the email sent with the party as a contact mechanism.

        :param customer_record: Objectified XML record sent by pystashop
        :returns: Active record of created party
        """
        ContactMechanism = Pool().get('party.contact_mechanism')
        Language = Pool().get('ir.lang')

        # Create the party with the email
        party, = cls.create([{
            'name': ' '.join([
                customer_record.firstname.pyval,
                customer_record.lastname.pyval
            ]),
            'prestashop_id': customer_record.id.pyval,
            'lang': Language.get_using_ps_id(
                customer_record.id_lang.pyval
            ).id if hasattr(customer_record, 'id_lang') else None,
            'contact_mechanisms': [('create', [{
                'type': 'email',
                'value': customer_record.email.pyval,
            }])],
        }])

        return party

    @classmethod
    def get_party_using_ps_data(cls, customer_record):
        """Find a party in Tryton which matches the details
        of this customer_record.
        By default it just matches the prestashop_id and site

        :param customer_record: Objectified XML record sent by prestashop
        :returns: Active record if a party is found else None
        """
        party = cls.search([
            ('prestashop_id', '=', customer_record.id.pyval),
            ('prestashop_site', '=', Transaction().context.get(
                'prestashop_site'
            ))
        ])

        return party and party[0] or None


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
        for address in party.addresses:
            if address.match_with_ps_data(address_record):
                break
        else:
            address = cls.create_for_party_using_ps_data(
                party, address_record
            )

        return address

    @classmethod
    def create_for_party_using_ps_data(cls, party, address_record):
        """Create address from the address record given and link it to the
        party.

        :param address_record: Objectified XML record sent by pystashop
        :param party: Active Record of Party
        :returns: Active record of created address
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')
        ContactMechanism = Pool().get('party.contact_mechanism')

        country = None
        subdivision = None
        if address_record.id_country:
            country = Country.get_using_ps_id(
                address_record.id_country.pyval
            )
        if address_record.id_state:
            subdivision = Subdivision.get_using_ps_id(
                address_record.id_state.pyval
            )
        address, = cls.create([{
            'prestashop_id': address_record.id.pyval,
            'party': party.id,
            'name': ' '.join([
                address_record.firstname.pyval,
                address_record.lastname.pyval
            ]),
            'street': address_record.address1.pyval,
            'streetbis': address_record.address2.pyval or None,
            'zip': unicode(address_record.postcode.pyval),
            'city': address_record.city.pyval,
            'country': country.id if country else None,
            'subdivision': subdivision.id if subdivision else None,
        }])

        # Create phone and/or mobile as a contact mechanism(s)
        contact_data = []
        if address_record.phone:
            contact_data.append({
                'party': party.id,
                'type': 'phone',
                'value': unicode(address_record.phone.pyval),
            })
        if address_record.phone_mobile:
            contact_data.append({
                'party': party.id,
                'type': 'mobile',
                'value': unicode(address_record.phone_mobile.pyval),
            })
        ContactMechanism.find_or_create_using_dict(contact_data)

        return address

    def match_with_ps_data(self, address_record):
        """Match the current address with the address_record.
        Match all the fields of the address, i.e., streets, city, subdivision
        and country. For any deviation in any field, returns False.

        :param address_record: Objectified XML record sent by pystashop
        :returns: True if address found else False
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')

        fields_map = {
            'prestashop_id': 'id',
            'street': 'address1',
            'streetbis': 'address2',
            'zip': 'postcode',
            'city': 'city',
        }
        for key, value in fields_map.items():
            # A string match is needed on both sides because these fields might
            # contains numbers which will be evaluated as number against
            # string
            if unicode(getattr(self, key)) != \
                    (unicode(getattr(address_record, value).pyval) or None):
                return False

        if self.name != u' '.join([
                address_record.firstname.pyval,
                address_record.lastname.pyval
            ]):
            return False

        if address_record.id_country:
            # If no country is found on tryton address return False
            if not self.country:
                return False

            if self.country and \
                    self.country != Country.get_using_ps_id(
                        address_record.id_country.pyval
                    ):
                return False

        if address_record.id_state:
            # If no subdivision is found on tryton address return False
            if not self.subdivision:
                return False

            if self.subdivision != Subdivision.get_using_ps_id(
                        address_record.id_state.pyval
                    ):
                return False

        # If this method reaches here, it means that every field has matched,
        # hence return True
        return True


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
        new_records = []

        for mechanism_data in data:
            # Check if a record exists with the set of values provided
            if not cls.search([
                    ('party', '=', mechanism_data['party']),
                    ('type', '=', mechanism_data['type']),
                    ('value', '=', mechanism_data['value'])
                ]):
                new_records.append(mechanism_data)

        if new_records:
            return cls.create(new_records)
        return []
