import os
from CecCtrl import CecCtrlServer
from circuits.core.debugger import Debugger
from circuits.core.components import Component
from circuits_bricks.core.timers import Timer
from CecCtrl.cec import CecMessage
from CecCtrl.cecadapter import cec_write, cec_read
from circuits.core.handlers import handler

class DummyAdapter(Component):

    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(DummyAdapter, self).__init__(*args, **kwargs)
        self._active_source = 3

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        print "Received: %s" % (event.msg)

    @handler("cec_write")
    def _on_cec_write(self, event):
        event.msg.srcAddr = 3
        msg = event.msg
        print "Sent: %s" % (msg)
        if msg.dstAddr == 0:
            if msg.cmd == 0x83:
                self.fire(cec_read(CecMessage(0, 15, 0x84, [0, 0, 1])))
            if msg.cmd == 0x46:
                self.fire(cec_read(CecMessage(0, 15, 0x47, list(map(ord,"TV")))))
        if msg.dstAddr == 3:
            if msg.cmd == 0x83:
                self.fire(cec_read(CecMessage(3, 15, 0x84, [0x20, 0, 3])))
            if msg.cmd == 0x46:
                self.fire(cec_read(CecMessage(3, 15, 0x47, list(map(ord,"vuultimo")))))
        if msg.dstAddr == 5:
            if msg.cmd == 0x83:
                self.fire(cec_read(CecMessage(5, 15, 0x84, [0x40, 0, 5])))
            if msg.cmd == 0x46:
                self.fire(cec_read(CecMessage(5, 15, 0x47, list(map(ord,"AV/Receiver")))))
        if msg.cmd == 0x85:
            if self._active_source == 3:
                self.fire(cec_read(CecMessage(3, 15, 0x82, []).append_physical([2,0,0,0])))
            if self._active_source == 5:
                self.fire(cec_read(CecMessage(5, 15, 0x82, []).append_physical([4,0,0,0])))
        if msg.cmd == 0x8c:
            if self._active_source == 3:
                self.fire(cec_read(CecMessage(3, 15, 0x87, [0, 0, 0])))
        if msg.cmd == 0x86:
            if msg.data == [0x20,0x0]:
                self.fire(cec_read(CecMessage(3, 15, 0x82, []).append_physical([2,0,0,0])))
            if msg.data == [0x40,0x0]:
                self.fire(cec_read(CecMessage(5, 15, 0x82, []).append_physical([4,0,0,0])))

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
