from extronlib.interface import SerialInterface, EthernetClientInterface
from extronlib.system import Wait, ProgramLog
import re
import copy


class DeviceClass:
    def __init__(self):

        self.Unidirectional = 'False'
        self.connectionCounter = 15
        self.DefaultResponseTimeout = 0.3
        self.Subscription = {}
        self.ReceiveData = self.__ReceiveData
        self.__receiveBuffer = b''
        self.__maxBufferSize = 2048
        self.__matchStringDict = {}
        self.counter = 0
        self.connectionFlag = True
        self.initializationChk = True
        self.Debug = False
        self._NumberofCallHistoryResults = 5
        self._NumberofPhonebookResults = 5
        self.deviceUsername = None
        self.devicePassword = None
        self.Models = {}

        self.Commands = {
            'ConnectionStatus': {'Status': {}},
            'CallerID': {'Parameters': ['Control ID'], 'Status': {}},
            'CallerName': {'Parameters': ['Control ID'], 'Status': {}},
            'CallStatus': {'Parameters': ['Control ID'], 'Status': {}},
            'CallHistoryNavigation': {'Parameters': ['Control ID'], 'Status': {}},
            'CallHistoryResults': {'Parameters': ['Control ID', 'Position'], 'Status': {}},
            'CallHistoryUpdate': {'Parameters': ['Control ID'], 'Status': {}},
            'Router': {'Parameters': ['Control ID'], 'Status': {}},
            'ControlSetValue': {'Parameters': ['Control ID', 'Control Value'], 'Status': {}},
            'Function': {'Parameters': ['Control ID'], 'Status': {}},
            'FocusControl': {'Parameters': ['Control ID'], 'Status': {}},
            'FocusMode': {'Parameters': ['Control ID'], 'Status': {}},
            'FocusSpeed': {'Parameters': ['Control ID'], 'Status': {}},
            'Gain': {'Parameters': ['Control ID'], 'Status': {}},
            'GetStatusString': {'Parameters': ['Control ID'], 'Status': {}},
            'GetStatusValue': {'Parameters': ['Control ID'], 'Status': {}},
            'LevelMeter': {'Parameters': ['Control ID'], 'Status': {}},
            'Mute': {'Parameters': ['Control ID'], 'Status': {}},
            'PhonebookControl': {'Parameters': ['Control ID', 'Phonebook ID'], 'Status': {}},
            'PhonebookListUpdate': {'Parameters': ['Control ID'], 'Status': {}},
            'PhonebookNavigation': {'Parameters': ['Control ID'], 'Status': {}},
            'PhonebookResults': {'Parameters': ['Control ID', 'Position'], 'Status': {}},
            'PhonebookResultSet': {'Parameters': ['Control ID', 'Position'], 'Status': {}},
            'PhonebookSearch': {'Parameters': ['Control ID'], 'Status': {}},
            'PhonebookUpdate': {'Parameters': ['Control ID'], 'Status': {}},
            'PTZControl': {'Parameters': ['Control ID'], 'Status': {}},
            'PTZSpeed': {'Parameters': ['Control ID'], 'Status': {}},
            'SnapshotLoad': {'Parameters': ['Load Time', 'Bank'], 'Status': {}},
            'SnapshotSave': {'Parameters': ['Bank'], 'Status': {}},
            'DesignName': { 'Status': {}},
        }

        self.dialString = {}
        self.CallHistory = {}
        self.Phonebook = {}
            
        if self.Unidirectional == 'False':
            self.AddMatchString(re.compile(b'sr \"([\w\s]{1,63})\" \"\w{1,63}\" [0-1] [0-1]\r\n'), self.__MatchDesignName, None)
            self.AddMatchString(re.compile(b'bad_(.*)\r\n'), self.__MatchError, None)
            if 'Serial' not in self.ConnectionType:
                self.AddMatchString(re.compile(b'login NAME PIN'), self.__MatchCredential, None)  # from legacy driver
                self.AddMatchString(re.compile(b'login_required'), self.__MatchCredential, None)  # based off manufacture emulator software

        self.CallHistorySearch = re.compile('Text.{1,2}?\"\:.{1,2}?\"([\w|\(|\)| ]+).{1,2}?\"') # Response based on Q-Sys_110f.png
        self.PhonebookSearch = re.compile('\d+ \d+\s?([\"\w ]+)\s?\d+ \d+')

    @property
    def NumberofCallHistoryResults(self):
        return self._NumberofCallHistoryResults

    @NumberofCallHistoryResults.setter
    def NumberofCallHistoryResults(self, value):
        self._NumberofCallHistoryResults = int(value)

    @property
    def NumberofPhonebookResults(self):
        return self._NumberofPhonebookResults

    @NumberofPhonebookResults.setter
    def NumberofPhonebookResults(self, value):
        self._NumberofPhonebookResults = int(value)

    def __MatchCredential(self, match, tag):
        self.SetPassword(None, None)

    def SetPassword(self, value, qualifier):
        if self.devicePassword is not None:
            self.Send('{0}\r\n'.format(self.devicePassword))
        else:
            self.MissingCredentialsLog('Password')

    def UpdateCallerID(self, value, qualifier):
        
        self.UpdateCallStatus(value, {'Control ID': qualifier['Control ID']})

    def UpdateCallerName(self, value, qualifier):
        
        self.UpdateCallStatus(value, {'Control ID': qualifier['Control ID']})

    def UpdateCallStatus(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID: 
            CallStatusCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['CallStatus']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(?:((.*) - (.*) \((.*)\))|(.*))\" .*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchCallStatus, None)
            self.__UpdateHelper('CallStatus', CallStatusCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateCallStatus')

    def __MatchCallStatus(self, match, tag):

        qualifier = {'Control ID': match.group(1).decode()}
        if match.group(6):
            callstatus = match.group(6).decode()
            self.WriteStatus('CallStatus', callstatus, qualifier)
            self.WriteStatus('CallerID', 'N/A', qualifier)
            self.WriteStatus('CallerName', 'N/A', qualifier)
        else:
            callID = match.group(5).decode()
            self.WriteStatus('CallerID', callID, qualifier)
            callname = match.group(4).decode()
            self.WriteStatus('CallerName', callname, qualifier)
            callstatus = match.group(3).decode()
            self.WriteStatus('CallStatus', callstatus, qualifier)

    def SetCallHistoryNavigation(self, value, qualifier):
        self.Debug = True

        ctrlID = qualifier['Control ID']       
        if ctrlID and ctrlID in self.CallHistory:
            call_history = self.CallHistory[ctrlID]
            if value == 'Up':
                call_history.scroll_up(1)
            elif value == 'Down':
                call_history.scroll_down(1)
            elif value == 'Page Up':
                call_history.scroll_up(self._NumberofCallHistoryResults)
            elif value == 'Page Down':
                call_history.scroll_down(self._NumberofCallHistoryResults)
        else:
            self.Discard('Invalid Command for SetCallHistoryNavigation')

    def SetCallHistoryResultSet(self, value, qualifier):
        self.Debug = True

        dialStringID, ctrlID, position = qualifier['Dial String ID'], qualifier['Control ID'], qualifier['Position']
        if dialStringID and ctrlID and ctrlID in self.CallHistory and 1 <= int(position) <= 10:
            result = self.ReadStatus('CallHistoryResults', {'Control ID': ctrlID, 'Position': position})
            if result and result not in ['*** End of List ***', '*** Not Available ***']:
                self.Set('ControlSetString', value, {'Control ID': dialStringID, 'Control String': result})
            else:
                self.Error(['Invalid Call History Result'])
        else:
            self.Discard('Invalid Command for SetCallHistoryResultSet')

    def SetCallHistoryUpdate(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.CallHistory:
                self.CallHistory[ctrlID] = Directory(self._NumberofCallHistoryResults, ctrlID,  filler='')
                self.CallHistory[ctrlID].write_status_function = self.WriteCallHistoryResults
                
            res = self.SendAndWait('cgm \"{0}\"\n'.format(ctrlID), 1, deliTag='\n')
            if res:
                res = res.decode()
                call_history_data = self.CallHistorySearch.findall(res)
                call_history_data.append('*** End of List ***')
                self.CallHistory[ctrlID].reset(call_history_data)
            else:
                self.CallHistory[ctrlID].reset(['*** Not Available ***'])
        else:
            self.Discard('Invalid Command for SetCallHistoryUpdate')
            
    def WriteCallHistoryResults(self,value,qualifier):
        self.WriteStatus('CallHistoryResults', value, qualifier)

    def SetControlSetString(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        ctrlStr = qualifier['Control String']

        if ctrlID and ctrlStr:
            ControlSetStringCmdString = 'css \"{0}\" \"{1}\"\n'.format(ctrlID, ctrlStr)
            self.__SetHelper('ControlSetString', ControlSetStringCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command')


    def SetRouter(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        state = {
            'Enable'  : '1', 
            'Disable' : '0'
        }[value]

        if ctrlID:
            RouterCmdString = 'csv \"{0}\" {1}\n'.format(qualifier['Control ID'], state)
            self.__SetHelper('Router', RouterCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetRouter')

    def UpdateRouter(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            RouterCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['GetStatusValue']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \".*\" (0|1).*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchRouter, None)
            self.__UpdateHelper('Router', RouterCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateRouter')

    def __MatchRouter(self, match, tag):

        ValueStateValues = {
            '1' : 'Enable', 
            '0' : 'Disable'
        }

        qualifier = {'Control ID':match.group(1).decode()}
        value = ValueStateValues[match.group(2).decode()]
        self.WriteStatus('Router', value, qualifier)

    def SetControlSetValue(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        ctrlStr = qualifier['Control Value']

        if ctrlID and 0 <= ctrlStr <= 100:
            ControlSetValueCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, ctrlStr)
            self.__SetHelper('ControlSetValue', ControlSetValueCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetControlSetValue')

    def EmulatedDialStringHandler(self, value, control_id):

        if control_id not in self.dialString:
            self.dialString[control_id] = ''

        if value == 'Clear':
            self.dialString[control_id] = ''
        elif value == 'Delete':
            if self.dialString[control_id]:
                self.dialString[control_id] = self.dialString[control_id][:-1]
        else:
            self.dialString[control_id] = self.dialString[control_id]+value

    def SetFocusControl(self, value, qualifier):

        ctrlID = qualifier['Control ID']    
        state = {
            'Enable'  : '1', 
            'Disable' : '0'
        }[value]

        if ctrlID:
            FocusControlCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, state)
            self.__SetHelper('FocusControl', FocusControlCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetFocusControl')

    def UpdateFocusMode(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Commands['FocusMode']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(true|false)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchFocusMode, None)
            FocusModeCmdString = 'get \"{0}\"\n'.format(ctrlID)
            self.__UpdateHelper('FocusMode', FocusModeCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateFocusMode')

    def __MatchFocusMode(self, match, tag):

        value = {
            'true'  : 'Auto', 
            'false' : 'Manual'
        }[match.group(2).decode()]
        
        self.WriteStatus('FocusMode', value, {'Control ID' : match.group(1).decode()})

    def SetFocusSpeed(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if 0.001 <= value <= 0.100 and ctrlID:
            FocusSpeedCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, value)
            self.__SetHelper('FocusSpeed', FocusSpeedCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetFocusSpeed')

    def UpdateFocusSpeed(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Commands['FocusSpeed']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(\d?\.\d+)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchFocusSpeed, None)        
            FocusSpeedCmdString = 'get \"{0}\"\n'.format(ctrlID)
            self.__UpdateHelper('FocusSpeed', FocusSpeedCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateFocusSpeed')

    def __MatchFocusSpeed(self, match, tag):

        qualifier = {}
        qualifier['Control ID'] = match.group(1).decode()
        value = float(match.group(2).decode())       
        self.WriteStatus('FocusSpeed', value, qualifier)

    def SetGain(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if -100 <= value <= 83 and ctrlID:
            if ctrlID not in self.Commands['Gain']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(.*)dB\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchGain, None)
            GainCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, value)
            self.__SetHelper('Gain', GainCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetGain')

    def UpdateGain(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Commands['Gain']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(.*)dB\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchGain, None)
            GainCmdString = 'get \"{0}\"\n'.format(ctrlID)
            self.__UpdateHelper('Gain', GainCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateGain')

    def __MatchGain(self, match, tag):

        qualifier = {'Control ID':match.group(1).decode()}
        value = round(float(match.group(2)), 1)
        self.WriteStatus('Gain', value, qualifier)

    def UpdateGetStatusString(self, value, qualifier):
        ctrlID = qualifier['Control ID']
        if ctrlID:
            GetStatusCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['GetStatusString']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(.*)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchGetStatusString, None)
            self.__UpdateHelper('GetStatusString', GetStatusCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command')
            
    def __MatchGetStatusString(self, match, tag):

        control_id = match.group(1).decode()
        self.dialString[control_id] = match.group(2).decode()
        self.WriteStatus('GetStatusString', self.dialString[control_id], {'Control ID': control_id})

    def UpdateGetStatusValue(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            GetStatusCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['GetStatusValue']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" ([01]).*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchGetStatusValue, None)
                self.AddMatchString(re.compile('cv \"({0})\" \".*\" (0|1).*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchGetStatusValue, None)
            self.__UpdateHelper('GetStatusValue', GetStatusCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateGetStatusValue')

    def __MatchGetStatusValue(self, match, tag):

        ValueStateValues = {
            '1' : 'On', 
            '0' : 'Off'
        }

        qualifier = {'Control ID':match.group(1).decode()}
        value = ValueStateValues[match.group(2).decode()]
        self.WriteStatus('GetStatusValue', value, qualifier)

    def UpdateLevelMeter(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Commands['LevelMeter']['Status']:
                self.AddMatchString(re.compile('cvv \"({0})\" 2 \"([-.0-9]+)dB\" \"([-.0-9]+)dB\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchLevelMeter, None)
            LevelMeterCmdString = 'get \"{0}\"\n'.format(ctrlID)
            self.__UpdateHelper('LevelMeter', LevelMeterCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateLevelMeter')

    def __MatchLevelMeter(self, match, tag):

        qualifier = {'Control ID':match.group(1).decode()}
        value = round(float(match.group(2)), 1)
        self.WriteStatus('LevelMeter', value, qualifier)

    def SetMute(self, value, qualifier):

        ValueStateValues = {
            'On' : '1', 
            'Off' : '0',
        }
        ctrlID = qualifier['Control ID']

        if ctrlID:
            MuteCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, ValueStateValues[value])
            if ctrlID not in self.Commands['Mute']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(muted|unmuted)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchMute, None)
            self.__SetHelper('Mute', MuteCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetMute')

    def UpdateMute(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            MuteCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['Mute']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(muted|unmuted)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchMute, None)
            self.__UpdateHelper('Mute', MuteCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateMute')

    def __MatchMute(self, match, tag):

        state = {b'muted':'On', b'unmuted':'Off'}
        qualifier = {}
        qualifier['Control ID'] = match.group(1).decode()
        value = state[match.group(2)]
        self.WriteStatus('Mute', value, qualifier)

    def SetFunction(self, value, qualifier):

        ValueStateValues = {
            'Enable'  : '1', 
            'Disable' : '0'
        }
        ctrlID = qualifier['Control ID']
        if ctrlID:
            FunctionCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, ValueStateValues[value])
            if ctrlID not in self.Commands['Function']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(enabled|disabled)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchFunction, None)
            self.__SetHelper('Function', FunctionCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetFunction')

    def UpdateFunction(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            FunctionCmdString = 'get \"{0}\"\n'.format(ctrlID)
            if ctrlID not in self.Commands['Function']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(enabled|disabled)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchFunction, None)
            self.__UpdateHelper('Function', FunctionCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdateFunction')

    def __MatchFunction(self, match, tag):

        state = {b'enabled': 'Enable', b'disabled': 'Disable'}
        qualifier = {}
        qualifier['Control ID'] = match.group(1).decode()
        value = state[match.group(2)]
        self.WriteStatus('Function', value, qualifier)

    def SetPhonebookControl(self, value, qualifier):

        ctrlID, phonebook = qualifier['Control ID'], qualifier['Phonebook ID']
        if ctrlID and phonebook:
            self.UpdateGetStatusString(None , {'Control ID': phonebook})
            tempString = self.ReadStatus('GetStatusString', {'Control ID': phonebook})
            self.__SetHelper('PhonebookControl', 'css \"{0}\" \"{1}\"\n'.format(ctrlID, tempString), value, qualifier)
        else:
            self.Discard('Invalid Command for SetPhonebookControl')

    def SetPhonebookListUpdate(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Phonebook:
                self.Phonebook[ctrlID] = Directory(self._NumberofPhonebookResults, ctrlID, filler='')
                self.Phonebook[ctrlID].write_status_function = self.WritePhonebookResults

            res = self.SendAndWait('cgm \"{0}\"\n'.format(ctrlID), 1, deliTag='\n')
            if res:
                res = res.decode()
                phonebook_data = self.CallHistorySearch.findall(res)
                phonebook_data.append('*** End of List ***')
                self.Phonebook[ctrlID].reset(phonebook_data)
            else:
                self.Phonebook[ctrlID].reset(['*** Not Available ***'])
        else:
            self.Discard('Invalid Command for SetPhonebookListUpdate')
            
    def WritePhonebookResults(self,value,qualifier):
        self.WriteStatus('PhonebookResults', value, qualifier)

    def SetPhonebookNavigation(self, value, qualifier):
        self.Debug = True

        ctrlID = qualifier['Control ID']
        if ctrlID and ctrlID in self.Phonebook:
            phonebook = self.Phonebook[ctrlID]
            if value == 'Up':
                phonebook.scroll_up(1)
            elif value == 'Down':
                phonebook.scroll_down(1)
            elif value == 'Page Up':
                phonebook.scroll_up(self._NumberofPhonebookResults)
            elif value == 'Page Down':
                phonebook.scroll_down(self._NumberofPhonebookResults)
        else:
            self.Discard('Invalid Command for SetPhonebookNavigation')

    def SetPhonebookResultSet(self, value, qualifier):
        self.Debug = True

        ctrlID, position = qualifier['Control ID'], int(qualifier['Position'])
        if ctrlID and ctrlID in self.Phonebook and 1 <= position <= 10:
            result = self.ReadStatus('PhonebookResults', qualifier)
            if result and result not in ['*** End of List ***', '*** Not Available ***']:
                
                self.__SetHelper('PhonebookResultSet', 'css \"{0}\" \"{1}\"\n'.format(ctrlID, result), value, qualifier)
            else:
                self.Error(['Invalid Phonebook Result'])
        else:
            self.Discard('Invalid Command for SetPhonebookResultSet')

    def SetPhonebookSearch(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        searchString = qualifier['Contact']
        if ctrlID:
            self.__SetHelper('PhonebookSearch', 'css \"{0}\" \"{1}\"\n'.format(ctrlID, searchString), value, qualifier)
        else:
            self.Discard('Invalid Command for SetPhonebookSearch')

    def SetPhonebookUpdate(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Phonebook:
                self.Phonebook[ctrlID] = Directory(self._NumberofPhonebookResults, ctrlID, filler='')
                self.Phonebook[ctrlID].write_status_function = self.WritePhonebookResults

            res = self.SendAndWait('cgm \"{0}\"\n'.format(ctrlID), 1, deliTag='\n')
            if res:
                res = res.decode()
                phonebook_data = re.search(self.PhonebookSearch, res).group(1).replace('"','').split()
                if phonebook_data:
                    phonebook_data.append('*** End of List ***')
                    self.Phonebook[ctrlID].reset(phonebook_data)
                else:
                    self.Phonebook[ctrlID].reset(['*** Not Available ***'])
            else:
                self.Phonebook[ctrlID].reset(['*** Not Available ***'])
        else:
            self.Discard('Invalid Command for SetPhonebookUpdate')

    def SetPTZControl(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        
        state = {
            'Enable'  : '1', 
            'Disable' : '0'
        }[value]

        if ctrlID:
            PTZControlCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, state)
            self.__SetHelper('PTZControl', PTZControlCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetPTZControl')

    def SetPTZSpeed(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if 0.01 <= value <= 1 and ctrlID:
            PTZSpeedCmdString = 'csv \"{0}\" {1}\n'.format(ctrlID, value)
            self.__SetHelper('PTZSpeed', PTZSpeedCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetPTZSpeed')

    def UpdatePTZSpeed(self, value, qualifier):

        ctrlID = qualifier['Control ID']
        if ctrlID:
            if ctrlID not in self.Commands['PTZSpeed']['Status']:
                self.AddMatchString(re.compile('cv \"({0})\" \"(\d?\.\d+)\".*\n'.format(ctrlID.replace('.', '\.')).encode()), self.__MatchPTZSpeed, None)     
            PTZSpeedCmdString = 'get \"{0}\"\n'.format(ctrlID)
            self.__UpdateHelper('PTZSpeed', PTZSpeedCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for UpdatePTZSpeed')

    def __MatchPTZSpeed(self, match, tag):

        qualifier = {}
        qualifier['Control ID'] = match.group(1).decode()
        value = float(match.group(2).decode())       
        self.WriteStatus('PTZSpeed', value, qualifier)

    def SetSnapshotLoad(self, value, qualifier):

        LoadTimeConstraints = {
            'Min' : 0,
            'Max' : 60
            }
        if LoadTimeConstraints['Min'] <= qualifier['Load Time'] <= LoadTimeConstraints['Max'] and len(qualifier['Bank']) > 0 and 1 <= int(value) <= 24:
            SnapshotLoadCmdString = 'ssl \"{0}\" {1} {2}\n'.format(qualifier['Bank'], value, qualifier['Load Time'])
            self.__SetHelper('SnapshotLoad', SnapshotLoadCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetSnapshotLoad')

    def SetSnapshotSave(self, value, qualifier):

        SnapshotSaveCmdString = 'sss \"{0}\" {1}\n'.format(qualifier['Bank'], value)
        if len(qualifier['Bank']) > 0 and 1 <= int(value) <= 24:
            self.__SetHelper('SnapshotSave', SnapshotSaveCmdString, value, qualifier)
        else:
            self.Discard('Invalid Command for SetSnapshotSave')

    def UpdateDesignName(self, value, qualifier):

        self.__UpdateHelper('DesignName', 'sg\n', value, qualifier)

    def __MatchDesignName(self, match, tag):

        value = match.group(1).decode()
        self.WriteStatus('DesignName', value, None)

    def __SetHelper(self, command, commandstring, value, qualifier):
        self.Debug = True
        self.Send(commandstring)

    def __UpdateHelper(self, command, commandstring, value, qualifier, queryDisallowTime=0.3):

        if self.Unidirectional == 'True':
            self.Discard('Inappropriate Command ' + command)
        else:
            self.Send(commandstring)

            if self.initializationChk:
                self.OnConnected()
                self.initializationChk = False

            self.counter = self.counter + 1
            if self.counter > self.connectionCounter and self.connectionFlag:
                self.OnDisconnected()

    def __MatchError(self, match, tag):
        self.counter = 0
        self.Error(['Error'])

    def OnConnected(self):
        self.connectionFlag = True
        self.WriteStatus('ConnectionStatus', 'Connected')
        self.counter = 0
        if 'Serial' not in self.ConnectionType:
            self.SetPassword(None, None)

    def OnDisconnected(self):
        self.WriteStatus('ConnectionStatus', 'Disconnected')
        self.connectionFlag = False

        self.dialString = {}
        self.CallHistory = {}
        self.Phonebook = {}

    ######################################################
    # RECOMMENDED not to modify the code below this point
    ######################################################

    # Send Control Commands
    def Set(self, command, value, qualifier=None):
        method = getattr(self, 'Set%s' % command, None)
        if method is not None and callable(method):
            method(value, qualifier)
        else:
            raise AttributeError(command + 'does not support Set.')

    # Send Update Commands
    def Update(self, command, qualifier=None):
        method = getattr(self, 'Update%s' % command, None)
        if method is not None and callable(method):
            method(None, qualifier)
        else:
            raise AttributeError(command + 'does not support Update.')

    # This method is to tie an specific command with a parameter to a call back method
    # when its value is updated. It sets how often the command will be query, if the command
    # have the update method.
    # If the command doesn't have the update feature then that command is only used for feedback 
    def SubscribeStatus(self, command, qualifier, callback):
        Command = self.Commands.get(command, None)
        if Command:
            if command not in self.Subscription:
                self.Subscription[command] = {'method':{}}
        
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
        
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
                        if Parameter in qualifier:
                            Method[qualifier[Parameter]] = {}
                            Method = Method[qualifier[Parameter]]
                        else:
                            return
        
            Method['callback'] = callback
            Method['qualifier'] = qualifier    
        else:
            raise KeyError('Invalid command for SubscribeStatus ' + command)

    # This method is to check the command with new status have a callback method then trigger the callback
    def NewStatus(self, command, value, qualifier):
        if command in self.Subscription :
            Subscribe = self.Subscription[command]
            Method = Subscribe['method']
            Command = self.Commands[command]
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Method = Method[qualifier[Parameter]]
                    except:
                        break
            if 'callback' in Method and Method['callback']:
                Method['callback'](command, value, qualifier)  

    # Save new status to the command
    def WriteStatus(self, command, value, qualifier=None):
        self.counter = 0
        if not self.connectionFlag:
            self.OnConnected()
        Command = self.Commands[command]
        Status = Command['Status']
        if qualifier:
            for Parameter in Command['Parameters']:
                try:
                    Status = Status[qualifier[Parameter]]
                except KeyError:
                    if Parameter in qualifier:
                        Status[qualifier[Parameter]] = {}
                        Status = Status[qualifier[Parameter]]
                    else:
                        return  
        try:
            if Status['Live'] != value:
                Status['Live'] = value
                self.NewStatus(command, value, qualifier)
        except:
            Status['Live'] = value
            self.NewStatus(command, value, qualifier)

    # Read the value from a command.
    def ReadStatus(self, command, qualifier=None):
        Command = self.Commands.get(command, None)
        if Command:
            Status = Command['Status']
            if qualifier:
                for Parameter in Command['Parameters']:
                    try:
                        Status = Status[qualifier[Parameter]]
                    except KeyError:
                        return None
            try:
                return Status['Live']
            except:
                return None
        else:
            raise KeyError('Invalid command for ReadStatus: ' + command)

    def __ReceiveData(self, interface, data):
        # Handle incoming data
        self.__receiveBuffer += data
        index = 0    # Start of possible good data
        # check incoming data if it matched any expected data from device module
        tempList = copy.copy(self.__matchStringDict)
        for regexString, CurrentMatch in tempList.items():
            while True:
                result = re.search(regexString, self.__receiveBuffer)
                if result:
                    index = result.start()
                    CurrentMatch['callback'](result, CurrentMatch['para'])
                    self.__receiveBuffer = self.__receiveBuffer[:result.start()] + self.__receiveBuffer[result.end():]
                else:
                    break
        if index:
            # Clear out any junk data that came in before any good matches.
            self.__receiveBuffer = self.__receiveBuffer[index:]
        else:
            # In rare cases, the buffer could be filled with garbage quickly.
            # Make sure the buffer is capped.  Max buffer size set in init.
            self.__receiveBuffer = self.__receiveBuffer[-self.__maxBufferSize:]

    # Add regular expression so that it can be check on incoming data from device.
    def AddMatchString(self, regex_string, callback, arg):
        if regex_string not in self.__matchStringDict:
            self.__matchStringDict[regex_string] = {'callback': callback, 'para':arg}

    def MissingCredentialsLog(self, credential_type):
        if isinstance(self, EthernetClientInterface):
            port_info = 'IP Address: {0}:{1}'.format(self.IPAddress, self.IPPort)
        elif isinstance(self, SerialInterface):
            port_info = 'Host Alias: {0}\r\nPort: {1}'.format(self.Host.DeviceAlias, self.Port)
        else:
            return 
        ProgramLog("{0} module received a request from the device for a {1}, "
                   "but device{1} was not provided.\n Please provide a device{1} "
                   "and attempt again.\n Ex: dvInterface.device{1} = '{1}'\n Please "
                   "review the communication sheet.\n {2}"
                   .format(__name__, credential_type, port_info), 'warning') 

class SerialClass(SerialInterface, DeviceClass):

    def __init__(self, Host, Port, Baud=115200, Data=8, Parity='None', Stop=1, FlowControl='Off', CharDelay=0, Mode='RS232', Model =None):
        SerialInterface.__init__(self, Host, Port, Baud, Data, Parity, Stop, FlowControl, CharDelay, Mode)
        self.ConnectionType = 'Serial'
        DeviceClass.__init__(self)
        # Check if Model belongs to a subclass
        if len(self.Models) > 0:
            if Model not in self.Models: 
                print('Model mismatch')              
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'Host Alias: {0}, Port: {1}'.format(self.Host.DeviceAlias, self.Port)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')
  
    def Discard(self, message):
        self.Error([message])

class SerialOverEthernetClass(EthernetClientInterface, DeviceClass):

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Serial'
        DeviceClass.__init__(self) 
        # Check if Model belongs to a subclass       
        if len(self.Models) > 0:
            if Model not in self.Models: 
                print('Model mismatch')              
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'IP Address/Host: {0}:{1}'.format(self.Hostname, self.IPPort)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')
  
    def Discard(self, message):
        self.Error([message])

    def Disconnect(self):
        EthernetClientInterface.Disconnect(self)
        self.OnDisconnected()

class EthernetClass(EthernetClientInterface, DeviceClass):

    def __init__(self, Hostname, IPPort, Protocol='TCP', ServicePort=0, Model=None):
        EthernetClientInterface.__init__(self, Hostname, IPPort, Protocol, ServicePort)
        self.ConnectionType = 'Ethernet'
        DeviceClass.__init__(self) 
        # Check if Model belongs to a subclass       
        if len(self.Models) > 0:
            if Model not in self.Models: 
                print('Model mismatch')              
            else:
                self.Models[Model]()

    def Error(self, message):
        portInfo = 'IP Address/Host: {0}:{1}'.format(self.Hostname, self.IPPort)
        print('Module: {}'.format(__name__), portInfo, 'Error Message: {}'.format(message[0]), sep='\r\n')
  
    def Discard(self, message):
        self.Error([message])

    def Disconnect(self):
        EthernetClientInterface.Disconnect(self)
        self.OnDisconnected()


def UseAutoUpdate(func):
    def wrapper(self, *args, **kwargs):
        res = func(self, *args, **kwargs)
        if self.auto_update:
            self.write_to_driver()
        return res

    return wrapper


class Directory:
    
    def __init__(self, display_count, control_id, filler=None):
        self._display_count = int(display_count)
        self.qualifier_name = 'Position'
        self._qualifier_type = 'Enum'

        self.control_id = control_id
        
        self.entry_list = []

        self._start_index = 0
        self.auto_update = True
        self.filler = filler
        self.first_filler = True
        self.entry_function = lambda entry: entry
        
    @property
    def display_count(self):
        return self._display_count
    
    @property
    def qualifier_type(self):
        return self._qualifier_type
    
    @qualifier_type.setter
    def qualifier_type(self, value):
        if value in ('Enum', 'Number'):
            self._qualifier_type = value
    
    def write_to_driver(self):

        for index, entry in enumerate(self.get_displayed_entries()):
            if self._qualifier_type == 'Number':
                position_value = index + 1
            else:
                position_value = str(index + 1)
            self.write_status_function(self.entry_function(entry[0]), {'Control ID': self.control_id, self.qualifier_name : position_value})

    def write_status_function(self, command, qualifier):
        pass    

    @UseAutoUpdate
    def add_entry(self, entry):
        if isinstance(entry, list):
            self.entry_list.extend(entry)
        else:
            self.entry_list.append(entry)
            
    @UseAutoUpdate
    def reset(self, newEntries=None):
        if isinstance(newEntries, list):
            self.entry_list.clear()
            self.entry_list.extend(newEntries)
        else:
            self.entry_list.clear()
        self._start_index = 0

    @UseAutoUpdate
    def remove_entry(self, display_position):

        
        if self.__display_position_check(display_position):
            try:
                return self.entry_list.pop(self._start_index + display_position - 1)
            except IndexError:
                return self.filler
        else:
            return self.filler
        
    def get_entry(self, display_position):

        if self.__display_position_check(display_position):
            try:
                return self.entry_list[self._start_index + display_position - 1]
            except IndexError:
                return self.filler
        else:
            return self.filler
        
    def get_displayed_entries(self):

        index = self._start_index
        while index <= self._start_index + self._display_count - 1:
            if index >= len(self.entry_list):
                yield self.filler, index + 1
            else:
                yield self.entry_list[index], index + 1
                
            index += 1

    def __display_position_check(self, position):

        return 0 < position <= self._display_count
        
    @UseAutoUpdate
    def scroll_up(self, step=1):
        if self._start_index - step >= 0:
            self._start_index -= step
        else:
            self._start_index = 0
    
    @UseAutoUpdate
    def scroll_down(self, step=1):
        if self._start_index + step < len(self.entry_list):
            self._start_index += step
        else:
            self._start_index = len(self.entry_list) - 1 # _start_index becomes the last item in the entry list
            if self._start_index < 0:
                self._start_index = 0
    
    @UseAutoUpdate
    def scroll_to_top(self):
        self._start_index = 0
    
    @UseAutoUpdate
    def scroll_to_bottom(self):
        self._start_index = len(self.entry_list) - 1
