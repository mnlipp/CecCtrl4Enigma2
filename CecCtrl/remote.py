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
from .events import cec_write, dev_report
from datetime import datetime
from circuits.io.events import write

class RemotePage(TemplateController):

    channel= "/remote"

    def __init__(self, *args, **kwargs):
        super(RemotePage, self).__init__(
            [os.path.join(dirname(__file__), "templates")], *args, **kwargs)
        WebSocketsDispatcher(channel="ctrl-ui",
                             path="/remote/socket", 
                             wschannel="remote-control").register(self)
        RemoteControl().register(self)

    @handler("GET")
    def _on_get(self, event, request, response, peer_cert=None):
        if request.path.endswith("/socket"):
            # Let WebSocket dispatch handle this...
            return
        return self.serve_tenjin(request, response, "base-remote.pyhtml", {})
  
class RemoteControl(Component):

    channel = "remote-control"

    def __init__(self, *args, **kwargs):
        super(RemoteControl, self).__init__(*args, **kwargs)
        self._connected = []

    def connect(self, sock, *args):
        self._connected.append(sock)
        self.fire(dev_report(), "dev-mgr")

    def close(self, sock):
        self._connected.remove(sock)

    def read(self, sock, data):
        try:
            cmd = json.loads(data)
            if "key" in cmd:
                self._key_cmd(cmd["key"])
            if "allOff" in cmd:
                # Broadcast <Standby>
                self.fire(cec_write(CecMessage(16, 15, 0x36, [])), "cec")
        except:
            pass

    def _key_cmd(self, args):
        code = args["code"]
        self.fire(cec_write(CecMessage(16, 3, 0x44, [code])), "cec")
        self.fire(cec_write(CecMessage(16, 3, 0x45, [])), "cec")

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
