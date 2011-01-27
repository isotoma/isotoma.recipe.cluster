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

import logging, os, sys
from zc.buildout import UserError, easy_install

try:
    from simplejson as json
except ImportError:
    import json


class Cluster(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

    def install(self):
        pybin = self.buildout["buildout"]["executable"]
        bindir = self.buildout['buildout']['bin-directory']

        serialized = {}
        for name in self.options["services"].split():
            part = self.buildout[name]

            x = serialized[name] = {}
            for key, value in part.items():
                x[key] = value

        ws = easy_install.working_set(
            ["isotoma.recipe.cluster"], pybin,
            [self.buildout["buildout"]['develop-eggs-directory'], self.buildout['buildout']['eggs-directory']])

        initialization = \
            'services = """%(services)s"""\n' + \
            'name = "%(name)s"\n' + \
            'bindir = "%(bindir)s"\n' + \
            'varrundir = "%(varrundir)s"\n'

        initialization = initialization % {
            "services": json.dumps(serialized),
            "name": self.name,
            "bindir": bindir,
            "varrundir": self.options.get("varrun-directory", os.path.join(self.buildout['buildout']['directory'],"var","run")),
            }

        scripts = easy_install.scripts(
            [(self.name, "isotoma.recipe.cluster.ctl", "main")],
            ws, pybin, bindir, initialization=initialization, arguments='services, name, bindir, varrundir')

        return [os.path.join(bindir, self.name)]

