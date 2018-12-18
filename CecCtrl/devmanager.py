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

class Interactor(object):
    """
    Base class for all interactors.
    """
    def __init__(self, device_manager, *args, **kwargs):
        super(Interactor, self).__init__(*args, **kwargs)
        self._dev_mgr = device_manager
        self._is_done = False
        
    def start(self):
        pass
    
    def handle_message(self, msg):
        pass
    
    def handle_timeout(self):
        pass
    
    def isDone(self):
        return self._is_done
        
    def _done(self):
        self._is_done = True
        
    def _set_timeout(self, wait_time):
        self._dev_mgr.set_interactor_timeout(wait_time)
        
    def _send_message(self, msg):
        self._dev_mgr.fire(cec_write(msg), "cec")


class SendMessage(Interactor):
    """
    An interactor that simply sends a message.
    """
    def __init__(self, device_manager, message, *args, **kwargs):
        super(SendMessage, self).__init__(device_manager, *args, **kwargs)
        self._message = message

    def start(self):
        self._send_message(self._message)
        self._done()


class PowerOnTv(Interactor):
    """
    An interactor that powers on the TV.
    """
    def __init__(self, device_manager, *args, **kwargs):
        super(PowerOnTv, self).__init__(device_manager, *args, **kwargs)
        self._attempts = 0

    def start(self):
        self._power_on()

    def _power_on(self):
        if self._attempts == 9:
            # Give up
            self._done()
            return
        if self._attempts % 3 == 0:
            # "Push" power on
            self._send_message(CecMessage(16, 0, 0x04, []))            
        # Request power status
        self._send_message(CecMessage(16, 0, 0x8f, []))
        self._set_timeout(1)
        self._attempts += 1

    def handle_message(self, msg):
        if msg.cmd == 0x90 and msg.srcAddr == 0:
            if msg.data[0] == 0:
                self._done()
                return
            self._power_on()
    
    def handle_timeout(self):
        self._power_on()
    

class PowerOnAudio(Interactor):
    """
    An interactor that powers on the audio device.
    """
    def __init__(self, device_manager, *args, **kwargs):
        super(PowerOnAudio, self).__init__(device_manager, *args, **kwargs)
        self._attempts = 0

    def start(self):
        self._power_on()

    def _power_on(self):
        if self._attempts == 9:
            # Give up
            self._done()
            return
        if self._attempts % 3 == 0:
            # "Push" power on
            self._send_message(CecMessage(16, 5, 0x44, [0x6d]))            
            self._send_message(CecMessage(16, 5, 0x45, []))            
        # Request power status
        self._send_message(CecMessage(16, 5, 0x8f, []))
        self._set_timeout(1)
        self._attempts += 1

    def handle_message(self, msg):
        if msg.cmd == 0x90 and msg.srcAddr == 5:
            if msg.data[0] == 0:
                self._done()
                return
            self._power_on()
    
    def handle_timeout(self):
        self._power_on()
    

class poll_next_info(Event):
    pass


class interactor_timeout(Event):
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
        self._active_source_change_pending = False
        self._active_remote = 0
        self._next_to_check = 0
        self._poll_timer = None
        self._poll_complete = False
        # Interactor support
        self._interactor_queue = []
        self._interactor_timer = None
        # Settings
        self._power_on_audio = False

    @handler("config_value", channel="configuration")
    def _on_config_value(self, section, option, value):
        if section == "device_manager":
            if option == "power_on_audio":
                self._power_on_audio = (value == "True")
    
    def _interact(self, interactor):
        self._interactor_queue.append(interactor)
        if len(self._interactor_queue) == 1:
            interactor.start()
            self._check_interactor_queue()

    def _check_interactor_queue(self):
        while True:
            if len(self._interactor_queue) == 0 \
                    or not self._interactor_queue[0].isDone():
                return
            # Done with this one
            if self._interactor_timer:
                self._interactor_timer.unregister()
                self._interactor_timer = None
            self._interactor_queue.pop(0)
            if len(self._interactor_queue) > 0:
                self._interactor_queue[0].start()
            
    def set_interactor_timeout(self, wait_time):
        if self._interactor_timer or wait_time == 0:
            self._interactor_timer.unregister()
        if wait_time > 0:
            Timer(wait_time, interactor_timeout(), "dev-mgr").register(self)
    
    @handler("interactor_timeout")
    def _on_interactor_timeout(self, event):
        self._interactor_timer = None
        # fail safe
        if len(self._interactor_queue) == 0:
            return
        self._interactor_queue[0].handle_timeout()
        self._check_interactor_queue()
            
    @handler("started", channel="*")
    def _on_started(self, event, *args):
        # Request active source
        self.fire(cec_write(CecMessage(16, 15, 0x85, [])), "cec")
        self._poll_timer = Timer(15, poll_next_info(), "dev-mgr").register(self)

    @handler("poll_next_info")
    def _on_poll_next_info(self, event):
        self._poll_timer = None
        self._poll_complete = False
        # Check for missing infos of knwon devices
        if self._request_missing():
            self._poll_timer = Timer(2, poll_next_info(), "dev-mgr").register(self)
            return
        # Check for devices
        while self._next_to_check < 15 and (self._next_to_check in [12, 13]
                                            or self._next_to_check in self._devices):
            self._next_to_check += 1
        if self._next_to_check < 15:
            # Give physical address
            self.fire(cec_write(CecMessage(16, self._next_to_check, 0x83, [])),
                      "cec")
            self._next_to_check += 1;
            self._poll_timer = Timer(2, poll_next_info(), "dev-mgr").register(self)
            return;
        self._poll_complete = True

    def _request_missing(self):
        for _, device in self._devices.items():
            # Request missing information, one by one
            if device.physical_address is None:
                self.fire(cec_write(CecMessage(16, device.logical_address, 0x83, [])), "cec")
                return True;
            if not device._osd_name_requested:
                # osd name support is optional, so just try once and see what we get
                self.fire(cec_write(CecMessage(16, device.logical_address, 0x46, [])), "cec")
                device._osd_name_requested = True
                return True;
            if not device._vendor_id_requested:
                # vendor id support is optional, so just try once and see what we get
                self.fire(cec_write(CecMessage(16, device.logical_address, 0x8c, [])), "cec")
                device._vendor_id_requested = True
                return True;
        return False

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        msg = event.msg

        # State changes            
        if msg.cmd == 0x82: # Active source
            if self._active_source != msg.srcAddr:
                self._active_source = msg.srcAddr
                self._active_source_change_pending = True

        # Forward to interactors
        if len(self._interactor_queue) > 0:
            self._interactor_queue[0].handle_message(msg)
            self._check_interactor_queue()
    
        # Update our model of existing devices and their state
        if msg.srcAddr == 15:
            # Source is broadcast, nothing to gain here
            return
        if not msg.srcAddr in self._devices:
            # New device!
            self._devices[msg.srcAddr] = Device(self, msg.srcAddr)
            self.fire(log(logging.INFO,
                          "New: %s" % (self._devices[msg.srcAddr])), "logger")
            if self._poll_timer is None and self._request_missing():
                self._poll_timer = Timer(2, poll_next_info(), "dev-mgr").register(self)
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
        except:
            # We sometimes get faulty messages...
            pass
        if not self._poll_complete:
            return
        # Pending change of active source?
        if self._active_source_change_pending and device.physical_address:
            # We have collected everything required (and most of the optional infos)
            self._active_remote = device.logical_address
            self.fire(dev_update_remote(device))
            self._active_source_change_pending = False

    @handler("dev_report")
    def _on_dev_report(self, event):
        for _,v in self._devices.items():
            self.fire(dev_status(v))

    @handler("dev_send_key")
    def _on_dev_send_key(self, event):
        self.fire(cec_write(CecMessage(16, self._active_remote, 0x44, [event.code])), "cec")
        self.fire(cec_write(CecMessage(16, self._active_remote, 0x45, [])), "cec")

    @handler("dev_make_source")
    def _on_dev_make_source(self, event):
        self._active_remote = event.logical_address
        if self._devices[self._active_remote]:
            self.fire(dev_update_remote(self._devices[self._active_remote]))
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
        if device.type != 5:
            # Make sure that we see something, Power on TV and maybe audio
            self._interact(PowerOnTv(self))
            if self._power_on_audio:
                self._interact(PowerOnAudio(self))
        # Special handling for switch to TV
        if event.logical_address == 0:
            if self._active_source > 0:
                # Inactive Source
                self._interact(SendMessage(self,CecMessage(16, 0, 0x9d, [])
                                           .append_physical(
                                               self._devices[self._active_source]
                                               .physical_address)))
            return
        # Set Stream Path
        self._interact(SendMessage(self, CecMessage(16, 15, 0x86, [])
                                   .append_physical(device.physical_address)))

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

class dev_update_remote(Event):
    """
    Reports a change of the remote to be displayed.
    """
    
    def __init__(self, device, *args, **kwargs):
        super(dev_update_remote, self).__init__(*args, **kwargs)
        self.device = device

class dev_send_key(Event): 
    """
    Send the given code to the active device.
    """
    
    def __init__(self, code, *args, **kwargs):
        super(dev_send_key, self).__init__(*args, **kwargs)
        self.code = code

