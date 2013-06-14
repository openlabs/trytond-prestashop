# -*- coding: utf-8 -*-
"""
    lang

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import ModelSQL, ModelView, fields
from trytond.transaction import Transaction
from trytond.pool import Pool, PoolMeta


__all__ = [
    'SiteLanguage', 'Language'
]
__metaclass__ = PoolMeta


class SiteLanguage(ModelSQL, ModelView):
    """Prestashop site language

    This model keeps a store of tryton languages corresponding to the
    languages on prestashop as per prestashop site.
    It determines what languages are allowed to be synced.
    """
    __name__ = 'prestashop.site.lang'

    name = fields.Char('Name', required=True, readonly=True)
    language = fields.Many2One('ir.lang', 'Language')
    site = fields.Many2One(
        'prestashop.site', 'Site', required=True, ondelete='CASCADE',
    )
    prestashop_id = fields.Integer('Prestashop ID', required=True)

    @staticmethod
    def default_site():
        "Return default site from context"
        return Transaction().context.get('prestashop_site')

    @classmethod
    def __setup__(cls):
        super(SiteLanguage, cls).__setup__()
        cls._error_messages.update({
            'language_not_found': 'Language with code %s not found',
        })
        cls._sql_constraints += [
            ('prestashop_id_site_uniq',
                'UNIQUE(prestashop_id, site)',
                'Language must be unique by prestashop id and site'
            )
        ]


class Language:
    "Language"
    __name__ = 'ir.lang'

    @classmethod
    def get_using_ps_id(cls, prestashop_id):
        """Return the language corresponding to the prestashop_id for the
        current site in context
        If the language is not found, fetch it from remote.
        Try to link the remote language to a local language.
        If not found, it will show the user the exception sent by prestashop

        :param prestashop_id: Prestashop ID for the language
        :returns: Active record of the language
        """
        pass
