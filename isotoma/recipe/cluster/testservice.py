#!/usr/bin/env python

import sys, os, time, atexit
from signal import SIGTERM

from isotoma.recipe.cluster.ctl import BaseService

class TestService(BaseService):

    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile

    def fork(self):
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)
        except OSError, e:
            print >>sys.stderr, "fork failed: %d (%s)\n" % (e.errno, e.strerror)
            sys.exit(1)

    def daemonize(self):
        self.fork()

        os.chdir("/")
        os.setsid()
        os.umask(0)

        # do second fork
        self.fork()

        sys.stdout.flush()
        sys.stderr.flush()
        si = file(self.stdin, 'r')
        so = file(self.stdout, 'a+')
        se = file(self.stderr, 'a+', 0)
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())

        atexit.register(self.cleanup)
        open(self.pidfile,'w').write("%s" % os.getpid())

    def cleanup(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self):
        if self.alive():
            print >>sys.stderr, "Daemon is already running, can't start again"
            return 1

        self.daemonize()
        self.run()

        return 0

    def stop(self):
        if not self.alive():
            print >>sys.stderr, "Daemon is not running, can't stop"
            return 1

        while True:
            try:
                os.kill(self.pid, SIGTERM)
                time.sleep(1)
                if not self.alive():
                    return
            except OSError, err:
                print str(err)
                return 1

        return 0

    def restart(self):
        self.stop()
        self.start()

    def run(self):
        while True:
            time.sleep(1)


def main():
    if len(sys.argv) != 3:
        print >>sys.stderr, "%s (start|stop|restart)" % sys.argv[0]
        return 1

    service = TestService(sys.argv[1])

    if sys.argv[2] == "start":
        return service.start()
    elif sys.argv[2] == "stop":
        return service.stop()
    elif sys.argv[2] == "restart":
        return service.restart()

    print >>sys.stderr, "Unknown command"
    return 2


if __name__ == "__main__":
    sys.exit(main())

