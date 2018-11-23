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
from .ebrigde import blockingCallOnMainThread, callOnMainThread
from .events import cec_read
import new
from .cec import CecMessage
from circuits.core.handlers import handler
import sys
import traceback
import ctypes

class eCECMessageStandIn:
    """
    Mimics the class eCecMessage, which isn't published to python for some
    unknown reason.
    """
    def __init__(self, address, command, data):
        self._address = address
        self._command = command
        self._data = data
        
    def getAddress(self):
        return self._address

    def getCommand(self):
        return self._command

    def getData(self, data, length):
        if length > len(self._data):
            length = len(self._data)
        ctypes.memmove(ctypes.c_char_p(data), self._data, length)


class E2Adapter(Component):
    """
    Integrates the CEC Control as a "virtual device". All messages received on the
    interface are reported as :class:`events.cec_read` events. All events generated
    by other enigma2 CEC modules are also reported as :class:`events.cec_read` events.
    
    Events of type :class:`events.cec_read` not targeted at enigma2's logical address
    (and broadcasts) are sent to the interface. Events targeted enigma2 (or brodcasts)
    are sent to other enigma2 CEC modules as if they were received on the interface.
    """
    
    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(E2Adapter, self).__init__(*args, **kwargs)
        self._ignore_next_sent = False
        def setup():
            try:
                eHdmiCEC.getInstance().messageReceived.get().index(self._on_message_received)
                print "[CecCtrl] Message listener already registered."
            except:
                # Make sure that our method is called before enigma2's default handler.
                # Else responses will have an earlier timestamp than the requests.
                eHdmiCEC.getInstance().messageReceived.get().insert(0, self._on_message_received)
                print "[CecCtrl] Handler for messageReceived registered."
                # Also monitor sent messages
                origSend = getattr(eHdmiCEC, "sendMessage")
                if origSend:
                    def wrapped(obj, addr, cmd, data, length):
                        if self._ignore_next_sent:
                            self._ignore_next_sent = False
                        else:
                            self.fire(
                                cec_read(
                                    CecMessage(obj.getLogicalAddress(), 
                                               addr, cmd, list(map(ord,data[0:length])))))
                        return origSend(obj, addr, cmd, data, length)
                    setattr(eHdmiCEC, "sendMessage", 
                            new.instancemethod(wrapped, None, eHdmiCEC))
                    print "[CecCtrl] Wrapper for sendMessage installed."
        blockingCallOnMainThread(setup)

    def _on_message_received(self, message):
        # Called from main loop
        cmd = message.getCommand()
        buf = 16 * '\x00'
        length = message.getData(buf, len(buf))
        data = list(map(ord,buf[0:length-1]))
        self.fire(cec_read(CecMessage(message.getAddress(), 
                                     eHdmiCEC.getInstance().getLogicalAddress(), cmd, data)))
        
    @handler("cec_write")
    def _on_cec_write(self, event):
        event.msg.srcAddr = eHdmiCEC.getInstance().getLogicalAddress()
        dataStr = "".join(map(chr, event.msg.data))
        # This "controller" acts as an independent device. Messages sent to
        # enigma (or broadcasts) must be "received"
        if event.msg.dstAddr == 15 \
            or event.msg.dstAddr != eHdmiCEC.getInstance().getLogicalAddress():
            def send():
                self._ignore_next_sent = True
                eHdmiCEC.getInstance().sendMessage(
                    event.msg.dstAddr, event.msg.cmd, dataStr, len(dataStr))
            callOnMainThread(send)
        if event.msg.dstAddr == 15 \
            or event.msg.dstAddr == eHdmiCEC.getInstance().getLogicalAddress():
            msg = eCECMessageStandIn(event.msg.dstAddr, event.msg.cmd, dataStr)
            def forward():
                print "Handlers:"
                print eHdmiCEC.getInstance().messageReceived.get()
                for hdlr in eHdmiCEC.getInstance().messageReceived.get():
                    if hdlr != self._on_message_received:
                        try:
                            hdlr(msg)
                        except:
                            print "Problem while forwarding message:", sys.exc_info()[0]
                            traceback.print_exc(file=sys.stdout)
            callOnMainThread(forward)
