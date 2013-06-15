#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool
from .prestashop import *
from .country import *
from .currency import *
from .party import *
from .product import *
from .sale import *
from .lang import *


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
