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
from enigma import eHdmiCEC
from .ebrigde import blockingCallOnMainThread
from .monitor import cec_msg
import new
from .cec import CecMessage

class E2Adapter(Component):
    
    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(E2Adapter, self).__init__(*args, **kwargs)
        def setup():
            try:
                eHdmiCEC.getInstance().messageReceived.get().index(self.message_received)
                print "[CecCtrl] Message listener already registered."
            except:
                eHdmiCEC.getInstance().messageReceived.get().append(self.message_received)
                print "[CecCtrl] Handler for messageReceived registered."
                # Also monito sent messages, results in more consistent log
                sendFunc = getattr(eHdmiCEC, "sendMessage")
                if sendFunc:
                    def wrapped(obj, addr, cmd, data, length):
                        self.fire(
                            cec_msg(
                                CecMessage(obj.getLogicalAddress(), 
                                           addr, cmd, list(map(ord,data[0:length])))))
                        return sendFunc(obj, addr, cmd, data, length)
                    setattr(eHdmiCEC, "sendMessage", 
                            new.instancemethod(wrapped, None, eHdmiCEC))
                    print "[CecCtrl] Wrapper for sendMessage installed."
        blockingCallOnMainThread(setup)

    def message_received(self, message):
        # Called from main loop
        cmd = message.getCommand()
        buf = 16 * '\x00'
        length = message.getData(buf, len(buf))
        data = list(map(ord,buf[0:length-1]))
        self.fire(cec_msg(CecMessage(message.getAddress(), 
                                     eHdmiCEC.getInstance().getLogicalAddress(), cmd, data)))
        
