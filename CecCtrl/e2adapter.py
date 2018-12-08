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
from enigma import eHdmiCEC, eActionMap
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
        self._last_cec_key = None
        self._key_map = {
            0x00: 352, # "Select" -> "KEY_OK"
            0x01: 103, # "Up" -> "KEY_UP"
            0x02: 108, # "Down" -> "KEY_DOWN"
            0x03: 105, # "Left" -> "KEY_LEFT"
            0x04: 106, # "Right" -> "KEY_RIGH"
            0x05: -1, # "Right-Up",
            0x06: -1, # "Right-Down",
            0x07: -1, # "Left-Up",
            0x08: -1, # "Left-Down",
            0x09: 139, # "Root Menu" -> "KEY_MENU"
            0x0A: -1, # "Setup Menu",
            0x0B: 366, # "Contents Menu" -> "KEY_PVR"
            0x0C: 364, # "Favorite Menu" -> "KEY_FAVORITES"
            0x0D: 174, # "Exit" -> "KEY_EXIT"
            0x0E: -1, # "Reserved",
            0x0F: -1, # "Reserved",
            0x10: 226, # "Media Top Menu" -> "KEY_MEDIA"
            0x11: 438, # "Media Context-sensitive Menu" -> "KEY_CONTEXT_MENU"
            0x1D: -1, # "Number Entry Mode",
            0x1E: -1, # "Number 11",
            0x1F: -1, # "Number 12",
            0x20: 11, # "Number 0 or Number 10" -> "KEY_0"
            0x21: 2, # "Number 1" -> "KEY_1"
            0x22: 3, # "Number 2" -> "KEY_2"
            0x23: 4, # "Number 3" -> "KEY_3"
            0x24: 5, # "Number 4" -> "KEY_4"
            0x25: 6, # "Number 5" -> "KEY_5"
            0x26: 7, # "Number 6" -> "KEY_6"
            0x27: 8, # "Number 7" -> "KEY_7"
            0x28: 9, # "Number 8" -> "KEY_8"
            0x29: 10, # "Number 9" -> "KEY_9"
            0x2A: -1, # "Dot",
            0x2B: -1, # "Enter",
            0x2C: -1, # "Clear",
            0x2D: -1, # "Reserved",
            0x2E: -1, # "Reserved",
            0x2F: -1, # "Next Favorite",
            0x30: 402, # "Channel Up" -> "KEY_CHANNELUP"
            0x31: 403, # "Channel Down" -> "KEY_CHANNELDOWN"
            0x32: 139, # "Previous Channel" -> "KEY_MENU" TODO
            0x33: -1, # "Sound Select",
            0x34: -1, # "Input Select",
            0x35: -1, # "Display Information",
            0x36: 138, # "Help" -> "KEY_HELP"
            0x37: -1, # "Page Up",
            0x38: -1, # "Page Down",
            0x40: -1, # "Power",
            0x41: 115, # "Volume Up" -> "KEY_VOLUMEUP"
            0x42: 114, # "Volume Down" -> "KEY_VOLUMEDOWN"
            0x43: 113, # "Mute" -> "KEY_MUTE"
            0x44: 207, # "Play" -> "KEY_PLAY"
            0x45: 128, # "Stop" -> "KEY_STOP"
            0x46: 119, # "Pause" -> "KEY_PAUSE"
            0x47: 167, # "Record" -> "KEY_RECORD"
            0x48: 168, # "Rewind" -> "KEY_REWIND"
            0x49: 208, # "Fast forward" -> "KEY_FASTFORWARD"
            0x4A: -1, # "Eject",
            0x4B: -1, # "Forward",
            0x4C: -1, # "Backward",
            0x4D: -1, # "Stop-Record",
            0x4E: -1, # "Pause-Record",
            0x4F: -1, # "Reserved",
            0x50: -1, # "Angle",
            0x51: -1, # "Sub picture",
            0x52: -1, # "Video on Demand",
            0x53: 358, # "Electronic Program Guide" -> "KEY_INFO"
            0x54: 362, # "Timer Programming" -> "KEY_PROGRAM"
            0x55: -1, # "Initial Configuration",
            0x56: -1, # "Select Broadcast Type",
            0x57: -1, # "Select Sound Presentation",
            0x60: 207, # "Play Function" -> "KEY_PLAY"
            0x61: 164, # "Pause-Play Function" -> "KEY_PLAYPAUSE"
            0x62: 167, # "Record Function" -> "KEY_RECORD"
            0x63: -1, # "Pause-Record Function",
            0x64: 128, # "Stop Function" -> "KEY_STOP"
            0x65: -1, # "Mute Function",
            0x66: -1, # "Restore Volume Function",
            0x67: -1, # "Tune Function",
            0x68: -1, # "Select Media Function",
            0x69: -1, # "Select A/V Input Function",
            0x6A: -1, # "Select Audio Input Function",
            0x6B: -1, # "Power Toggle Function",
            0x6C: -1, # "Power Off Function",
            0x6D: -1, # "Power On Function",
            0x6E: -1, # "Reserved",
            0x6F: -1, # "Reserved",
            0x70: -1, # "Reserved",
            0x71: 401, # "F1 (Blue)" -> "KEY_BLUE"
            0x72: 398, # "F2 (Red)" -> "KEY_RED"
            0x73: 399, # "F3 (Green)" -> "KEY_GREEN"
            0x74: 400, # "F4 (Yellow)" -> "KEY_YELLOW"
            0x75: -1, # "F5",
            0x76: -1, # "Data",
        }
        def setup():
            self.eam = eActionMap.getInstance()            
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
        # This "controller" acts as an independent device. Messages sent to
        # enigma (or broadcasts) must be "received"
        if event.msg.dstAddr == 15 \
            or event.msg.dstAddr != eHdmiCEC.getInstance().getLogicalAddress():
            dataStr = "".join(map(chr, event.msg.data))
            def send():
                self._ignore_next_sent = True
                eHdmiCEC.getInstance().sendMessage(
                    event.msg.dstAddr, event.msg.cmd, dataStr, len(dataStr))
            callOnMainThread(send)
        if event.msg.dstAddr == 15 \
            or event.msg.dstAddr == eHdmiCEC.getInstance().getLogicalAddress():
            def forward():
                self._forward(event.msg)
            callOnMainThread(forward)

    def _forward(self, msg):
        # Key presses are not handled by the registered messageReceived handlers.
        # Rather, they have special handling in cpp-Code. We have to duplicate this here.
        if msg.cmd == 0x44 or msg.cmd == 0x45:
            self._forward_key(msg);
        
        # Now forward to "normal" handlers
        dataStr = "".join(map(chr, msg.data))
        handlerMsg = eCECMessageStandIn(msg.dstAddr, msg.cmd, dataStr)
        for hdlr in eHdmiCEC.getInstance().messageReceived.get():
            if hdlr != self._on_message_received:
                try:
                    hdlr(handlerMsg)
                except:
                    print "Problem while forwarding message:", sys.exc_info()[0]
                    traceback.print_exc(file=sys.stdout)

    def _forward_key(self, msg):
            # Flags
        FLAG_MAKE = 0
        FLAG_BREAK = 1
        FLAG_REPEAT = 2
        FLAG_LONG = 3
        FLAG_ASCII = 4
    
        #Device Types
        TYPE_STANDARD = "dreambox remote control (native)"
        TYPE_ADVANCED = "dreambox advanced remote control (native)"
        TYPE_KEYBOARD = "dreambox ir keyboard"

        if msg.cmd == 0x44:
            cecKey = msg.data[0];
            self._last_cec_key = cecKey
        else:
            cecKey = self._last_cec_key
            self._last_cec_key = None
        if cecKey is None:
            return
        enigmaKey = 0x8b
        if not cecKey in self._key_map or self._key_map[cecKey] < 0:
            print "[CecCtrl] No mapping for CEC key 0x%02x" % cecKey
        else:
            enigmaKey = self._key_map[cecKey];
        if msg.cmd == 0x44:
            # Press key
            self.eam.keyPressed(TYPE_ADVANCED, self._key_map[cecKey], FLAG_MAKE)
        if msg.cmd == 0x45:
            # Release the key
            self.eam.keyPressed(TYPE_ADVANCED, self._key_map[cecKey], FLAG_BREAK)        

