# Copyright (C) 2006-2007 Red Hat, Inc.
# Copyright (C) 2008 One Laptop Per Child
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import logging
from gettext import gettext as _

import gtk

from sugar import profile
from sugar.graphics.tray import TrayIcon
from sugar.graphics import style
from sugar.graphics.palette import Palette

from jarabe.model.devices import device
from jarabe.model.devices import wireless
from jarabe.model import network
from jarabe.frame.frameinvoker import FrameWidgetInvoker

class DeviceView(TrayIcon):

    FRAME_POSITION_RELATIVE = 400

    def __init__(self, model):
        TrayIcon.__init__(self, icon_name='network-mesh')

        self._model = model

        self.palette = MeshPalette(_("Mesh Network"), model)
        self.set_palette(self.palette)
        self.palette.props.invoker = FrameWidgetInvoker(self)
        self.palette.set_group_id('frame')

        model.connect('notify::state', self._state_changed_cb)
        model.connect('notify::activation-stage', self._state_changed_cb)
        self._update_state()

    def _state_changed_cb(self, model, pspec):
        self._update_state()

    def _update_state(self):
        # FIXME Change icon colors once we have real icons
        state = self._model.props.state
        self.palette.update_state(state)

        if state == device.STATE_ACTIVATING:
            self.icon.props.fill_color = style.COLOR_INACTIVE_FILL.get_svg()
            self.icon.props.stroke_color = style.COLOR_INACTIVE_STROKE.get_svg()
        elif state == device.STATE_ACTIVATED:
            self.icon.props.xo_color = profile.get_color()
        elif state == device.STATE_INACTIVE:
            self.icon.props.fill_color = style.COLOR_INACTIVE_FILL.get_svg()
            self.icon.props.stroke_color = style.COLOR_INACTIVE_STROKE.get_svg()

        if state == device.STATE_INACTIVE:
            self.palette.set_primary_text(_("Mesh Network"))
        else:
            chan = wireless.freq_to_channel(self._model.props.frequency)
            if chan > 0:
                self.palette.set_primary_text(_("Mesh Network") + " %d" % chan)
            self.palette.set_mesh_step(self._model.props.mesh_step, state)

class MeshPalette(Palette):
    def __init__(self, primary_text, model):
        Palette.__init__(self, primary_text, menu_after_content=True)
        self._model = model

        self._step_label = gtk.Label()
        self._step_label.show()

        vbox = gtk.VBox()
        vbox.pack_start(self._step_label)
        vbox.show()

        self.set_content(vbox)

        self._disconnect_item = gtk.MenuItem(_('Disconnect...'))
        self._disconnect_item.connect('activate', self._disconnect_activate_cb)
        self.menu.append(self._disconnect_item)

    def update_state(self, state):
        if state == device.STATE_ACTIVATED:
            self._disconnect_item.show()
        else:
            self._disconnect_item.hide()

    def _disconnect_activate_cb(self, menuitem):
        # Disconnection for an mesh means activating the default mesh device
        # again without a channel
        network_manager = network.get_manager()
        nm_device = self._model.get_nm_device()
        if network_manager and nm_device:
            network_manager.set_active_device(nm_device)

    def set_mesh_step(self, step, state):
        label = ""
        if step == 1:
            if state == device.STATE_ACTIVATED:
                label = _("Connected to a School Mesh Portal")
            elif state == device.STATE_ACTIVATING:
                label = _("Looking for a School Mesh Portal...")
        elif step == 3:
            if state == device.STATE_ACTIVATED:
                label = _("Connected to an XO Mesh Portal")
            elif state == device.STATE_ACTIVATING:
                label = _("Looking for an XO Mesh Portal...")
        elif step == 4:
            if state == device.STATE_ACTIVATED:
                label = _("Connected to a Simple Mesh")
            elif state == device.STATE_ACTIVATING:
                label = _("Starting a Simple Mesh")

        if len(label):
            self._step_label.set_text(label)
        else:
            logging.debug("Unhandled mesh step %d" % step)
            self._step_label.set_text(_("Unknown Mesh"))

