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
from .cec import deviceType, CecMessage
from .cecadapter import cec_write
from circuits.core.events import Event
from circuits.core.timers import Timer

class Device(object):
    """
    Represents a device with all information collected from CEC messages.
    """
    
    def __init__(self, manager, logical_address):
        self._manager = manager
        self._logical_address = logical_address
        self._physical_address = None
        self._osd_name = None
        self._osd_name_requested = False
        self._vendor_id = None
        self._vendor_id_requested = False
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
        return self._osd_name if self._osd_name else "(Unknown)"

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

    @property
    def vendor_id(self):
        return self._vendor_id
    
    @vendor_id.setter
    def vendor_id(self, value):
        if self._vendor_id != value:
            self._vendor_id = value
            self._update()

    def _update(self):
        if not self._physical_address is None:
            self._manager.fire(dev_status(self))

    def __str__(self):
        return "Device \"%s\" (%s) at (%d)[%s]" \
            % (self.osd_name, 
               "?" if self.type is None else deviceType[self.type],
               self.logical_address,
               ":".join(map(str,self.physical_address)) if self.physical_address else "?")

class check_next_device(Event):
    pass

class DeviceManager(Component):
    """
    A directory of all known devices.
    """

    channel = "dev-mgr"

    def __init__(self, *args, **kwargs):
        super(DeviceManager, self).__init__(*args, **kwargs)
        self._devices = {}
        self._active_source = -1
        self._active_change_pending = False
        self._next_to_check = 0

    @handler("started", channel="*")
    def _on_started(self, event, *args):
        # Request active source
        self.fire(cec_write(CecMessage(16, 15, 0x85, [])), "cec")
        self._poll_timer = Timer(0.2, check_next_device(), "dev-mgr").register(self)

    @handler("check_next_device")
    def _on_check_next_device(self, event):
        while self._next_to_check in [12, 13] \
            or self._next_to_check in self._devices:
            self._next_to_check += 1
        if self._next_to_check < 15:
            # Give physical address
            self.fire(cec_write(CecMessage(16, self._next_to_check, 0x83, [])),
                      "cec")
            self._next_to_check += 1;
        if self._next_to_check < 15:
            self._poll_timer = Timer(0.2, check_next_device(), "dev-mgr").register(self)

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        msg = event.msg
        if msg.srcAddr == 15:
            # Source is broadcast, nothing to gain here
            return
        if not msg.srcAddr in self._devices:
            # New device!
            self._devices[msg.srcAddr] = Device(self, msg.srcAddr)
            self.fire(log(logging.INFO,
                          "New: %s" % (self._devices[msg.srcAddr])), "logger")
        device = self._devices[msg.srcAddr]
        try:
            if msg.cmd == 0x84: # Report Physical Address
                device.physical_address = msg.physical_at(0);
                device.type = msg.data[2]
                self.fire(log(logging.INFO, "Updated: %s" % (device)), "logger")
            if msg.cmd == 0x47: # Set OSD Name
                device.osd_name = msg.string_at(0)
                self.fire(log(logging.INFO, "Updated: %s" % (device)), "logger")
            if msg.cmd == 0x87: # Device Vendor ID
                device.vendor_id = msg.data[0] << 16 | msg.data[1] << 8 | msg.data[2]
            if msg.cmd == 0x82: # Active source
                if self._active_source != msg.srcAddr:
                    self._active_source = msg.srcAddr
                    self._active_change_pending = True
        except:
            # We sometimes get faulty messages...
            pass
        # Request missing information, one by one
        if device.physical_address is None:
            self.fire(cec_write(CecMessage(16, msg.srcAddr, 0x83, [])), "cec")
            return;
        if not device._osd_name_requested:
            # osd name support is optional, so just try once and see what we get
            self.fire(cec_write(CecMessage(16, msg.srcAddr, 0x46, [])), "cec")
            device._osd_name_requested = True
            return;
        if not device._vendor_id_requested:
            # vendor id support is optional, so just try once and see what we get
            self.fire(cec_write(CecMessage(16, msg.srcAddr, 0x8c, [])), "cec")
            device._vendor_id_requested = True
            return;
        # Pending change of active source?
        if self._active_change_pending and device.physical_address:
            # We have collected everything required (and most of the optional infos)
            self.fire(dev_source_changed(device))
            self._active_change_pending = False

    @handler("dev_report")
    def _on_dev_report(self, event):
        for _,v in self._devices.items():
            self.fire(dev_status(v))

    @handler("dev_send_key")
    def _on_dev_send_key(self, event):
        if self._active_source >= 0: 
            self.fire(cec_write(CecMessage(16, self._active_source, 0x44, [event.code])), "cec")
            self.fire(cec_write(CecMessage(16, self._active_source, 0x45, [])), "cec")
            
            
    @handler("dev_make_source")
    def _on_dev_make_source(self, event):
        if not event.logical_address in self._devices:
            self.fire(log(logging.DEBUG, "Cannot make source: unknown device %d"
                          % (event.logical_address)), "logger")
            return
        device = self._devices[event.logical_address]
        if device.physical_address is None:
            self.fire(log(logging.DEBUG, 
                          "Cannot make source: missing physical address for %d"
                          % (event.logical_address)), "logger")
            return
        # Special handling for switch to TV
        if event.logical_address == 0:
            if self._active_source > 0:
                self.fire(cec_write(CecMessage(16, 0, 0x9d, [])
                                    .append_physical(self._devices[self._active_source]
                                                     .physical_address)), "cec")
            return
        # Set Stream Path
        self.fire(cec_write(CecMessage(16, 15, 0x86, [])
                            .append_physical(device.physical_address)), "cec")

class dev_status(Event):
    """
    Reports a device status after a change or after explicit request. 
    """
    
    def __init__(self, device, *args, **kwargs):
        super(dev_status, self).__init__(*args, **kwargs)
        self.device = device

    def __str__(self):
        return "dev_status(" + str(self.device) + ")"

class dev_report(Event):
    """
    Trigger the reporting of the status for each known device.
    """
    pass

class dev_make_source(Event):
    """
    Try to make the specified device the active device.
    """ 

    def __init__(self, logical_address, *args, **kwargs):
        super(dev_make_source, self).__init__(*args, **kwargs)
        self.logical_address = logical_address

class dev_source_changed(Event):
    """
    Reports a change of the active device.
    """
    
    def __init__(self, device, *args, **kwargs):
        super(dev_source_changed, self).__init__(*args, **kwargs)
        self.device = device

class dev_send_key(Event): 
    """
    Send the given code to the active device.
    """
    
    def __init__(self, code, *args, **kwargs):
        super(dev_send_key, self).__init__(*args, **kwargs)
        self.code = code

