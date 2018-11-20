import os
from CecCtrl import CecCtrlServer
from circuits.core.debugger import Debugger
from circuits.core.components import Component
from circuits_bricks.core.timers import Timer
from CecCtrl.monitor import cec_msg
from CecCtrl.cec import CecMessage

class DummyAdapter(Component):

    channel = "cec"
    
    def __init__(self, *args, **kwargs):
        super(DummyAdapter, self).__init__(*args, **kwargs)
        Timer(5, cec_msg(CecMessage(0, 0, 0x84, [0x40, 0, 5])), persist=True).register(self)

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
