"""Test setup for isotoma.recipe.apache.
"""

import os, sys, subprocess, re
import pkg_resources

import zc.buildout.testing

import unittest
import zope.testing
from zope.testing import doctest, renormalizing

from isotoma.recipe.cluster.ctl import BaseService, Service

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

def sibpath(path):
    return os.path.join(os.path.dirname(__file__), path)

class TestCtl(unittest.TestCase):

    def raw_test_service(self, pid, command):
        env = os.environ.copy()
        env["PYTHONPATH"] = ":".join(sys.path)
        p = subprocess.Popen([sys.executable, sibpath("testservice.py"), os.path.realpath(pid), command], env=env)
        p.wait()

    def service(self, pid):
        s = Service("", "", "cluster", {
            "pidfile": os.path.realpath(pid),
            "start-command": " ".join((sys.executable, sibpath("testservice.py"), os.path.realpath(pid), "start")),
            "stop_command": " ".join((sys.executable, sibpath("testservice.py"), os.path.realpath(pid), "stop")),
            })
        return s

    def raw_start_service(self, pid):
        self.raw_test_service(pid, "start")

    def raw_stop_service(self, pid):
        self.raw_test_service(pid, "stop")

    def status_service(self, pid):
        c = BaseService()
        c.pidfile = os.path.realpath(pid)
        return c.alive()

    def test_testservice(self):
        self.failUnless(not self.status_service("a.pid"), "Test environment wasnt clean")
        self.raw_start_service("a.pid")
        self.failUnless(self.status_service("a.pid"), "Couldnt start testservice")
        self.raw_stop_service("a.pid")
        self.failUnless(not self.status_service("a.pid"), "Couldnt stop testservice")

    def test_service_start(self):
        s = self.service("a.pid")
        s.start()
        self.failUnless(self.status_service("a.pid"))
        self.raw_stop_service("a.pid")

    def test_service_alive(self):
        s = self.service("a.pid")
        self.failUnless(not s.alive())
        s.start()
        self.failUnless(s.alive())

def test_suite():
    tests = [
        "doctests/simple-usage.txt",
        ]

    suites = []
    for test in tests:
        suites.append(doctest.DocFileSuite(test,
            setUp=setUp, tearDown=zc.buildout.testing.buildoutTearDown,
            optionflags=doctest.ELLIPSIS, checker=checker))

    suites.append(unittest.TestLoader().loadTestsFromTestCase(TestCtl))

    return unittest.TestSuite(suites)


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
