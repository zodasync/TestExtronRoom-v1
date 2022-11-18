## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.device import UIDevice
from extronlib.ui import Button, Knob, Label, Level, Slider

class SuperUIDevice(UIDevice):
    def __init__(self, DeviceAlias, PartNumber = None):
        super().__init__(DeviceAlias, PartNumber)
        self.__online = False
        self.SubDict = {}
        self.SubDict['Events'] = {}
        self.SubDict['Listeners'] = []

        @event(self, ['Online', 'Offline'])
        def HandleConnectionEvent(dev, status):
            if status == 'Online':
                self.__online = True
            elif status == 'Offline':
                self.__online = False

    @property
    def IsOnline(self):
        return self.__online

# Method to either return an existing button object or create a new one and return that
    def Button(self,buttonID,inHoldTime=None,inRepeatTime=None):
        if not buttonID in self.SubDict:
            self.SubDict[buttonID] = {}
        if not 'Button' in self.SubDict[buttonID]:
            self.SubDict[buttonID]['Button'] = Button(self,buttonID,holdTime=inHoldTime,repeatTime=inRepeatTime)
        if not 'Events' in self.SubDict[buttonID]:
            self.SubDict[buttonID]['Events'] = {}

        tmpButton = self.SubDict[buttonID]['Button']
        return tmpButton

# Method to either return an existing slider object or create a new one and return that
    def Slider(self,sliderID,min=None,max=None,step=None):
        if not sliderID in self.SubDict:
            self.SubDict[sliderID] = {}
        if not 'Slider' in self.SubDict[sliderID]:
            self.SubDict[sliderID]['Slider'] = Slider(self,sliderID)
        if not 'Events' in self.SubDict[sliderID]:
            self.SubDict[sliderID]['Events'] = {}

        tmpSlider = self.SubDict[sliderID]['Slider']
        if not min == None and not max == None:
            tmpSlider.SetRange(min,max,step)
        return tmpSlider

# Method to either return an existing level object or create a new one and return that
    def Level(self,levelID,min=None,max=None,step=1):
        if not levelID in self.SubDict:
            self.SubDict[levelID] = {}
        if not 'Level' in self.SubDict[levelID]:
            self.SubDict[levelID]['Level'] = Level(self,levelID)
        if not 'Events' in self.SubDict[levelID]:
            self.SubDict[levelID]['Events'] = {}

        tmpLevel = self.SubDict[levelID]['Level']
        if not min == None and not max == None:
            tmpLevel.SetRange(min,max,step)
        return tmpLevel

# Method to either return an existing label object or create a new one and return that
    def Label(self,labelID):
        if not labelID in self.SubDict:
            self.SubDict[labelID] = {}
        if not 'Label' in self.SubDict[labelID]:
            self.SubDict[labelID]['Label'] = Label(self,labelID)

        tmpLabel = self.SubDict[labelID]['Label']
        return tmpLabel

# Method to either return an existing knob object or create a new one and return that
    def Knob(self,knobID):
        # Navigate dictionary to endpoint, creating along the way if necessary
        if not knobID in self.SubDict:
            self.SubDict[knobID] = {}
        if not 'Knob' in self.SubDict[knobID]:
            self.SubDict[knobID]['Knob'] = Knob(knobID)
                
        # Create temporary knob to set up events
        tmpKnob = self.SubDict[knobID]['Knob']
        return tmpKnob

# Use this function to register a button on a UI to call a function in place of the @event model
    def RegisterButtonEvent(self,buttonID,events,function,momentary=False,holdTime=None,repeatTime=None):
        eventlist = []
        if type(events) == str:
            eventlist.append(events)
        elif type(events) == list:
            eventlist = events
        
        # Either get the existing button object or create a new one
        tmpButton = self.Button(buttonID,holdTime,repeatTime)
        self.SubDict[buttonID]['Momentary'] = momentary
        if momentary and 'Released' not in eventlist:
            eventlist.append('Released')

        for eventname in eventlist:
            if not eventname in ['Pressed','Held','Repeated','Released','Tapped']:
                print('RegisterButtonEvent: {} not a valid button event.'.format(eventname))
                return

            # Navigate dictionary to endpoint, creating along the way if necessary
            if not eventname in self.SubDict[buttonID]['Events']:
                self.SubDict[buttonID]['Events'][eventname] = []
            if not function in self.SubDict[buttonID]['Events'][eventname]:
                self.SubDict[buttonID]['Events'][eventname].append(function)

        # Set up our button event capture
        @event(tmpButton,eventlist)
        def tmpEvent(btn,ev):
            if self.SubDict[buttonID]['Momentary']:
                btn.SetState(ev in 'PressedHeldRepeated')
            if not ev == 'Released' or (ev == 'Released' and not self.SubDict[buttonID]['Momentary']):
                self.__buttonevent(btn,ev)

        return tmpButton

# Remove a single button function subscription
# Leaving function blank will delete all functions associated with event; leaving events blank will delete all events associated with button
    def UnRegisterButtonEvent(self,buttonID,events=None,function=None):
        eventlist = []
        if type(events) == str:
            eventlist.append(events)
        elif type(events) == list:
            eventlist = events
        
        if buttonID in self.SubDict:
            # Are we specifying an event?
            if events is not None:
                for eventname in eventlist:
                    if eventname in self.SubDict[buttonID]['Events']:
                        # Are we specifying a particular function?
                        if function is not None:
                            if function in self.SubDict[buttonID]['Events'][eventname]:
                                self.SubDict[buttonID]['Events'][eventname].remove(function)
                        # Delete all functions
                        else:
                            self.SubDict[buttonID]['Events'][eventname] = []
            # Delete all events
            else:
                self.SubDict[buttonID]['Events'] = {}

# Function that is called by a button push
    def __buttonevent(self,button,event):
        if button.ID in self.SubDict:
            if event in self.SubDict[button.ID]['Events']:
                if len(self.SubDict[button.ID]['Events'][event]):
                    for func in self.SubDict[button.ID]['Events'][event]:
                        func(button,event)

# Trigger events based on UI and button ID
    def SimulateButtonEvent(self,host,ID,event):
        if ID in self.SubDict:
            button = self.SubDict[ID]['Button']
            if event in self.SubDict[ID]['Events']:
                if len(self.SubDict[ID]['Events'][event]):
                    for func in self.SubDict[ID]['Events'][event]:
                        func(button,event)

# Register a function to a knob turning a specific direction
    def RegisterKnobEvent(self,knobID,direction,function):        # Direction should be CW or CCW
        if direction not in ['CW','CCW']:
            print('RegisterKnobEvent: {} is not a valid direction.'.format(direction))
            return
        
        tmpKnob = self.Knob(knobID)

        if not function in self.SubDict[knobID]:
            self.SubDict[knobID][direction] = []
        if not function in self.SubDict[knobID][direction]:
            self.SubDict[knobID][direction].append(function)
        
        @event(tmpKnob,'Turned')
        def tmpEvent(knb,num):
            if num > 0:
                self.__knobevent(knb,'CW',num)
            else:
                self.__knobevent(knb,'CCW',abs(num))
        
        return tmpKnob

# Remove a single knob function subscription
    def UnRegisterKnobEvent(self,knobID,eventname,function):
        if knobID in self.SubDict:
            if eventname in self.SubDict[knobID]:
                if function in self.SubDict[knobID][eventname]:
                    self.SubDict[knobID][eventname].remove(function)

# Function that is called by knob turn
    def __knobevent(self,knb,dir,num):
        if knb.ID in self.SubDict:
            if dir in self.SubDict[knb.ID]:
                if len(self.SubDict[knb.ID][dir]):
                    for func in self.SubDict[knb.ID][dir]:
                        for i in range(num):
                            func()

# Use this function to register a button on a UI to call a function in place of the @event model
    def RegisterSliderEvent(self,sliderID,events,function,min=None,max=None,step=None):
        eventlist = []
        if type(events) == str:
            eventlist.append(events)
        elif type(events) == list:
            eventlist = events
        
        # Either get the existing slider object or create a new one
        tmpSlider = self.Slider(sliderID,min,max,step)

        for eventname in eventlist:
            if not eventname in ['Pressed','Released','Changed']:
                print('RegisterSliderEvent: {} not a valid slider event.'.format(eventname))
                return

            # Navigate dictionary to endpoint, creating along the way if necessary
            if not eventname in self.SubDict[sliderID]['Events']:
                self.SubDict[sliderID]['Events'][eventname] = []
            if not function in self.SubDict[sliderID]['Events'][eventname]:
                self.SubDict[sliderID]['Events'][eventname].append(function)

        # Set up our slider event capture
        @event(tmpSlider,eventlist)
        def tmpEvent(obj,ev,num):
            self.__sliderevent(obj,ev,num)

        return tmpSlider

# Remove a single slider function subscription
# Leaving function blank will delete all functions associated with event; leaving events blank will delete all events associated with slider
    def UnRegisterSliderEvent(self,sliderID,events=None,function=None):
        eventlist = []
        if type(events) == str:
            eventlist.append(events)
        elif type(events) == list:
            eventlist = events
        
        if sliderID in self.SubDict:
            # Are we specifying an event?
            if events is not None:
                for eventname in eventlist:
                    if eventname in self.SubDict[sliderID]['Events']:
                        # Are we specifying a particular function?
                        if function is not None:
                            if function in self.SubDict[sliderID]['Events'][eventname]:
                                self.SubDict[sliderID]['Events'][eventname].remove(function)
                        # Delete all functions
                        else:
                            self.SubDict[sliderID]['Events'][eventname] = []
            # Delete all events
            else:
                self.SubDict[sliderID]['Events'] = {}

# Function that is called by a slider push
    def __sliderevent(self,slider,event,num):
        if slider.ID in self.SubDict:
            if event in self.SubDict[slider.ID]['Events']:
                if len(self.SubDict[slider.ID]['Events'][event]):
                    for func in self.SubDict[slider.ID]['Events'][event]:
                        func(slider,event,num)
