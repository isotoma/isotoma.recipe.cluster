# Copyright 2010 Isotoma Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os, sys, subprocess, shlex
import yaml


class BaseService(object):

    @property
    def pid(self):
        pidfile = self.pidfile
        if not os.path.exists(pidfile):
            return None

        pid = open(pidfile).read().strip()
        try:
            pid = int(pid)
        except:
            return None

        return pid

    def alive(self):
        pid = self.pid

        if not pid:
            return False

        # Try kill() with signal 0
        # No exceptions means the pid is alive
        #  Special case: if we dont have permissions, give up
        try:
            os.kill(pid, 0)
            return True
        except OSError, e:
            if e.errno == 3:
                if "No such process" in e.strerror:
                    return False
                raise SystemExit("We don't have permission to check the status of that pid")
        return False


class Service(BaseService):

    """ I am a service that can be stopped and started and can report my status """

    def __init__(self, bindir, varrundir, service, settings):
        self.bindir = bindir
        self.varrundir = varrundir
        self.service = service
        self.settings = settings

    @property
    def start_command(self):
        if "start-command" in self.settings:
            return self.settings["start-command"]
        return "%s start", os.path.join(self.bindir, "bin", self.service)

    @property
    def stop_command(self):
        if "stop-command" in self.settings:
            return self.settings["stop-command"]
        return "%s stop", os.path.join(self.bindir, "bin", self.service)

    @property
    def pidfile(self):
        if "pidfile" in self.settings:
            return self.settings["pidfile"]
        return os.path.join(self.varrundir, "var", "%s.pid" % self.service)

    def start(self):
        print "Attempting to start %s" % self.service

        if self.alive():
            print >>sys.stderr, " >> Service is already started"
            return 0

        p = subprocess.Popen(shlex.split(self.start_command))
        p.wait()

        if not self.alive():
            print >>sys.stderr, " >> Service is not running"
            return 1

        return 0

    def stop(self):
        print "Attempting to stop %s" % self.service

        if not self.alive():
            print >>sys.stderr, " >> Service is already stopped"
            return 0

        p = subprocess.Popen(shlex.split(self.stop_command))
        p.wait()

        if self.alive():
            print >>sys.stderr, " >> Service is still running"
            return 1

        return 0


class Services(object):

    """ I am a collection of services that can be start, stopped, restarted and query for their status as a group """

    def __init__(self, bindir, varrundir, services):
        self.services = []
        for service, values in services.iteritems():
            self.services.append(bindir, varrundir, service, values or {})

    def start(self):
        """ start everything in the list of daemons """
        for service in self.services:
            service.start()

    def stop(self):
        """ reverse the list of daemons, then stop everything """
        services = self.services[:]
        services.reverse()
        for service in services:
            service.stop()

    def restart(self):
        """ stop all of the daemons, then start them again """
        self.stop()
        self.start()

    def status(self):
        """ iterate a dictionary of daemon information and get status info """
        for service in self.services:
            service.status()


def main(services_yaml, bindir, varrundir):
    if len(sys.argv) != 2:
        return 1

    services = Services(bindir, varrundir, yaml.load(services_yaml))

    if sys.argv[1] == "start":
        return services.start()
    elif sys.argv[1] == "stop":
        return services.stop()
    elif sys.argv[1] == "restart":
        return services.restart()
    elif sys.argv[1] == "status":
        return services.status()

    print >>sys.stderr, "%(name) (start|stop|restart|status)" % name
    return 1


