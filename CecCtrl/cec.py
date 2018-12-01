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
from datetime import datetime

class CecMessage:

    def __init__(self, srcAddr, dstAddr, cmd, data):
        self.srcAddr = srcAddr
        self.dstAddr = dstAddr
        self.cmd = cmd
        self.data = data
        
    def to_string(self):
        result = "%d->%d: %02X" % (self.srcAddr, self.dstAddr, self.cmd)
        displayLength = len(self.data)
        for i in range(len(self.data)-1, 0, -1):
            if self.data[i] != 0 or self.data[i-1] != 0:
                break;
            displayLength = i
        for i in range(displayLength):
            result += " %02X" % (self.data[i])
        if displayLength < len(self.data):
            result += " ..."
            
        # Pretty print
        if self.cmd in cecCommands:
            result += " " + cecCommands[self.cmd][0]
            paramIndex = 0;
            for fmt in tuple(cecCommands[self.cmd][1]):
                if paramIndex >= len(self.data):
                    # fail safe
                    break    
                if fmt == "A":
                    if self.data[paramIndex] in abortReason:
                        result += " " + abortReason[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "B":
                    paramIndex += 1
                elif fmt == "D":
                    if self.data[paramIndex] in deviceType:
                        result += " " + deviceType[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "P":
                    if self.data[paramIndex] in powerStatus:
                        result += " " + powerStatus[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "U":
                    if self.data[paramIndex] in userControlCode:
                        result += " " + userControlCode[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "b":
                    result += " " + "%02X" % (self.data[paramIndex])
                    paramIndex += 1
                elif fmt == "o":
                    paramIndex += 1
                elif fmt == "p":
                    if len(self.data) - paramIndex < 2:
                        break
                    value = self.data[paramIndex] << 8 | self.data[paramIndex + 1]
                    result += " %d" % (value >> 12)
                    for i in range(3):
                        result += ":%d" % ((value >> (2 - i) * 4) & 0xf)
                    paramIndex += 2
                elif fmt == "s":
                    try:
                        s = "".join(list(map(chr,self.data[paramIndex:])))
                        result += ' "' + s.encode("string-escape") + '"'
                    except:
                        pass 
                    paramIndex = len(self.data)
                elif fmt == "V":
                    if self.data[paramIndex] < len(cecVersion):
                        result += " " + " Version: %s" % cecVersion[self.data[paramIndex]]
                    paramIndex += 1;
        else:
            result += " <unknown>"
        return result
        

# Commands:
cecCommands = {
    0x00: ("<Feature Abort>", "bA"),
    0x04: ("<Image View On>", ""),
    0x05: ("<Tuner Step Increment>", ""),
    0x06: ("<Tuner Step Decrement>", ""),
    0x07: ("<Tuner Device Status>", "o"),
    0x08: ("<Give Tuner Device Status>", "o"),
    0x09: ("<Record On>", "o"),
    0x0a: ("<Record Status>", "o"),
    0x0b: ("<Record Off>", ""),
    0x0d: ("<Text View On>", ""),
    0x0f: ("<Record TV Screen>", ""),
    0x1a: ("<Give Deck Status>", "o"),
    0x1b: ("<Deck Status>", "o"),
    0x32: ("<Set Menu Language>", "sB"),
    0x33: ("<Clear Analogue Timer>", "o"),
    0x34: ("<Set Analogue Timer>", "o"),
    0x35: ("<Timer Status>", "o"),
    0x36: ("<Standby>", ""),
    0x41: ("<Play>", "o"),
    0x42: ("<Deck Control>", "o"),
    0x43: ("<Timer Cleared Status>", "o"),
    0x44: ("<User Control Pressed>", "U"),
    0x45: ("<User Control Released>", ""),
    0x46: ("<Give OSD Name>", ""),
    0x47: ("<Set OSD Name>", "s"),
    0x64: ("<Set OSD String>", "o"),
    0x67: ("<Set Timer Program Title>", "o"),
    0x70: ("<System Mode Audio Request>", "p"),
    0x71: ("<Give Audio Status>", ""),
    0x72: ("<Set System Audio Mode>", "o"),
    0x7a: ("<Report Audio Status>", "o"),
    0x7d: ("<Give System Audio Mode Status>", ""),
    0x7e: ("<System Audio Mode Status>", "o"),
    0x80: ("<Routing Change>", "ppB"),
    0x81: ("<Routing Information>", "pB"),
    0x82: ("<Active Source>", "pB"),
    0x83: ("<Give Physical Address>", ""),
    0x84: ("<Report Physical Address>", "pDB"),
    0x85: ("<Request Active Source>", "B"),
    0x86: ("<Set Stream Path>", "pB"),
    0x87: ("<Device Vendor ID>", "oB"),
    0x89: ("<Vendor Command>", "o"), 
    0x8a: ("<Vendor Remote Button Down>", "o"),
    0x8b: ("<Vendor Remote Button Up>", ""),
    0x8c: ("<Give Device Vendor ID>", ""),
    0x8d: ("<Menu Request>", "o"),
    0x8e: ("<Menu Status>", "o"),
    0x8f: ("<Give Device Power Status>", ""),
    0x90: ("<Report Power Status>", "P"),
    0x91: ("<Get Menu Language>", ""),
    0x92: ("<Select Analogue Service>", "o"),
    0x93: ("<Select Digital Service>", "o"),
    0x97: ("<Set Digital Timer>", "o"),
    0x99: ("<Clear Digital Timer>", "o"),
    0x9a: ("<Set Audio Rate>", "o"),
    0x9e: ("<CEC Version>", ""),
    0x9d: ("<Inactive Source>", "p"),
    0x9e: ("<CEC Version>", "V"),
    0x9f: ("<Get CEC Version>", ""),
    0xa0: ("<Vendor Command With ID>", "o"),
    0xa1: ("<Clear External Timer>", "o"),
    0xa2: ("<Set External Timer>", "o"),
    0xa3: ("<Report Short Audio Descriptor>", "o"),
    0xa4: ("<Request Short Audio Descriptor>", "o"),
    0xc0: ("<Initiate ARC>", ""),
    0xc1: ("<Report ARC Initiated>", ""),
    0xc2: ("<Report ARC Terminated>", ""),
    0xc3: ("<Request ARC Initiation>", ""),
    0xc4: ("<Request ARC Termination>", ""),
    0xc5: ("<Terminate ARC>", ""),
    0xf8: ("<CDC Message>", "B"),
    0xff: ("<Abort>", "o"),
    }
# returned abort codes:
abortReason = {
    0x00:"Unrecognized opcode",
    0x01:"Not in correct mode to respond",
    0x02:"Cannot provide source",
    0x03:"Invalid operand",
    0x04:"Refused",
    0x05:"Unable to determine",
    }
# power status return codes:
powerStatus = {
    0x00:"(On)",
    0x01:"(Standby)",
    0x02:"(In transition Standby to On)",
    0x03:"(In transition On to Standby)",
    }
# Device types
deviceType = {
    0: "TV",
    1: "Recording Device",
    2: "Reserved",
    3: "Tuner",
    4: "Playback Device",
    5: "Audio System",
    6: "Pure CEC Switch",
    7: "Video Processor",
    }
# User control codes
userControlCode = {
    0x00: "Select",
    0x01: "Up",
    0x02: "Down",
    0x03: "Left",
    0x04: "Right",
    0x05: "Right-Up",
    0x06: "Right-Down",
    0x07: "Left-Up",
    0x08: "Left-Down",
    0x09: "Root Menu",
    0x0A: "Setup Menu",
    0x0B: "Contents Menu",
    0x0C: "Favorite Menu",
    0x0D: "Exit",
    0x0E: "Reserved",
    0x0F: "Reserved",
    0x10: "Media Top Menu",
    0x11: "Media Context-sensitive Menu",
    0x12: "Reserved",
    0x13: "Reserved",
    0x14: "Reserved",
    0x15: "Reserved",
    0x16: "Reserved",
    0x17: "Reserved",
    0x18: "Reserved",
    0x19: "Reserved",
    0x1A: "Reserved",
    0x1B: "Reserved",
    0x1C: "Reserved",
    0x1D: "Number Entry Mode",
    0x1E: "Number 11",
    0x1F: "Number 12",
    0x20: "Number 0 or Number 10",
    0x21: "Number 1",
    0x22: "Number 2",
    0x23: "Number 3",
    0x24: "Number 4",
    0x25: "Number 5",
    0x26: "Number 6",
    0x27: "Number 7",
    0x28: "Number 8",
    0x29: "Number 9",
    0x2A: "Dot",
    0x2B: "Enter",
    0x2C: "Clear",
    0x2D: "Reserved",
    0x2E: "Reserved",
    0x2F: "Next Favorite",
    0x30: "Channel Up",
    0x31: "Channel Down",
    0x32: "Previous Channel",
    0x33: "Sound Select",
    0x34: "Input Select",
    0x35: "Display Information",
    0x36: "Help",
    0x37: "Page Up",
    0x38: "Page Down",
    0x39: "Reserved",
    0x3A: "Reserved",
    0x3B: "Reserved",
    0x3C: "Reserved",
    0x3D: "Reserved",
    0x3E: "Reserved",
    0x3F: "Reserved",
    0x40: "Power",
    0x41: "Volume Up",
    0x42: "Volume Down",
    0x43: "Mute",
    0x44: "Play",
    0x45: "Stop",
    0x46: "Pause",
    0x47: "Record",
    0x48: "Rewind",
    0x49: "Fast forward",
    0x4A: "Eject",
    0x4B: "Forward",
    0x4C: "Backward",
    0x4D: "Stop-Record",
    0x4E: "Pause-Record",
    0x4F: "Reserved",
    0x50: "Angle",
    0x51: "Sub picture",
    0x52: "Video on Demand",
    0x53: "Electronic Program Guide",
    0x54: "Timer Programming",
    0x55: "Initial Configuration",
    0x56: "Select Broadcast Type",
    0x57: "Select Sound Presentation",
    0x58: "Reserved",
    0x59: "Reserved",
    0x5A: "Reserved",
    0x5B: "Reserved",
    0x5C: "Reserved",
    0x5D: "Reserved",
    0x5E: "Reserved",
    0x5F: "Reserved",
    0x60: "Play Function",
    0x61: "Pause-Play Function",
    0x62: "Record Function",
    0x63: "Pause-Record Function",
    0x64: "Stop Function",
    0x65: "Mute Function",
    0x66: "Restore Volume Function",
    0x67: "Tune Function",
    0x68: "Select Media Function",
    0x69: "Select A/V Input Function",
    0x6A: "Select Audio Input Function",
    0x6B: "Power Toggle Function",
    0x6C: "Power Off Function",
    0x6D: "Power On Function",
    0x6E: "Reserved",
    0x6F: "Reserved",
    0x70: "Reserved",
    0x71: "F1 (Blue)",
    0x72: "F2 (Red)",
    0x73: "F3 (Green)",
    0x74: "F4 (Yellow)",
    0x75: "F5",
    0x76: "Data",
}
# CEC Version's table:
cecVersion = ["1.1","1.2","1.2a","1.3","1.3a","1.4","2.0?","unknown"]
# opcode for broadcast only:
BROADCAST = [0x32, 0x72, 0x80, 0x81, 0x82, 0x84, 0x85, 0x86, 0x87, 0x8a, 0x8b, 0xA0]
# opcode for direct address or broadcast:
BOTH = [0x36, 0x72, 0x8a, 0x8b, 0xA0]
