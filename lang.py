# -*- coding: utf-8 -*-
"""
    lang

    :copyright: (c) 2013-2015 by Openlabs Technologies & Consulting (P) Limited
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
    languages on prestashop as per prestashop channel.
    It determines what languages are allowed to be synced.
    """
    __name__ = 'prestashop.site.lang'

    # TODO: Table name need to be renamed with migration

    name = fields.Char('Name', required=True, readonly=True)
    language = fields.Many2One('ir.lang', 'Language')
    channel = fields.Many2One(
        'sale.channel', 'Channel', required=True, ondelete='CASCADE',
    )
    prestashop_id = fields.Integer('Prestashop ID', required=True)

    @staticmethod
    def default_channel():
        "Return default site from context"
        return Transaction().context.get('current_channel')

    @classmethod
    def __setup__(cls):
        super(SiteLanguage, cls).__setup__()
        cls._error_messages.update({
            'language_not_found': 'Language with code %s not found',
        })
        cls._sql_constraints += [(
            'prestashop_id_site_language_uniq',
            'UNIQUE(prestashop_id, channel, language)',
            'Language must be unique by prestashop id and channel'
        )]

    @classmethod
    def get_channel_languages(cls, channel=None):
        """
        Get the list of tryton languages for a channel for which PS langs exist
        """
        SaleChannel = Pool().get('sale.channel')

        if not channel:
            channel = SaleChannel(Transaction().context.get('current_channel'))

        return cls.search([('channel', '=', channel.id)])

    @classmethod
    def search_using_ps_id(cls, prestashop_id):
        """
        Search for a language using the given ps_id in the current channel

        :param prestashop_id: Prestashop ID for the language
        :returns: Langauge record found or None
        """
        site_langs = cls.search([
            ('prestashop_id', '=', prestashop_id),
            ('channel', '=', Transaction().context.get('current_channel'))
        ])

        return site_langs and site_langs[0] or None

    @classmethod
    def create_using_ps_data(cls, lang_record):
        """
        Create a record in `prestashop.site.lang` with the languages
        corresponding to prestashop_id

        Tryton fetches the languages from prestashop and tries to find a best
        match for the language in tryton.

        Prestashop stores language codes in two formats, i.e., ISO 639‑1 2
        character codes and IETF language tags where the ISO 639‑1 2 character
        code can be combined with the ISO 3166-1 country 2 character code via
        hyphen(-). The default language codes used by prestashop does not seem
        to adhere to any of the above though. We take into consideration the
        IETF language tags based codes from prestashop and match with tryton.

        Tryton uses IETF best practice of using the 2 character language code
        in combination with the ISO 3166-1 country code separated by an
        undersrcore. For example, Tryton uses en_US to represent English as
        used in the United States and en_GB for English as used in the Great
        Britain.

        English (en) is a special case and is always mapped to en_US since the
        language is bundled with the standard installation of Prestashop and
        claims to be English United States.

        :param ps_lang: Objectified XML data for the language
        :return: Created record
        """
        Language = Pool().get('ir.lang')
        SaleChannel = Pool().get('sale.channel')

        channel = SaleChannel(Transaction().context.get('current_channel'))

        channel.validate_prestashop_channel()

        if lang_record.language_code.pyval == 'en':
            tryton_lang = Language.search([('code', '=', 'en_US')])
        else:
            lang_code, country_code = lang_record.language_code.pyval.split('-')
            tryton_lang = Language.search([
                ('code', '=', '_'.join([lang_code, country_code.upper()]))
            ])
        site_lang, = SiteLanguage.create([{
            'name': lang_record.name.pyval,
            'channel': channel.id,
            'prestashop_id': lang_record.id.pyval,
            'language': tryton_lang and tryton_lang[0].id or None,
        }])

        return site_lang


class Language:
    "Language"
    __name__ = 'ir.lang'

    @classmethod
    def get_using_ps_id(cls, prestashop_id):
        """
        Return the language corresponding to the prestashop_id for the
        current site in context
        If the language is not found, fetch it from remote.
        Try to link the remote language to a local language.
        If not found, it will show the user the exception sent by prestashop

        :param prestashop_id: Prestashop ID for the language
        :returns: Active record of the language
        """
        SiteLanguage = Pool().get('prestashop.site.lang')
        SaleChannel = Pool().get('sale.channel')

        site_language = SiteLanguage.search_using_ps_id(prestashop_id)

        if not site_language:
            channel = SaleChannel(Transaction().context.get('current_channel'))
            channel.validate_prestashop_channel()

            client = channel.get_prestashop_client()
            site_language = [SiteLanguage.create_using_ps_data(
                client.languages.get(prestashop_id)
            )]

        return site_language.language
