# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: (c) 2015 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""

from trytond.pool import Pool
from prestashop import (
    Site, ImportWizardView, ExportWizardView,
    ConnectionWizardView, ExportWizard, ConnectionWizard
)
from country import (
    Country, Subdivision, CountryPrestashop, SubdivisionPrestashop
)
from currency import CurrencyPrestashop, Currency
from party import Party, Address, ContactMechanism
from product import Template, TemplatePrestashop, Product, ProductPrestashop
from sale import Sale, SaleLine, SiteOrderState
from lang import Language, SiteLanguage


def register():
    "Register classes with pool"
    Pool.register(
        Site,
        ImportWizardView,
        ExportWizardView,
        ConnectionWizardView,
        Country,
        Subdivision,
        CountryPrestashop,
        SubdivisionPrestashop,
        Currency,
        CurrencyPrestashop,
        Language,
        SiteLanguage,
        Party,
        Address,
        ContactMechanism,
        Template,
        TemplatePrestashop,
        Product,
        ProductPrestashop,
        Sale,
        SaleLine,
        SiteOrderState,
        module='prestashop', type_='model')
    Pool.register(
        ImportWizard,
        ExportWizard,
        ConnectionWizard,
        module='prestashop', type_='wizard')
