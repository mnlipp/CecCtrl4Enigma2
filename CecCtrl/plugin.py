from Plugins.Plugin import PluginDescriptor
from .server import CecCtrlServer
from .e2adapter import E2Adapter

def plugin_start(reason, **kwargs):
	print "[CecCtrl] reason = " + str(reason)
	session = kwargs.get('session', None)
	print "[CecCtrl] session = " + str(session)	
	
	CONFIG = {
		"logging": {
	   	    "type": "TimedRotatingFile",
	        "file": "/var/log/cecctrl.log",
	        "when": "midnight",
	        "backupCount": 7,
	        "level": "DEBUG",
	        },
	    "ui": {
	        "port": "8123",
	        },
	}

	server = CecCtrlServer(CONFIG, { "config_dir": "/etc/enigma2/cecctrl",
								"app_dir": "/var/lib/cecctrl" })
	E2Adapter().register(server)
	server.start()

def Plugins(**kwargs):
	return PluginDescriptor(
            name="CecCtrl",
            where=PluginDescriptor.WHERE_SESSIONSTART, 
            fnc=plugin_start)
