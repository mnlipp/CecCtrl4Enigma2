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
from .utils.misc import TemplateController
from circuits.core.handlers import handler
from circuits.web.websockets.dispatcher import WebSocketsDispatcher
import os
import json
import logging
from posixpath import dirname
from circuits.core.components import Component
from circuits_bricks.app.logger import log
from .cec import cecCommands, CecMessage
from .cecadapter import cec_write
from devmanager import dev_report, dev_make_source, dev_send_key
from circuits.io.events import write
from circuits_bricks.app.config import config_value

class RemotePage(TemplateController):

    channel= "/remote"

    def __init__(self, *args, **kwargs):
        super(RemotePage, self).__init__(
            [os.path.join(dirname(__file__), "templates", "remotes")], *args, **kwargs)
        WebSocketsDispatcher(channel="ctrl-ui",
                             path="/remote/socket", 
                             wschannel="remote-control").register(self)
        RemoteControl().register(self)

    @handler("GET")
    def _on_get(self, event, request, response, peer_cert=None):
        if request.path.endswith("/socket"):
            # Let WebSocket dispatch handle this...
            return
        return self.serve_tenjin(request, response, "remote.pyhtml", {})
    
    @handler("dev_update_remote", channel="dev-mgr")
    def _on_dev_update_remote(self, event):
        root = os.path.join(dirname(__file__), "templates", "remotes")
        device = event.device
        paths = []
        if not device.vendor_id is None:
            paths.append(os.path.join(root, str(device.type), "%06X" % (device.vendor_id)))
        paths.append(os.path.join(root, str(device.type)))
        paths.append(root)
        self.update_engine(paths)
  
class RemoteControl(Component):

    channel = "remote-control"

    def __init__(self, *args, **kwargs):
        super(RemoteControl, self).__init__(*args, **kwargs)
        self._connected = []
        self._active_remote = 0
        self._dev_mgr_settings = {}

    @handler("config_value", channel="configuration")
    def _on_config_value(self, section, option, value):
        if section == "device_manager":
            self._dev_mgr_settings[option] = value
            for sock in self._connected:
                self._send_settings(sock)

    def _send_settings(self, sock):
        data = json.dumps({ 
            "settings": {
                "device_manager": self._dev_mgr_settings
            }
        })
        self.fire(write(sock, data))
    
    def connect(self, sock, *args):
        self._connected.append(sock)
        self._send_settings(sock)
        self.fire(dev_report(), "dev-mgr")
        data = json.dumps({ 
            "activeRemote": self._active_remote
        })
        self.fire(write(sock, data))

    def close(self, sock):
        self._connected.remove(sock)

    def read(self, sock, data):
        try:
            cmd = json.loads(data)
            if "key" in cmd:
                self._key_cmd(cmd["key"])
            elif "allOff" in cmd:
                # Broadcast <Standby>
                self.fire(cec_write(CecMessage(16, 15, 0x36, [])), "cec")
            elif "makeSource" in cmd:
                self.fire(dev_make_source(cmd["makeSource"]["logical_address"]), "dev-mgr")
            elif "setting" in cmd:
                section = cmd["setting"].iterkeys().next()
                option = cmd["setting"][section].iterkeys().next()
                self.fire(config_value(section, option, 
                                       str(cmd["setting"][section][option])),
                                       "configuration")
        except:
            pass

    def _key_cmd(self, args):
        code = args["code"]
        self.fire(dev_send_key(code), "dev-mgr")

    @handler("dev_status", channel="dev-mgr")
    def _on_dev_status(self, event):
        device = event.device;
        data = json.dumps({ 
            "dev_status": {
                "logical_address": device.logical_address,
                "physical_address": device.physical_address,
                "osd_name": device.osd_name,
                "type": device.type,
                }
        })
        for sock in self._connected:
            self.fire(write(sock, data))

    @handler("dev_update_remote", channel="dev-mgr", priority=-1)
    def _on_dev_update_remote(self, event):
        self._active_remote = event.device.logical_address
        data = json.dumps({ 
            "reload": {}
        })
        for sock in self._connected:
            self.fire(write(sock, data))

    