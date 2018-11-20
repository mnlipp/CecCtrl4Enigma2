from Screens.Screen import Screen
from Components.ConfigList import ConfigListScreen
from Components.config import config, ConfigSubsection, ConfigSelection, ConfigYesNo, ConfigSelectionNumber, getConfigListEntry
from Components.ActionMap import ActionMap
from Components.Label import Label
from enigma import eTimer, getDesktop
from enigma import eHdmiCEC
import struct
import os

HD = False
if getDesktop(0).size().width() >= 1280:
	HD = True

class CecCtrl(Screen, ConfigListScreen):
    skin = """
    <screen position="center,center" size="640,400" title="CEC Control" >
    <widget name="myLabel" position="10,60" size="200,40"
    font="Regular;20"/>
    </screen>
    """

    def __init__(self, session):
        self._session = session
	Screen.__init__(self, session)
        self["myLabel"] = Label("Hello World ;-)")
	self["actions"] = ActionMap(["SetupActions"],
        {
	    "cancel": self.close
        }, -1)

