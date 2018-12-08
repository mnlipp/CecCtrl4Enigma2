import os
from CecCtrl import CecCtrlServer
from circuits.core.debugger import Debugger
from circuits.core.components import Component
from circuits_bricks.core.timers import Timer
from CecCtrl.cec import CecMessage
from CecCtrl.events import cec_write, cec_read
from circuits.core.handlers import handler

class DummyAdapter(Component):

    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(DummyAdapter, self).__init__(*args, **kwargs)

    @handler("cec_read", channel="cec")
    def _on_cec_read(self, event):
        print "Received: %s" % (event.msg)

    @handler("cec_write")
    def _on_cec_write(self, event):
        event.msg.srcAddr = 3
        msg = event.msg
        print "Sent: %s" % (msg)
        if msg.dstAddr == 5:
            if msg.cmd == 0x83:
                self.fire(cec_read(CecMessage(5, 3, 0x84, [0x40, 0, 5])))
            if msg.cmd == 0x46:
                self.fire(cec_read(CecMessage(5, 3, 0x47, list(map(ord,"A/V Receiver")))))

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
