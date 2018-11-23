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
from circuits.core.components import Component
import sys
from circuits.web import Server, Controller
import os
from circuits_bricks.app import Application
from posixpath import dirname
from circuits.web.dispatchers.static import Static
from .monitor import MonitorPage
from .remote import RemotePage

class Root(Controller):

    def index(self):
        return "Hello World!"
  
class ErrorHandler(Component):
    def exception(self, error_type, value, traceback, \
                  handler=None, fevent=None):
        sys.exit();

class CecCtrlServer(Application):

    def __init__(self, config, defaults, *args, **kwargs):
        super(CecCtrlServer, self).__init__("CecCtrlTest", config, defaults)
        ErrorHandler().register(self)
        # Build a web (HTTP) server for handling user interface requests.
        port = int(self.config.get("ui", "port", 0))
        server = Server(("0.0.0.0", port), channel="ctrl-ui") \
            .register(self)
        Static("/static", docroot=os.path.join(dirname(__file__), "static"),
               channel="ctrl-ui").register(server)
        Root().register(server)
        MonitorPage().register(server)
        RemotePage().register(server)
        
        from circuits.tools import graph
        print graph(self)
