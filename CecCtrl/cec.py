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
                if fmt == "d":
                    if self.data[paramIndex] in deviceType:
                        result += " " + deviceType[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "p":
                    if len(self.data) - paramIndex < 2:
                        break
                    value = self.data[paramIndex] << 8 | self.data[paramIndex + 1]
                    result += " %d" % (value >> 12)
                    for i in range(3):
                        result += ":%d" % ((value >> (2 - i) * 4) & 0xf)
                    paramIndex += 2
                elif fmt == "P":
                    if self.data[paramIndex] in powerStatus:
                        result += " " + powerStatus[self.data[paramIndex]]
                    paramIndex += 1
                elif fmt == "s":
                    result += ' "' + "".join(list(map(chr,self.data[paramIndex:]))) + '"' 
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
    0x00: ("<Feature Abort>", "A"),
    0x04: ("<Image View On>", ""),
    0x05: ("<Tuner Step Increment>", ""),
    0x06: ("<Tuner Step Decrement>", ""),
    0x07: ("<Tuner Device Status>", ""),
    0x08: ("<Give Tuner Device Status>", ""),
    0x09: ("<Record On>", ""),
    0x0a: ("<Record Status>", ""),
    0x0b: ("<Record Off>", ""),
    0x0d: ("<Text View On>", ""),
    0x0f: ("<Record TV Screen>", ""),
    0x1a: ("<Give Deck Status>", ""),
    0x1b: ("<Deck Status>", ""),
    0x32: ("<Set Menu Language>", "s"),
    0x33: ("<Clear Analogue Timer>", ""),
    0x34: ("<Set Analogue Timer>", ""),
    0x35: ("<Timer Status>", ""),
    0x36: ("<Standby>", ""),
    0x41: ("<Play>", ""),
    0x42: ("<Deck Control>", ""),
    0x43: ("<Timer Cleared Status>", ""),
    0x44: ("<User Control Pressed>", ""),
    0x45: ("<User Control Released>", ""),
    0x46: ("<Give OSD Name>", ""),
    0x47: ("<Set OSD Name>", "s"),
    0x64: ("<Set OSD String>", "s"),
    0x67: ("<Set Timer Program Title>", ""),
    0x70: ("<System Mode Audio Request>", "p"),
    0x71: ("<Give Audio Status>", ""),
    0x72: ("<Set System Audio Mode>", ""),
    0x7a: ("<Report Audio Status>", ""),
    0x7d: ("<Give System Audio Mode Status>", ""),
    0x7e: ("<System Audio Mode Status>", ""),
    0x80: ("<Routing Change>", "pp"),
    0x81: ("<Routing Information>", "p"),
    0x82: ("<Active Source>", "p"),
    0x83: ("<Give Physical Address>", ""),
    0x84: ("<Report Physical Address>", "pd"),
    0x85: ("<Request Active Source>", ""),
    0x86: ("<Set Stream Path>", "p"),
    0x87: ("<Device Vendor ID>", ""),
    0x89: ("<Vendor Command>", ""), 
    0x8a: ("<Vendor Remote Button Down>", ""),
    0x8b: ("<Vendor Remote Button Up>", ""),
    0x8c: ("<Give Device Vendor ID>", ""),
    0x8d: ("<Menu Request>", ""),
    0x8e: ("<Menu Status>", ""),
    0x8f: ("<Give Device Power Status>", ""),
    0x90: ("<Report Power Status>", "P"),
    0x91: ("<Get Menu Language>", ""),
    0x92: ("<Select Analogue Service>", ""),
    0x93: ("<Select Digital Service>", ""),
    0x97: ("<Set Digital Timer>", ""),
    0x99: ("<Clear Digital Timer>", ""),
    0x9a: ("<Set Audio Rate>", ""),
    0x9e: ("<CEC Version>", ""),
    0x9d: ("<Inactive Source>", "p"),
    0x9e: ("<CEC Version>", "V"),
    0x9f: ("<Get CEC Version>", ""),
    0xa0: ("<Vendor Command With ID>", ""),
    0xa1: ("<Clear External Timer>", ""),
    0xa2: ("<Set External Timer>", ""),
    0xa3: ("<Report Short Audio Descriptor>", ""),
    0xa4: ("<Request Short Audio Descriptor>", ""),
    0xc0: ("<Initiate ARC>", ""),
    0xc1: ("<Report ARC Initiated>", ""),
    0xc2: ("<Report ARC Terminated>", ""),
    0xc3: ("<Request ARC Initiation>", ""),
    0xc4: ("<Request ARC Termination>", ""),
    0xc5: ("<Terminate ARC>", ""),
    0xf8: ("<CDC Message>", ""),
    0xff: ("<Abort>", ""),
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
# CEC Version's table:
cecVersion = ["1.1","1.2","1.2a","1.3","1.3a","1.4","2.0?","unknown"]
# opcode for broadcast only:
BROADCAST = [0x32, 0x72, 0x80, 0x81, 0x82, 0x84, 0x85, 0x86, 0x87, 0x8a, 0x8b, 0xA0]
# opcode for direct address or broadcast:
BOTH = [0x36, 0x72, 0x8a, 0x8b, 0xA0]
