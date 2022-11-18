## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.device import ProcessorDevice # UIDevice
#from extronlib.ui import Button, Knob, Label, Level, Slider
from extronlib.system import MESet, Timer, Wait

from SC_Console import ConsoleClass
from SC_PubSub import PubSubClass
from SC_UIDevice import SuperUIDevice as UIDevice

from ConnectionHandler import GetConnectionHandler
import system_config as sysConfig
import qsc_dsp_Q_Sys_Core_Series_v1_12_4_0 as qsc_dsp
import nec_display_P_V_X_Series_v1_4_1_0 as NecDisplay
import extr_matrix_DTPCrossPoint_86_1084KSeriesv11000 as extr_matrix_DTPCrossPoint
import sony_camera_SRG_300_Series_v1_8_0_0 as sony_camera

print(Version())

# ---------------------------------------------------------------------------------------------------------------------
# Program Notes
#
# ---------------------------------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------
# System Constants
# ---------------------------------------------------------------------------------------------------------------------
thisProc = ProcessorDevice('Proc1')

# Set up PubSub object - This object is included as a parameter for all other classes so they can use the Event system
PS = PubSubClass()
Console = ConsoleClass(PubSub = PS,Port=9824)

# Variable to disable devices trying to connect - THIS NEEDS TO BE SET TO FALSE IN THE FIELD
System_Debug_Only = True


# ---------------------------------------------------------------------------------------------------------------------
# Ethernet Devices
# ---------------------------------------------------------------------------------------------------------------------
Display_01 = GetConnectionHandler(NecDisplay.EthernetClass('10.10.112.81', 7142), 'Power')

Display_01.Connect()

def Display01_StatusHandler(command, value, qualifier):
    print('NATSEC Edge Planar status {}: {}'.format(command, value))

Display_01.SubscribeStatus('Power', None, Display01_StatusHandler)
Display_01.SubscribeStatus('Input', None, Display01_StatusHandler)

# Instantiating Switcher
Switcher1 = extr_matrix_DTPCrossPoint.SSHClass('192.168.254.250', 22023, Credentials=('admin', 'extron'),
                                               Model='DTP CrossPoint 108 4K')

Switcher1.Connect(timeout=5)


# ---------------------------------------------------------------------------------------------------------------------
# Secure Platform Devices
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# System Variables
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# System Functions
# ---------------------------------------------------------------------------------------------------------------------
def ScaleValue(value, min, max, scale):
    range = float(max) - min
    rel_value = float(value) - min
    return round(rel_value / range * scale)



# ---------------------------------------------------------------------------------------------------------------------
# Device Definitions
# ---------------------------------------------------------------------------------------------------------------------

#IPCP 350
Proc1 = ProcessorDevice('Proc1')

# ---------------------------------------------------------------------------------------------------------------------
# Touchpanels
# ---------------------------------------------------------------------------------------------------------------------
TP_01 = UIDevice('TP1')
TP_01.SetInactivityTime([240])

TouchpanelConfig = {
   TP_01:         sysConfig.config['tp01']
}

print('Touchpanels defined')

# ---------------------------------------------------------------------------------------------------------------------
# Switcher1 Setup - Main Switcher
# ---------------------------------------------------------------------------------------------------------------------
Switcher1_Source_Map = {
                1:   { 'Name':'Room PC',            'Input':1,        'Index':1,  'Display_Input':'HDMI1' },
                2:   { 'Name':'Wireless Collab',    'Input':2,        'Index':2,  'Display_Input':'HDMI1' },
                3:   { 'Name':'Laptop',             'Input':3,        'Index':3,  'Display_Input':'HDMI1' },
                4:   { 'Name':'Camera',             'Input':4,        'Index':4,  'Display_Input':'HDMI1' },

                25:  { 'Name':'Blank',              'Input':0,        'Index':5 },
    }

Switcher1_Dest_Map = {
                1:  { 'Name':'Display',             'Output':5,       'Index':1,  'Room':'', 'Type':'Audio/Video' },
    }

def Switch_AV(source, dest, type='Audio/Video'):
    if source == 0:
        inputNum = 0
    else:
        inputNum = Switcher1_Source_Map[source]['Input']

    outputNum = Switcher1_Dest_Map[dest]['Output']
    Switcher1.Set('MatrixTieCommand', 'String', { 'Input': inputNum, 'Output': outputNum, 'Tie Type': type })
    PS.TriggerEvent('switcher1.avroute', { 'source': source, 'dest': dest })

# ---------------------------------------------------------------------------------------------------------------------
# DSP Config
# ---------------------------------------------------------------------------------------------------------------------
Dsp_Config = sysConfig.config['dsp']
DSP_01 = GetConnectionHandler(qsc_dsp.EthernetClass(Dsp_Config['address'], 1702, Model='Q-Sys Core 110f'))
DSP_01.Connect()

DSP_PollingTimer = None

DSP_Level_Settings = {
    'WELCOME_LEV':      { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'THEATER_WPLEV':    { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'IGLOO_LEV':        { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'INFRA_LEV':        { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'CITZ_LEV':         { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'EDGE_LEV':         { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'CMD_LEV':          { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
    'CLOSING_LEV':      { 'min': -50, 'max': 0, 'startup': -20, 'currentLevel': 0, 'muteState': False },
}

Source_Selector_Tags = {
    'CMD_SS': { 1: 'Wall Plate', 2: 'Content' }
}

def PeriodicResubscribeCallback(timer, count):
    DSP_01.Update('LevelControl', {'Instance Tag': 'WELCOME_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'THEATER_WPLEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'IGLOO_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'INFRA_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'CITZ_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'EDGE_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'CMD_LEV', 'Channel': '1'})
    DSP_01.Update('LevelControl', {'Instance Tag': 'CLOSING_LEV', 'Channel': '1'})

    DSP_01.Update('MuteControl', {'Instance Tag': 'WELCOME_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'THEATER_WPLEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'IGLOO_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'INFRA_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'CITZ_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'EDGE_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'CMD_LEV', 'Channel': '1'})
    DSP_01.Update('MuteControl', {'Instance Tag': 'CLOSING_LEV', 'Channel': '1'})

    DSP_01.Update('SourceSelectorSourceSelection', {'Instance Tag': 'CMD_SS'})
    # print('Subscription sent')

@event(DSP_01, ['Connected', 'Disconnected'])
def DSP_EthernetStatus(interface, state):
    global DSP_PollingTimer
    if state == 'Connected':
        print('DSP Connected')
        if DSP_PollingTimer is None:
            PeriodicResubscribeCallback(None, None)
            DSP_PollingTimer = Timer(30, PeriodicResubscribeCallback)
        else:
            DSP_PollingTimer.Restart()
    else:
        if DSP_PollingTimer:
            DSP_PollingTimer.Stop()

def DSP_FeedbackHandler(command, value, qualifier):
    if command == 'MuteControl':
        instance = qualifier['Instance Tag']
        this_value = (value == 'On')
        instance_settings = DSP_Level_Settings[instance]
        instance_settings['muteState'] = this_value
    elif command == 'LevelControl':
        instance = qualifier['Instance Tag']
        this_value = value
        instance_settings = DSP_Level_Settings[instance]
        instance_settings['currentLevel'] = this_value

    PS.TriggerEvent('dsp.feedback.{}'.format(command), { 'command': command, 'value': value, 'qualifier': qualifier})


DSP_01.Connect()
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'WELCOME_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'THEATER_WPLEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'IGLOO_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'INFRA_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'CITZ_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'EDGE_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'CMD_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('MuteControl', { 'Instance Tag': 'CLOSING_LEV', 'Channel': '1' }, DSP_FeedbackHandler)

DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'WELCOME_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'THEATER_WPLEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'IGLOO_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'INFRA_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'CITZ_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'EDGE_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'CMD_LEV', 'Channel': '1' }, DSP_FeedbackHandler)
DSP_01.SubscribeStatus('LevelControl', { 'Instance Tag': 'CLOSING_LEV', 'Channel': '1' }, DSP_FeedbackHandler)

DSP_01.SubscribeStatus('SourceSelectorSourceSelection', {'Instance Tag': 'CMD_SS'}, DSP_FeedbackHandler)

# ---------------------------------------------------------------------------------------------------------------------
# Camera Config
# ---------------------------------------------------------------------------------------------------------------------
Camera_01 = sony_camera.SerialClass(Proc1, 'COM1', Model='SRG-300H')

CamPanSpeed = '10'
CamTiltSpeed = '10'
CamZoomSpeed = '4'

CameraPTZ_Btns = [ 5198, 5194, 5197, 5195, 5193, 5192 ]

def CameraPTZControl(btn, ev):
    global CamPanSpeed
    global CamTiltSpeed
    global CamZoomSpeed

    if ev == 'Released':
        Camera_01.Set('Pan', 'Stop', {'Speed': 1 } )
        Camera_01.Set('Tilt', 'Stop', {'Speed': 1 } )
        Camera_01.Set('Zoom', 'Stop', {'Speed': 1 } )

    elif btn.ID == 5198:
        Camera_01.Set('Tilt', 'Up', {'Speed': CamTiltSpeed })
    elif btn.ID == 5194:
        Camera_01.Set('Tilt', 'Down', {'Speed': CamTiltSpeed })
    elif btn.ID == 5197:
        Camera_01.Set('Pan', 'Left', {'Speed': CamPanSpeed })
    elif btn.ID == 5195:
        Camera_01.Set('Pan', 'Right', {'Speed': CamPanSpeed })
    elif btn.ID == 5193:
        Camera_01.Set('Zoom', 'In', { 'Speed': CamZoomSpeed })
    elif btn.ID == 5192:
        Camera_01.Set('Zoom', 'Out', { 'Speed': CamZoomSpeed })

for btn in CameraPTZ_Btns:
    TP_01.RegisterButton(btn, ['Pressed','Released'], CameraPTZControl)

CameraHome_Btn = 5196
CameraPreset_Btns = [ 5191, 5189, 5190 ]

def CameraPresetStopLED():
    TP_01.SetLEDState(65533, 'Off')

def CameraPresetControl(btn, ev):
    PresetNum = CameraPreset_Btns.index(btn.ID) + 1

    # Save a preset
    if ev == 'Held':
        Camera_01.Set('PresetSave', str(PresetNum))
        TP_01.SetLEDBlinking(65533, 'Fast', ['Off', 'Green'])
        Wait(2,CameraPresetStopLED)
    elif ev == 'Tapped':
        Camera_01.Set('PresetRecall', str(PresetNum))

for btn in CameraPreset_Btns:
    TP_01.RegisterButton(btn, ['Held','Tapped'], CameraPresetControl, holdTime=3)

def CameraSetHome(btn, ev):
    Camera_01.Set('Home', None)

TP_01.RegisterButton(CameraHome_Btn, 'Pressed', CameraSetHome)

# ---------------------------------------------------------------------------------------------------------------------
# SurgeX Code
# ---------------------------------------------------------------------------------------------------------------------
SurgeX_IP = '192.168.254.21'
SurgeX_Port = EthernetClientInterface(SurgeX_IP, 23)
SurgeX_Connected = False
SurgeX_LoggedIn = False
SurgeX_Username = 'admin'
SurgeX_Password = 'admin'

@event(SurgeX_Port,['Connected','Disconnected'])
def SurgeX_Connection(iface, state):
    global SurgeX_Connected
    global SurgeX_LoggedIn

    if state == 'Connected':
        PS.TriggerEvent('SurgeX_Events','Connected.')
        print('SurgeX Connected')
        SurgeX_Connected = True
    elif state == 'Disconnected':
        PS.TriggerEvent('SurgeX_Events','Disconnected.')
        print('SurgeX Disconnected')
        SurgeX_Connected = False
        SurgeX_LoggedIn = False
        Wait(5,SurgeX_Reconnect)

def SurgeX_Reconnect():
    result = SurgeX_Port.Connect()
    if result != 'Connected':
        PS.TriggerEvent('SurgeX_Events','Not connected. Retrying.')
        Wait(5,SurgeX_Reconnect)


@event(SurgeX_Port,'ReceiveData')
def SurgeX_Receive(iface, data):
    global SurgeX_LoggedIn

    if b'\xff\xfb' in data:
        SurgeX_Port.Send(bytes([0xff,0xfd,data[2]]))
    elif b'User>' in data:
        iface.Send('{}\r\n'.format(SurgeX_Username))
        PS.TriggerEvent('SurgeX_Events','Username sent')
        print('SurgeX Username')
    elif b'Password>' in data:
        iface.Send('{}\r\n'.format(SurgeX_Password))
        PS.TriggerEvent('SurgeX_Events','Password sent')
        print('SurgeX Password')
    elif b'Axess ELITE>' and not SurgeX_LoggedIn:
        PS.TriggerEvent('SurgeX_Events','Logged in')
        print('SurgeX Logged In')
        SurgeX_LoggedIn = True

def SurgeX_SetPort(port, state):
    global SurgeX_LoggedIn
    if type(port) == int and state.lower() in ['on','off','reboot']:
        SurgeX_Port.Send('set outlet {} {}\r\n'.format(port,state.lower()))
        PS.TriggerEvent('SurgeX_Events','set outlet {} {}\r\n'.format(port,state.lower()))


SurgeX_Reconnect()


# ---------------------------------------------------------------------------------------------------------------------
# Touchpanel Logic
# ---------------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------------
# Touchpanel Page Logic
# ---------------------------------------------------------------------------------------------------------------------
@event(TP_01,'Online')
def TP_01_Online(dev, ev):
    TP_01.HideAllPopups()
    TP_01.ShowPage('00 Entry Pincode')

@event(TP_01,'InactivityChanged')
def TP_01_Inactive(dev, time):
    TP_01.ShowPage('00 Entry Pincode')

TP_01_PageMap = {
    393:  { 'type': 'popup', 'name': 'SpeakerAudio' },
    395:  { 'type': 'popup', 'name': 'MicAudio' },
    396:  { 'type': 'popup', 'name': 'PC Health' },
    397:  { 'type': 'popup', 'name': 'Lighting Global' },
    398:  { 'type': 'popup', 'name': 'KVM Routing' },
    401:  { 'type': 'popup', 'name': 'AV Routing basePage' },
    402:  { 'type': 'page',  'name': '00 Entry Pincode' },
}

TP_01_PageMap_List = [ 393, 395, 396, 397, 398, 401, 402 ]

TP_01_Mic_PageMap = {
    78:  'MicAudio',
    80:  'MicRouting',
}

TP_01_PCStatus_PageMap = {
    177:  'PC Health',
    178:  'PC Reboot',
}

TP_01_Lighting_PageMap = {
    268:  'Lighting Global',
    269:  'Lighting Zn1 Welcome',
    270:  'Lighting Zn2 Theater',
    271:  'Lighting Zn3 Future',
    272:  'Lighting Zn4 Infrastructure',
    273:  'Lighting Zn5 Citizen',
    274:  'Lighting Zn6 NS Edge',
    275:  'Lighting Zn7 NS Command',
    276:  'Lighting Zn8 Closing',
}

TP_01_Routing_PageMap = {
    448:  'AV Routing Dests Reception',
    436:  'AV Routing Dests Citizen',
    437:  'AV Routing Dests NS Edge',
    449:  'AV Routing Dests CC Wall',
    450:  'AV Routing Dests CC Monitors',
}

TP_01_PageMap_Btns = MESet([])
TP_01_PageMap_Btns_List = []
TP_01_Mic_PageMap_Btns = MESet([])
TP_01_Mic_PageMap_Btns_List = []
TP_01_PCStatus_PageMap_Btns = MESet([])
TP_01_PCStatus_PageMap_Btns_List = []
TP_01_Lighting_PageMap_Btns = MESet([])
TP_01_Lighting_PageMap_Btns_List = []
TP_01_Routing_PageMap_Btns = MESet([])
TP_01_Routing_PageMap_Btns_List = []

def TP_01_Base_PageMap_Press(btn, ev):
    if (TP_01_PageMap[btn.ID]['type'] == 'page'):
        TP_01.ShowPage(TP_01_PageMap[btn.ID]['name'])
    elif (TP_01_PageMap[btn.ID]['type'] == 'popup'):
        TP_01.ShowPopup(TP_01_PageMap[btn.ID]['name'])
    TP_01_PageMap_Btns.SetCurrent(btn)

    index = TP_01_PageMap_List.index(btn.ID)
    if not index == 5:
        for id in TP_01_Routing_PageMap:
            TP_01.HidePopup(TP_01_Routing_PageMap[id])

    if index == 1:
        PS.SimulateButtonEvent(TP_01, 78, 'Pressed')
    elif index == 2:
        PS.SimulateButtonEvent(TP_01, 177, 'Pressed')
    elif index == 3:
        PS.SimulateButtonEvent(TP_01, 268, 'Pressed')
    elif index == 5:
        PS.SimulateButtonEvent(TP_01, 448, 'Pressed')

for btn_id in TP_01_PageMap:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_Base_PageMap_Press)
    TP_01_PageMap_Btns.Append(btn)
    TP_01_PageMap_Btns_List.append(btn)



def TP_01_Mic_PageMap_Press(btn, ev):
    TP_01.ShowPopup(TP_01_Mic_PageMap[btn.ID])
    TP_01_Mic_PageMap_Btns.SetCurrent(btn)

for btn_id in TP_01_Mic_PageMap:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_Mic_PageMap_Press)
    TP_01_Mic_PageMap_Btns.Append(btn)
    TP_01_Mic_PageMap_Btns_List.append(btn)



def TP_01_PCStatus_PageMap_Press(btn, ev):
    TP_01.ShowPopup(TP_01_PCStatus_PageMap[btn.ID])
    TP_01_PCStatus_PageMap_Btns.SetCurrent(btn)

for btn_id in TP_01_PCStatus_PageMap:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_PCStatus_PageMap_Press)
    TP_01_PCStatus_PageMap_Btns.Append(btn)
    TP_01_PCStatus_PageMap_Btns_List.append(btn)



def TP_01_Lighting_PageMap_Press(btn, ev):
    TP_01.ShowPopup(TP_01_Lighting_PageMap[btn.ID])
    TP_01_Lighting_PageMap_Btns.SetCurrent(btn)

for btn_id in TP_01_Lighting_PageMap:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_Lighting_PageMap_Press)
    TP_01_Lighting_PageMap_Btns.Append(btn)
    TP_01_Lighting_PageMap_Btns_List.append(btn)



def TP_01_Routing_PageMap_Press(btn, ev):
    TP_01.ShowPopup(TP_01_Routing_PageMap[btn.ID])
    TP_01_Routing_PageMap_Btns.SetCurrent(btn)

for btn_id in TP_01_Routing_PageMap:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_Routing_PageMap_Press)
    TP_01_Routing_PageMap_Btns.Append(btn)
    TP_01_Routing_PageMap_Btns_List.append(btn)

# ---------------------------------------------------------------------------------------------------------------------
# Rack Touchpanel Routing Logic
# ---------------------------------------------------------------------------------------------------------------------
TP_01_SelectedSource = None

TP_01_SourceBtn_Map = {
    301:   1,
    302:   2,
    303:   3,
    304:   4,
}

TP_01_Source_Btns = MESet([])
TP_01_Source_Btns_List = []

def TP_01_SourceMap_Press(btn, ev):
    global TP_01_SelectedSource
    TP_01_SelectedSource = TP_01_SourceBtn_Map[btn.ID]
    TP_01_Source_Btns.SetCurrent(btn)

for btn_id in TP_01_SourceBtn_Map:
    btn = TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_SourceMap_Press)
    TP_01_Source_Btns.Append(btn)
    TP_01_Source_Btns_List.append(btn)



TP_01_DestBtn_Map = {
    468:    { 'dest': 1, 'text': 469 },
}

def TP_01_DestMap_Press(btn, ev):
    global TP_01_SelectedSource
    destBtn = TP_01_DestBtn_Map[btn.ID]
    Switch_AV(TP_01_SelectedSource, destBtn['dest'])

for btn_id in TP_01_DestBtn_Map:
    TP_01.RegisterButtonEvent( btn_id, 'Pressed', TP_01_DestMap_Press)



# This is a callback for updating the rack touchpanel buttons when any routes are made
def TP_01_UpdateDestText(data):
    if data['source'] > 0:
        sourceName = Switcher1_Source_Map[data['source']]['Name']
    else:
        sourceName = 'None'
    dest = data['dest']

    for btn in TP_01_DestBtn_Map:
        if TP_01_DestBtn_Map[btn]['dest'] == dest:
            TP_01.Button(TP_01_DestBtn_Map[btn]['text']).SetText(sourceName)
            # print('Setting button {} to {}'.format(TP_01_DestBtn_Map[btn]['text'],sourceName))

PS.RegisterEvent('switcher1.avroute',TP_01_UpdateDestText)

# ---------------------------------------------------------------------------------------------------------------------
# Rack Touchpanel Volume Controls
# ---------------------------------------------------------------------------------------------------------------------
Rack_Volume_Control_Map = {
    'WELCOME_LEV':      { 'volUp': 101, 'volDown': 102, 'muteToggle': 103, 'gauge': 104, 'textFb': 105 },
    'THEATER_WPLEV':    { 'volUp': 106, 'volDown': 107, 'muteToggle': 108, 'gauge': 109, 'textFb': 110 },
    'IGLOO_LEV':        { 'volUp': 111, 'volDown': 112, 'muteToggle': 113, 'gauge': 114, 'textFb': 115 },
    'INFRA_LEV':        { 'volUp': 116, 'volDown': 117, 'muteToggle': 118, 'gauge': 119, 'textFb': 120 },
    'CITZ_LEV':         { 'volUp': 121, 'volDown': 122, 'muteToggle': 123, 'gauge': 124, 'textFb': 125 },
    'EDGE_LEV':         { 'volUp': 126, 'volDown': 127, 'muteToggle': 128, 'gauge': 129, 'textFb': 130 },
    'CMD_LEV':          { 'volUp': 131, 'volDown': 132, 'muteToggle': 133, 'gauge': 134, 'textFb': 135 },
    'CLOSING_LEV':      { 'volUp': 136, 'volDown': 137, 'muteToggle': 138, 'gauge': 139, 'textFb': 140 },
}

Rack_Volume_ID_Map = {}

def Rack_DSP_VolUp(btn, ev):
    instance = Rack_Volume_ID_Map[btn.ID]
    instance_settings = DSP_Level_Settings[instance]
    if instance_settings['currentLevel'] < instance_settings['max']:
        DSP_01.Set('LevelControl', instance_settings['currentLevel'] + 1, { 'Instance Tag': instance, 'Channel': '1' })
    else:
        DSP_01.Set('LevelControl', instance_settings['max'], { 'Instance Tag': instance, 'Channel': '1' })
    DSP_01.Update('LevelControl', {'Instance Tag': instance, 'Channel': '1'})


def Rack_DSP_VolDown(btn, ev):
    instance = Rack_Volume_ID_Map[btn.ID]
    instance_settings = DSP_Level_Settings[instance]
    if instance_settings['currentLevel'] > instance_settings['min']:
        DSP_01.Set('LevelControl', instance_settings['currentLevel'] - 1, { 'Instance Tag': instance, 'Channel': '1' })
    else:
        DSP_01.Set('LevelControl', instance_settings['min'], { 'Instance Tag': instance, 'Channel': '1' })
    DSP_01.Update('LevelControl', {'Instance Tag': instance, 'Channel': '1'})

def Rack_DSP_MuteToggle(btn, ev):
    instance = Rack_Volume_ID_Map[btn.ID]
    instance_settings = DSP_Level_Settings[instance]
    if instance_settings['muteState']:
        DSP_01.Set('MuteControl', 'Off', { 'Instance Tag': instance, 'Channel': '1' })
    else:
        DSP_01.Set('MuteControl', 'On', { 'Instance Tag': instance, 'Channel': '1' })
    DSP_01.Update('MuteControl', {'Instance Tag': instance, 'Channel': '1'})

for instance in Rack_Volume_Control_Map:
    Rack_Volume_ID_Map[Rack_Volume_Control_Map[instance]['volUp']] = instance
    Rack_Volume_ID_Map[Rack_Volume_Control_Map[instance]['volDown']] = instance
    Rack_Volume_ID_Map[Rack_Volume_Control_Map[instance]['muteToggle']] = instance

    TP_01.RegisterButtonEvent(Rack_Volume_Control_Map[instance]['volUp'], ['Pressed', 'Repeated'], Rack_DSP_VolUp, repeatTime=0.2)
    TP_01.RegisterButtonEvent(Rack_Volume_Control_Map[instance]['volDown'], ['Pressed', 'Repeated'], Rack_DSP_VolDown, repeatTime=0.2)
    TP_01.RegisterButtonEvent(Rack_Volume_Control_Map[instance]['muteToggle'], 'Pressed', Rack_DSP_MuteToggle)

def Rack_Handle_DSP_Mute_Feedback(data):
    instance = data['qualifier']['Instance Tag']
    this_value = (data['value'] == 'On')
    TP_01.Button(Rack_Volume_Control_Map[instance]['muteToggle']).SetState(this_value)

def Rack_Handle_DSP_Level_Feedback(data):
    instance = data['qualifier']['Instance Tag']
    this_value = data['value']
    instance_settings = DSP_Level_Settings[instance]
    scaledValue = ScaleValue(this_value, instance_settings['min'], instance_settings['max'], 100)
    TP_01.Level(Rack_Volume_Control_Map[instance]['gauge'], 0, 100).SetLevel(scaledValue)
    TP_01.Label(Rack_Volume_Control_Map[instance]['textFb']).SetText('{}%'.format(scaledValue))

PS.RegisterEvent('dsp.feedback.MuteControl', Rack_Handle_DSP_Mute_Feedback)
PS.RegisterEvent('dsp.feedback.LevelControl', Rack_Handle_DSP_Level_Feedback)

# ---------------------------------------------------------------------------------------------------------------------
# Console Commands
# ---------------------------------------------------------------------------------------------------------------------
def ResetPanelPages(client, cmd=None):
    TP_01.HideAllPopups()
    TP_01.ShowPage('Start')

def console_Nav_Route(client, cmd):
    if ' ' in cmd:
        try:
            source,dest,route = cmd.split(' ')
            Switch_AV(int(source), int(dest), route)
            client.Send('Routing input {} to output {}, type: {}'.format(source, dest, route))
        except ValueError:
            source,dest = cmd.split(' ')
            Switch_AV(int(source), int(dest), route)
            client.Send('Routing input {} to output {}, type: Audio/Video'.format(source, dest))
    else:
        client.Send('Error: Must have at least 2 values: source and destination.')


Console.RegisterCommand('tpreset',ResetPanelPages,'Resets Touchpanels to start pages','In case of a logic error, run this command to get back to start on the touchpanels.',access=1)

Console.RegisterCommand('navroute',console_Nav_Route,'Routes source to destination on the NAV','Routes source to destination on the NAV.\r\nnavroute <source> <destination>',access=1)


# ---------------------------------------------------------------------------------------------------------------------
# Startup Code
# ---------------------------------------------------------------------------------------------------------------------
def Initialize():
    print(Version())

Wait(10,Initialize)
