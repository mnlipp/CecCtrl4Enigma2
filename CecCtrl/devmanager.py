"""
..
   This file is part of the CEC Control plugin.
   Copyright (C) 2018 Michael N. Lipp
   
   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.
   
   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.

.. moduleauthor:: mnl
"""
from circuits.core.handlers import handler
from circuits.core.components import Component
from circuits_bricks.app.logger import log
import logging
from .cec import deviceType
from .events import dev_update

class Device(object):
    
    def __init__(self, manager, logical_address):
        self._manager = manager
        self._logical_address = logical_address
        self._physical_address = None
        self._osd_name = "(unknown)"
        self._type = None

    @property
    def logical_address(self):
        return self._logical_address

    @logical_address.setter
    def logical_address(self, value):
        if self._logical_address != value:
            self._logical_address = value
            self._update()

    @property
    def physical_address(self):
        return self._physical_address
    
    @physical_address.setter
    def physical_address(self, value):
        if self._physical_address != value:
            self._physical_address = value
            self._update()

    @property
    def osd_name(self):
        return self._osd_name

    @osd_name.setter
    def osd_name(self, value):
        if self._osd_name != value:
            self._osd_name = value        
            self._update()

    @property
    def type(self):
        return self._type
    
    @type.setter
    def type(self, value):
        if self._type != value:
            self._type = value
            self._update()

    def _update(self):
        if not self._physical_address is None:
            self._manager.fire(dev_update(self))

    def __str__(self):
        return "Device \"%s\" (%s) at (%d)[%s]" \
            % (self.osd_name, 
               "?" if self.type is None else deviceType[self.type],
               self.logical_address,
               ":".join(map(str,self.physical_address)) if self.physical_address else "?")

class DeviceManager(Component):

    channel = "dev-mgr"

    def __init__(self, *args, **kwargs):
        super(DeviceManager, self).__init__(*args, **kwargs)
        self._devices = {}

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        msg = event.msg
        if not msg.srcAddr in self._devices and msg.srcAddr != 15:
            self._devices[msg.srcAddr] = Device(self, msg.srcAddr)
            self.fire(log(logging.INFO,
                          "New: %s" % (self._devices[msg.srcAddr])), "logger")
        if msg.srcAddr != 15:
            device = self._devices[msg.srcAddr]
            if msg.cmd == 0x84: # Report Physical Address
                device.physical_address = msg.physical_at(0);
                device.type = msg.data[2]
                self.fire(log(logging.INFO, "Updated: %s" % (device)), "logger")
            if msg.cmd == 0x47: # Give OSD Name
                device.osd_name = "".join(list(map(chr,msg.data[0:])))
                self.fire(log(logging.INFO, "Updated: %s" % (device)), "logger")
