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
import yaml
from zc.buildout import UserError, easy_install

class Cluster(object):

    def __init__(self, buildout, name, options):
        self.buildout = buildout
        self.name = name
        self.options = options

    def install(self):
        pybin = self.buildout["buildout"]["executable"]
        bindir = self.buildout['buildout']['bin-directory']

        try:
            config = yaml.load(self.options["services"])
        except:
            raise UserError("Error parsing yaml")

        ws = easy_install.working_set(
            ["PyYAML"], pybin,
            [self.buildout["buildout"]['develop-eggs-directory'], self.buildout['buildout']['eggs-directory']])

        initialization = \
            'services = """%(services)s"""\n' + \
            'bindir = "%(bindir)s"\n' + \
            'varrundir = "%(varrundir)s"\n'

        initialization = initialization % {
            "services": self.options["services"],
            "bindir": bindir,
            "varrundir": self.options.get("varrun-directory", os.path.join(self.buildout['buildout']['directory'],"var","run")),
            }

        scripts = easy_install.scripts(
            [(self.name, "isotoma.recipe.cluster.ctl", "main")],
            ws, pybin, bindir, initialization=initialization, arguments='services, bindir, varrundir')

        return [os.path.join(bindir, self.name)]


