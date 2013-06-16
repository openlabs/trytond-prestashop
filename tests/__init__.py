# -*- coding: utf-8 -*-
"""
    __init__

    :copyright: © 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
import unittest
import trytond.tests.test_tryton

from test_prestashop import TestPrestashop
from test_party import TestParty
from test_product import TestProduct
from test_sale import TestSale

def suite():
    "Prestashop integration test suite"
    test_suite = trytond.tests.test_tryton.suite()
    test_suite.addTests([
        unittest.TestLoader().loadTestsFromTestCase(TestPrestashop),
        unittest.TestLoader().loadTestsFromTestCase(TestParty),
        unittest.TestLoader().loadTestsFromTestCase(TestProduct),
        unittest.TestLoader().loadTestsFromTestCase(TestSale),
    ])
    return test_suite

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())
