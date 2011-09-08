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

import logging, os, sys, ConfigParser
from zc.buildout import UserError, easy_install

class Cluster(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

        if 'run-directory' in buildout:
            options.setdefault("varrun-directory", buildout['run-directory'])
        else:
            options.setdefault("varrun-directory", os.path.join(self.buildout['buildout']['directory'], "var", "run"))

    def install(self):
        pybin = self.buildout["buildout"]["executable"]
        bindir = self.buildout['buildout']['bin-directory']
        partsdir = os.path.join(self.buildout['buildout']['parts-directory'], self.name)
        cfg = os.path.join(partsdir, "cluster.cfg")

        if not os.path.exists(partsdir):
            os.makedirs(partsdir)

        services = []
        for s in self.options["services"].strip().split():
            s = s.strip()
            if s:
                services.append(s)

        config = ConfigParser.RawConfigParser()

        config.add_section('cluster')
        config.set('cluster', 'services', ' '.join(services))
        config.set('cluster', 'name', self.name)
        config.set('cluster', 'bindir', bindir)
        config.set('cluster', 'varrundir', self.options["varrun-directory"])
        config.set('cluster', 'user', self.options.get("force-user", "root"))
        config.set('cluster', 'owner', self.options.get("owner", "root"))

        for s in services:
            config.add_section(s)
            config.set(s, "name", s)

            part = self.buildout[s]
            for key, value in part.items():
                config.set(s, key, value)

        config.write(open(cfg, 'wb'))

        ws = easy_install.working_set(
            ["isotoma.recipe.cluster"], pybin,
            [self.buildout["buildout"]['develop-eggs-directory'], self.buildout['buildout']['eggs-directory']])

        scripts = easy_install.scripts(
            [(self.name, "isotoma.recipe.cluster.ctl", "main")],
            ws, pybin, bindir, arguments='"%s"' % cfg)

        return [os.path.join(bindir, self.name), cfg]

