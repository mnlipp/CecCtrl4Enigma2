import os
from CecCtrl import CecCtrlServer
from circuits.core.debugger import Debugger
from circuits.core.components import Component
from circuits_bricks.core.timers import Timer
from CecCtrl.cec import CecMessage
from CecCtrl.cecadapter import cec_write, cec_read
from circuits.core.handlers import handler

class TestDevice(object):
    
    def __init__(self, adapter, logical_addr, physical_addr, type, name, vendor_id):
        super(TestDevice, self).__init__()
        self._adapter = adapter
        self._logical_addr = logical_addr
        self._physical_addr = physical_addr
        self._type = type
        self._name = name
        self._vendor_id = vendor_id
        self._on = False
    
    def on_cec_write(self, event):
        msg = event.msg
        if msg.dstAddr == self._logical_addr:
            if msg.cmd == 0x83: # Give Physical Address
                response = CecMessage(self._logical_addr, 15, 0x84, [])
                response.append_physical(self._physical_addr)
                response.data.append(self._type)
                self._adapter.fire(cec_read(response))
            if msg.cmd == 0x46: # Give OSD Name
                self._adapter.fire(cec_read(CecMessage(self._logical_addr, 15, 0x47, 
                                              list(map(ord,self._name)))))
            if msg.cmd == 0x8c: # Give Device Vendor ID
                if self._vendor_id:
                    self._adapter.fire(cec_read(CecMessage(self._logical_addr, 15, 0x87, 
                                                           self._vendor_id)))
            if msg.cmd == 0x8f: # Give device power status
                    self._adapter.fire(cec_read(CecMessage(self._logical_addr, 15, 0x90, 
                                                           [0 if self._on else 1])))
        if msg.cmd == 0x86: # Set Stream Path
            if msg.data == self._physical_addr:
                self._adapter.fire(cec_read(CecMessage(self._logical_addr, 15, 0x82, [])
                                            .append_physical(self._physical_addr)))

class TestTv(TestDevice):
    
    def __init__(self, adapter, logical_addr, physical_addr, type, name, vendor_id):
        super(TestTv, self).__init__(adapter, logical_addr, physical_addr, type, name, vendor_id)

    def on_cec_write(self, event):
        super(TestTv, self).on_cec_write(event)
        msg = event.msg
        if msg.dstAddr == self._logical_addr:
            if msg.cmd == 0x04:
                self._on = True

class DummyAdapter(Component):

    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(DummyAdapter, self).__init__(*args, **kwargs)
        self._active_source = 3
        self._devices = {
            0: TestTv(self, 0, [0, 0, 0, 0], 1, "TV", None),
            3: TestDevice(self, 3, [2, 0, 0, 0], 3, "vuultimo", None),
            4: TestDevice(self, 4, [4, 2, 0, 0], 4, "BD Player", None),
            5: TestDevice(self, 5, [4, 0, 0, 0], 5, "A/V Receiver", None),
            }

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        print "Received: %s" % (event.msg)

    @handler("cec_write")
    def _on_cec_write(self, event):
        event.msg.srcAddr = 3
        msg = event.msg
        print "Sent: %s" % (msg)
        for _, v in self._devices.items():
            v.on_cec_write(event)

        if msg.cmd == 0x85:# Request Active Source
            if self._active_source in self._devices:
                device = self._devices[self._active_source]
                self.fire(cec_read(CecMessage(device._logical_addr, 15, 0x82, [])
                                   .append_physical(device._physical_addr)))
        if msg.cmd == 0x86: # Set Stream Path
            for _, v in self._devices.items():
                if v._physical_addr == msg.data:
                    self._on = True
                    self.fire(cec_read(CecMessage(v.logical_address, 15, 0x82, [])
                                       .append_physical(v._physical_addr)))
                    break;

if __name__ == '__main__':

    CONFIG = {
        "logging": {
            "type": "TimedRotatingFile",
            "file": os.path.join("%(log_dir)s", "application.log"),
            "when": "midnight",
            "backupCount": 7,
            "level": "DEBUG",
        },
        "ui": {
            "port": "8123",
        },
    }
    
    server = CecCtrlServer(CONFIG, {})
    Debugger().register(server)
    DummyAdapter().register(server)
    server.run()
