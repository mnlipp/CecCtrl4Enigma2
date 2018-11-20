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
from circuits.core.events import Event
import cec
from .cec import CecMessage
from circuits_bricks.app.logger import log

class cec_msg(Event):
    
    def __init__(self, msg, *args, **kwargs):
        super(cec_msg, self).__init__(*args, **kwargs)
        self.msg = msg
    
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
        return self.serve_tenjin(request, response, "monitor.pyhtml", {})
  
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
        socks = self._connected[:]
        for client in socks:
            try:
                self.fireEvent(write(client, "Received: " + data))
            except:
                self._connected.remove(client)

    @handler("cec_msg", channel="cec")
    def _on_cec_msg(self, event):
        if event.msg.cmd == 0 and len(event.msg.data) == 0:
            return
        self.fire(log(logging.DEBUG, event.msg.to_string()), "logger")
