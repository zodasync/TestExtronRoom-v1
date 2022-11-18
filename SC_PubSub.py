## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.device import eBUSDevice, ProcessorDevice, UIDevice
from extronlib.interface import (ContactInterface, DigitalIOInterface,
    EthernetClientInterface, EthernetServerInterfaceEx, FlexIOInterface,
    IRInterface, RelayInterface, SerialInterface, SWPowerInterface,
    VolumeInterface)
from extronlib.ui import Button, Knob, Label, Level, Slider
from extronlib.system import Clock, MESet, Wait

class PubSubClass:
    def __init__(self):
        self.SubDict = {}
        self.SubDict['Events'] = {}
        self.SubDict['Listeners'] = []
    
    # This is for registering regular text events
    def RegisterEvent(self,events,function):
        eventlist = []
        if type(events) == str:
            eventlist.append(events.lower())
        elif type(events) == list:
            eventlist = [x.lower() for x in events]

        for eventname in eventlist:
            if not eventname in self.SubDict['Events']:
                self.SubDict['Events'][eventname] = []
            self.SubDict['Events'][eventname].append(function)

    # This is for registering regular text events
    def UnregisterEvent(self,events,function):
        eventlist = []
        if type(events) == str:
            eventlist.append(events.lower())
        elif type(events) == list:
            eventlist = [x.lower() for x in events]

        for eventname in eventlist:
            if eventname in self.SubDict['Events']:
                if function in self.SubDict['Events'][eventname]:
                    self.SubDict['Events'][eventname].remove(function)

    # Register a listener for all events that come through this PubSub
    def RegisterListener(self,function):
        if function not in self.SubDict['Listeners']:
            self.SubDict['Listeners'].append(function)

    # Unregister a listener for all events that come through this PubSub
    def UnregisterListener(self,function):
        if function in self.SubDict['Listeners']:
            self.SubDict['Listeners'].remove(function)

    # This triggers an event which calls any functions registered with that event with optional data
    def TriggerEvent(self,eventname,data=None):
        # Listeners are functions that listen for all events, such as the debugger console
        if len(self.SubDict['Listeners']):
            for function in self.SubDict['Listeners']:
                function(eventname,data)

        # Trigger all functions that have registered for this specific event
        if eventname.lower() in self.SubDict['Events']:
            for function in self.SubDict['Events'][eventname.lower()]:
                function(data)

