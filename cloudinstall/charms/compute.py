#
# compute.py - Nova Compute Charm instructions
#
# Copyright 2014 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
from cloudinstall.charms import CharmBase, DisplayPriorities

log = logging.getLogger('cloudinstall.charms.compute')


class CharmNovaCompute(CharmBase):
    """ Openstack Nova Compute directives """

    charm_name = 'nova-compute'
    display_name = 'Compute'
    menuable = True
    display_priority = DisplayPriorities.Compute
    related = ['mysql', 'glance', 'nova-cloud-controller']
    isolate = True
    constraints = {'mem': 4096,
                   'root-disk': 40960}
    allow_multi_units = True

    def set_relations(self):
        controller = self.wait_for_agent('nova-cloud-controller')
        if not controller:
            return True
        for charm in self.related:
            log.debug("{1} adding relation to {0}".format(
                charm, self.display_name))
            self.juju.add_relation(self.charm_name,
                                   charm)

        service = self.juju_state.service(self.charm_name)
        has_amqp = list(filter(lambda r: 'amqp' in r.relation_name,
                        service.relations))
        if len(has_amqp) == 0:
            log.debug("Setting amqp relation for compute.")
            self.juju.add_relation("{c}:amqp".format(
                                   c=self.charm_name),
                                   "rabbitmq-server:amqp")
            return False

__charm_class__ = CharmNovaCompute
