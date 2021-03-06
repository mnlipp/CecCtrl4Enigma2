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
from circuits.io.events import write
import os
import logging
from posixpath import dirname
from circuits.core.components import Component
from circuits_bricks.app.logger import log
from .cec import cecCommands, CecMessage
from .cecadapter import cec_write
from datetime import datetime
from .cec import abortReason, powerStatus, deviceType, userControlCode

class MonitorPage(TemplateController):

    channel= "/monitor"

    def __init__(self, *args, **kwargs):
        super(MonitorPage, self).__init__(
            [os.path.join(dirname(__file__), "templates")], *args, **kwargs)
        WebSocketsDispatcher(channel="ctrl-ui",
                             path="/monitor/socket", 
                             wschannel="message-monitor").register(self)
        MessageMonitor().register(self)

    @handler("GET")
    def _on_get(self, event, request, response, peer_cert=None):
        if request.path.endswith("/socket"):
            # Let WebSocket dispatch handle this...
            return
        return self.serve_tenjin(request, response, "monitor.pyhtml", 
                                 {"cecCommands": cecCommands,
                                  "abortReason": abortReason,
                                  "powerStatus": powerStatus,
                                  "deviceType": deviceType,
                                  "userControlCode": userControlCode})
  
class MessageMonitor(Component):

    channel = "message-monitor"

    def __init__(self, *args, **kwargs):
        super(MessageMonitor, self).__init__(*args, **kwargs)
        self._connected = []

    def connect(self, sock, *args):
        self._connected.append(sock)

    def close(self, sock):
        self._connected.remove(sock)

    def read(self, sock, data):
        try:
            addrCmd = data.split("<")
            addr = int(addrCmd[0])
            opData = addrCmd[1].strip().split(":")
            opCode = int(opData[0], 0x10)
            data = map(lambda x: int(x, 0x10), opData[1:])
            self.fire(cec_write(CecMessage(16, addr, opCode, data)), "cec")
        except:
            pass

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        self._add_message(event.msg, event.timestamp)

    @handler("cec_write", channel="cec")
    def _on_cec_write(self, event):
        self._add_message(event.msg, datetime.now())

    def _add_message(self, msg, timestamp):
        if msg.cmd == 0 and len(msg.data) == 0:
            return
        entry = timestamp.strftime("%X.%f")[:-3] + ": " + str(msg)
        self.fire(log(logging.DEBUG, entry), "logger")
        socks = self._connected[:]
        for client in socks:
            try:
                self.fireEvent(write(client, entry))
            except:
                self._connected.remove(client)
