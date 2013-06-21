# -*- coding: utf-8 -*-
"""
    country

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import ModelSQL, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta


__all__ = [
    'CountryPrestashop', 'Country', 'SubdivisionPrestashop', 'Subdivision'
]
__metaclass__ = PoolMeta


class CountryPrestashop(ModelSQL):
    """Prestashop country cache

    This model keeps a store of tryton country corresponding to the country
    on prestashop as per prestashop site.
    This model is used to prevent extra API calls to be sent to prestashop
    to get the country.
    Everytime a country has to be looked up, it is first looked up in this
    model. If not found, a new record is created here.
    """
    __name__ = 'country.country.prestashop'

    country = fields.Many2One('country.country', 'Country', required=True)
    site = fields.Many2One('prestashop.site', 'Site', required=True)
    prestashop_id = fields.Integer('Prestashop ID', required=True)

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        super(CountryPrestashop, cls).__setup__()
        cls._sql_constraints += [
            ('prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, site)',
                'Country must be unique by prestashop id and site'
            )
        ]


class SubdivisionPrestashop(ModelSQL):
    """Prestashop subdivision cache

    This model keeps a store of tryton subdivision corresponding to the state
    on prestashop as per prestashop site.
    This model is used to prevent extra API calls to be sent to prestashop
    to get the subdivision.
    Everytime a subdivision has to be looked up, it is first looked up in this
    model. If not found, a new record is created here.
    """
    __name__ = 'country.subdivision.prestashop'

    subdivision = fields.Many2One(
        'country.subdivision', 'Subdivision', required=True
    )
    site = fields.Many2One('prestashop.site', 'Site', required=True)
    prestashop_id = fields.Integer('Prestashop ID', required=True)

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        super(SubdivisionPrestashop, cls).__setup__()
        cls._sql_constraints += [
            ('prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, site)',
                'Subdivision must be unique by prestashop id and site'
            )
        ]


class Country:
    "Country"
    __name__ = 'country.country'

    @classmethod
    def __setup__(cls):
        super(Country, cls).__setup__()
        cls._error_messages.update({
            'country_not_found': 'Country with code %s not found',
        })

    @classmethod
    def get_using_ps_id(cls, prestashop_id):
        """Return the country corresponding to the prestashop_id for the
        current site in context
        If the country is not found in the cache model, it is fetched from
        remote and a record is created in the cache for future references.

        :param prestashop_id: Prestashop ID for the country
        :returns: Active record of the country
        """
        CountryPrestashop = Pool().get('country.country.prestashop')

        records = CountryPrestashop.search([
            ('site', '=', Transaction().context.get('prestashop_site')),
            ('prestashop_id', '=', prestashop_id)
        ])

        if records:
            return records[0].country
        # Country is not cached yet, cache it and return
        return cls.cache_prestashop_id(prestashop_id)

    @classmethod
    def cache_prestashop_id(cls, prestashop_id):
        """Cache the value of country corresponding to the prestashop_id
        by creating a record in the cache model

        :param prestashop_id: Prestashop ID
        :returns: Active record of the country cached
        """
        CountryPrestashop = Pool().get('country.country.prestashop')
        Site = Pool().get('prestashop.site')

        site = Site(Transaction().context.get('prestashop_site'))
        client = site.get_prestashop_client()

        country_data = client.countries.get(prestashop_id)
        country = cls.search([('code', '=', country_data.iso_code.pyval)])

        if not country:
            cls.raise_user_error(
                'country_not_found', (country_data.iso_code.pyval,)
            )
        CountryPrestashop.create([{
            'country': country[0].id,
            'site': site.id,
            'prestashop_id': prestashop_id,
        }])

        return country and country[0] or None


class Subdivision:
    "Subdivision"
    __name__ = 'country.subdivision'

    @classmethod
    def __setup__(cls):
        super(Subdivision, cls).__setup__()
        cls._error_messages.update({
            'subdivision_not_found': 'Subdivision with code %s not found',
        })

    @classmethod
    def get_using_ps_id(cls, prestashop_id):
        """Return the subdivision corresponding to the prestashop_id for the
        current site in context.
        If the subdivision is not found in the cache model, it is fetched from
        remote and a record is created in the cache for future references.

        :param prestashop_id: Prestashop ID for the subdivision
        :returns: Active record of the subdivision
        """
        SubdivisionPrestashop = Pool().get('country.subdivision.prestashop')

        records = SubdivisionPrestashop.search([
            ('site', '=', Transaction().context.get('prestashop_site')),
            ('prestashop_id', '=', prestashop_id)
        ])

        if records:
            return records[0].subdivision
        # Subdivision is not cached yet, cache it and return
        return cls.cache_prestashop_id(prestashop_id)

    @classmethod
    def cache_prestashop_id(cls, prestashop_id):
        """Cache the value of subdivision corresponding to the prestashop_id
        by creating a record in the cache model

        :param prestashop_id: Prestashop ID
        :returns: Active record of the subdivision cached
        """
        SubdivisionPrestashop = Pool().get('country.subdivision.prestashop')
        Country = Pool().get('country.country')
        Site = Pool().get('prestashop.site')

        site = Site(Transaction().context.get('prestashop_site'))
        client = site.get_prestashop_client()

        state_data = client.states.get(prestashop_id)
        # The country should have been cached till now for sure
        country = Country.get_using_ps_id(state_data.id_country.pyval)
        subdivision = cls.search([
            ('code', '=', country.code + '-' + state_data.iso_code.pyval)
        ])

        if not subdivision:
            cls.raise_user_error(
                'subdivision_not_found', (
                    country.code + '-' + state_data.iso_code.pyval,
                )
            )

        SubdivisionPrestashop.create([{
            'subdivision': subdivision[0].id,
            'site': site.id,
            'prestashop_id': prestashop_id,
        }])

        return subdivision and subdivision[0] or None
