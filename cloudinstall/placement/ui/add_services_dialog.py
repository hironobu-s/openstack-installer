# Copyright 2015 Canonical, Ltd.
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

from urwid import (AttrMap, Button, Columns, Divider, GridFlow,
                   LineBox, Pile, SelectableIcon, WidgetWrap)

from cloudinstall.placement.controller import AssignmentType
from cloudinstall.placement.ui.services_list import ServicesList
from cloudinstall.state import CharmState

log = logging.getLogger('cloudinstall.placement')


BUTTON_SIZE = 20


class AddServicesDialog(WidgetWrap):
    """ Dialog to add services. Does not specify placement.

    :param cb: callback routine to process submit/cancel actions
    """

    def __init__(self, install_controller, deploy_cb, cancel_cb):
        self.install_controller = install_controller
        self.orig_pc = install_controller.placement_controller
        self.pc = self.orig_pc.get_temp_copy()
        self.charms = []
        self.deploy_cb = deploy_cb
        self.cancel_cb = cancel_cb
        self.boxes = []
        w = self.build_widget()
        self.update()

        super().__init__(w)

    def build_widget(self, **kwargs):

        def remove_p(charm_class):
            n = self.pc.assignment_machine_count_for_charm(charm_class)
            return n > 0

        def not_conflicted_p(cc):
            state, _, _ = self.pc.get_charm_state(cc)
            return state != CharmState.CONFLICTED

        actions = [(remove_p, 'Remove', self.do_remove),
                   (not_conflicted_p, 'Add', self.do_add)]
        self.required_sl = ServicesList(self.pc,
                                        actions, actions,
                                        show_type='required',
                                        show_placements=True,
                                        title="Required for Deploy")
        self.unrequired_undeployed_sl = ServicesList(self.pc,
                                                     actions, actions,
                                                     ignore_deployed=True,
                                                     title="Un-Deployed")
        self.deployed_sl = ServicesList(self.pc,
                                        actions, actions,
                                        deployed_only=True,
                                        show_placements=True,
                                        title="Deployed Services")

        self.assigned_sl = ServicesList(self.pc,
                                        actions, actions,
                                        assigned_only=True,
                                        show_placements=True,
                                        title="Services to be Deployed")

        self.buttons = []
        self.button_grid = GridFlow(self.buttons, 22, 1, 1, 'center')
        self.pile1 = Pile([self.required_sl,
                               self.unrequired_undeployed_sl])
        self.pile2 = Pile([self.deployed_sl])
        self.pile3 = Pile([self.assigned_sl])
        return LineBox(Pile([Columns([self.pile1, self.pile2, self.pile3]),
                             Divider(),
                             self.button_grid]),
                       title="Add Services")

    def update(self):
        self.required_sl.update()
        self.unrequired_undeployed_sl.update()
        self.deployed_sl.update()
        self.assigned_sl.update()
        self.update_buttons()

    def update_buttons(self):
        buttons = [(AttrMap(Button("Cancel", self.handle_cancel),
                            'button_primary', 'button_primary focus'),
                    self.button_grid.options())]
        n_assigned = len(self.pc.assigned_services)
        if n_assigned > 0 and self.pc.can_deploy():
            b = AttrMap(Button("Deploy", self.handle_deploy),
                        'button_primary', 'button_primary focus')
        else:
            b = AttrMap(SelectableIcon("(Deploy)"),
                        'disabled_button',
                        'disabled_button_focus')
        buttons.append((b, self.button_grid.options()))
        self.button_grid.contents = buttons

    def do_add(self, sender, charm_class):
        """Add the selected charm using default juju location.
        Equivalent to a simple 'juju deploy foo'
        """
        self.pc.assign(self.pc.def_placeholder, charm_class,
                       AssignmentType.DEFAULT)
        self.update()

    def do_remove(self, sender, charm_class):
        "Undo an assignment"
        self.pc.remove_one_assignment(self.pc.def_placeholder,
                                      charm_class)
        self.update()

    def handle_deploy(self, button):
        """Commits changes to the main placement controller, and calls the
        deploy callback to do the rest.
        """
        self.orig_pc.update_from_controller(self.pc)
        self.deploy_cb()

    def handle_cancel(self, button):
        self.cancel_cb()
