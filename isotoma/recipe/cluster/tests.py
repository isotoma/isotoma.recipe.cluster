"""Test setup for isotoma.recipe.apache.
"""

import os, re
import pkg_resources

import zc.buildout.testing

import unittest
import zope.testing
from zope.testing import doctest, renormalizing


def setUp(test):
    zc.buildout.testing.buildoutSetUp(test)
    zc.buildout.testing.install_develop('isotoma.recipe.cluster', test)
    zc.buildout.testing.install('PyYAML', test)
    zc.buildout.testing.install('zope.testing', test)


checker = renormalizing.RENormalizing([
    zc.buildout.testing.normalize_path,
    (re.compile('#![^\n]+\n'), ''),
    (re.compile('-\S+-py\d[.]\d(-\S+)?.egg'),
     '-pyN.N.egg',
    ),
    ])


def test_suite():
    tests = [
        "doctests/simple-usage.txt",
        ]

    suites = []
    for test in tests:
        suites.append(doctest.DocFileSuite(test,
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS, checker=checker))

    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
