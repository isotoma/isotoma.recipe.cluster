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

import os, sys, subprocess, shlex, time, pwd, grp, ConfigParser

try:
    import simplejson as json
except ImportError:
    import json


class NothingToDo(Exception):
    pass


class ActionFailed(Exception):
    pass


class BaseService(object):

    """ I am a service that has a pidfile and can report whether i am alive or not """

    @property
    def pid(self):
        """ I read the pidfile and return it """
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
        """ I check if my pid is alive """
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
        return "%s start" % os.path.join(self.bindir, self.service)

    @property
    def stop_command(self):
        if "stop-command" in self.settings:
            return self.settings["stop-command"]
        return "%s stop" % os.path.join(self.bindir, self.service)

    @property
    def pidfile(self):
        if "pidfile" in self.settings:
            return self.settings["pidfile"]
        return os.path.join(self.varrundir, "%s.pid" % self.service)

    @property
    def env(self):
        if "env" in self.settings:
            return self.settings["env"]
        return None

    @property
    def user(self):
        return self.settings.get("user", None)

    def get_command(self, command, user):
        cmd = []

        if user and pwd.getpwnam(user).pw_uid != os.getuid():
            cmd = ["sudo", "-u", user]

        cmd.extend(shlex.split(command.encode("UTF-8")))
        return cmd

    def start(self):
        """ I attempt to to start a service """

        print "Attempting to start %s" % self.service

        if self.alive():
            raise NothingToDo("Service already running")
            return 1

        p = subprocess.Popen(self.get_command(self.start_command, self.user), env=self.env)
        p.wait()

        if p.returncode != 0:
            raise ActionFailed("Start script reported error")

        for i in range(100):
            time.sleep(0.1)
            if self.alive():
                return

        if not self.alive():
            raise ActionFailed("Could not start service")


    def stop(self):
        """ I attempt to to stop a service """

        print "Attempting to stop %s (pid=%s)" % (self.service, self.pid)

        if not self.alive():
            raise NothingToDo("Service is already stopped")

        p = subprocess.Popen(self.get_command(self.stop_command, self.user), env=self.env)
        p.wait()

        if p.returncode != 0:
            raise ActionFailed("Stop script reported error")

        for i in range(100):
            time.sleep(0.1)
            if not self.alive():
                return

        if self.alive():
            raise ActionFailed("Service wouldn't shut down")

    def status(self):
        pid = self.pid or "no pid"
        if self.alive():
            print "'%s' is alive (%s)." % (self.service, pid)
        else:
            print "'%s' is not running." % self.service


class Services(object):

    """ I am a collection of services that can be start, stopped, restarted and query for their status as a group """

    def __init__(self, bindir, varrundir, services):
        self.services = []
        for service in services:
            self.services.append(Service(bindir, varrundir, service["name"], service))

    def start(self):
        """ I start everything in the list of daemons """
        for service in self.services:
            try:
                service.start()
            except NothingToDo:
                print "Skipped as already running"

    def stop(self):
        """ I reverse the list of daemons, then stop everything """
        errorflag = False

        services = self.services[:]
        services.reverse()
        for service in services:
            try:
                service.stop()
            except NothingToDo:
                # if service is already stopped, we just carry on
                print "Skipped as already stopped"
            except ActionFailed, e:
                print e.args[0]
                errorflag = True

        if errorflag:
            raise ActionFailed("Not all services shut down")

    def restart(self):
        """ I stop all of the daemons, then start them again """
        self.stop()
        self.start()

    def status(self):
        """ I iterate a dictionary of daemon information and get status info """
        for service in self.services:
            service.status()


def main(path):
    if len(sys.argv) != 2:
        return 1

    config = ConfigParser.RawConfigParser()
    config.read(path)

    user = config.get('cluster', 'user')
    owner = config.get('cluster', 'owner')
    bindir = config.get('cluster', 'bindir')
    varrundir = config.get('cluster', 'varrundir')

    svcinf = [dict(config.items(s)) for s in config.get('cluster', 'services').strip().split(" ")]

    if len(user.strip()) > 0 and user != pwd.getpwuid(os.getuid()).pw_name:
        print >>sys.stderr, "Only '%s' is allowed to run this script" % user
        return

    if not os.path.exists(varrundir):
        os.makedirs(varrundir)
        os.chown(varrundir, pwd.getpwnam(owner).pw_uid, grp.getgrnam(owner).gr_gid)
        os.chmod(varrundir, 0755)

    services = Services(bindir, varrundir, svcinf)

    try:
        if sys.argv[1] == "start":
            return services.start()
        elif sys.argv[1] == "stop":
            return services.stop()
        elif sys.argv[1] == "restart":
            return services.restart()
        elif sys.argv[1] == "status":
            return services.status()
    except NothingToDo, e:
        print >>sys.stderr, "Nothing To Do:", e.args[0]
        sys.exit(0)
    except ActionFailed, e:
        print >>sys.stderr, "Action Failed:", e.args[0]
        sys.exit(1)

    print >>sys.stderr, "%s (start|stop|restart|status)" % name
    sys.exit(0)


