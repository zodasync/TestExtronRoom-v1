## Begin ControlScript Import --------------------------------------------------
from extronlib import event, Version
from extronlib.device import eBUSDevice, ProcessorDevice, UIDevice
from extronlib.interface import (ContactInterface, DigitalIOInterface,
    EthernetClientInterface, EthernetServerInterfaceEx, FlexIOInterface,
    IRInterface, RelayInterface, SerialInterface, SWPowerInterface,
    VolumeInterface)
from extronlib.ui import Button, Knob, Label, Level
from extronlib.system import Clock, MESet, Wait, GetSystemUpTime, Ping

import datetime

class ConsoleClass:
    """
    CLASS: ConsoleClass
    AUTHOR: Eric Walters @ Status Controls (eric@statuscontrols.com)
    PARAMETERS:
        Port: TCP port to listen on (default = 9823),
        Usertable: A dictionary including usernames as the key and the value being a dictionary with password and access as keys
            Default: {'admin': {'password': 'extron', 'access': 2}, 'user': {'password': 'password', 'access': 1}},
        PubSub: The PubSub object to use to communicate with other code
    
    METHODS:
        RegisterCommand(string name,function callbackFunction,string shortDesc,string longDesc,integer access)
            Registers a custom command to be available for the console to use.
                >Name can't be help, exit, quit, bye. If a PubSub is defined, name also can't be register, unregister, trigger or list.
                >CallbackFunction is the handler for the defined console command.
                    Function should be defined FunctionName(client,cmd=None)
                >ShortDesc is sent to the client when a user types "help".
                >LongDesc is sent to the client when a user types "help name"
                >Access is the user access level required to use the command
        ListClients()
            Returns a dictionary object of connected clients. Example { 1: {'username': 'admin', 'ip': '192.168.1.1', 'access': 2}}
        DisconnectClient(integer clientID)
            Disconnects a client from the console using the client ID key from the ListClients dictionary
        DisconnectAllClients()
            Disconnects all clients connected to the console
    """
    def __init__(self,
        Title='GlobalScripter Debug Console v1.0',
        Port=9823,
        Usertable={'admin': {'password': 'extron', 'access': 2}, 'user': {'password': 'password', 'access': 1}},
        PubSub=None,
    ):
        self.__title = Title
        self.__usertable = Usertable
        self.__connectedusers = []                                                  # A list of connected users
        self.__portnum = Port
        self.__clients = []                                                         # A list of client objects
        self.__clientstate = {}                                                     # State information for each client
        self.__consoleport = EthernetServerInterfaceEx(self.__portnum,'TCP')        # The server port that handles multiple clients
        self.__ps = PubSub                                                          # The PubSub Object we're using to listen
        self.__lastchar = {}                                                        # Store the last character received from the client (for handling CRLF)

        self.__custom_commands = []                                                 # Custom Commands that the user can define externally
        self.__custom_cmd_dict = {}                                                 # Custom command storage

        # If you're going to add commands to the console, it needs to go in this list and also in the __cmd_dict below; see instructions
        # This list is to define what order they are shown in the "help" command, if they are set to be visible
        self.__commands = [
            'help',
            'uptime',
            'who',
            'kick',
            'exit',
            'quit',
            'bye',
        ]
        self.__cmd_dict = {
          # How to add commands:
          # 'command_name': {
          #     'func': The function to call when the user uses the command; should handle parameters or no parameters, see other commands
          #     'short': 'This is the description of the command when a user types "help"',
          #     'long': 'This is the long descript when the user types "help command_name"',
          #     'visible': True/False   - Should the command be listed in "help"
          # }
            'help': {
                'func': self.__help,
                'short': 'Displays a list of commands or help for a specific command.',
                'long': 'If you need help with help, you really need help.',
                'visible': True,
                'access': 1,
            },
            'uptime': {
                'func': self.__uptime,
                'short': 'Displays the current uptime of the system.',
                'long': 'Displays the system uptime. This is between power losses or reboots, not code updates.',
                'visible': True,
                'access': 1,
            },
            'who': {
                'func': self.__who,
                'short': 'Displays a list of connected clients and their associated info.',
                'long': 'Just type who. Nothing special.',
                'visible': True,
                'access': 2,
            },
            'kick': {
                'func': self.__kickclient,
                'short': 'Disconnect a client that is also connected to this console.',
                'long': 'Usage:\r\nkick <clientid>\r\nThe client ID is the number shown in the WHO command.',
                'visible': True,
                'access': 2,
            },
            'exit': {
                'func': self.__exit,
                'short': 'Disconnect from system. Can also use quit or bye.',
                'long': 'It disconnects you from the system. Come on.',
                'visible': True,
                'access': 1,
            },
            'quit': {
                'func': self.__exit,
                'short': 'Disconnect from system.',
                'long': 'It disconnects you from the system. Come on.',
                'visible': False,
                'access': 1,
            },
            'bye': {
                'func': self.__exit,
                'short': 'Disconnect from system.',
                'long': 'It disconnects you from the system. Come on.',
                'visible': False,
                'access': 1,
            },
        }

        if not self.__ps == None:
            def HandlePubSub(ev,data):
                if len(self.__clients):                                             # Is anybody connected?
                    for client in self.__clients:
                        if 'all' in self.__clientstate[client]['subscriptions']:   # Check to see if this client is registered for all events
                            client.Send('\r\n[{:%Y-%m-%d %H:%M:%S}] [{}] {}\r\n'.format(datetime.datetime.now(),ev,data))
                            client.Send('> ')
                        else:
                            for reg in self.__clientstate[client]['subscriptions']:
                                if reg in ev.lower():
                                    client.Send('[{:%Y-%m-%d %H:%M:%S}] [{}] {}\r\n'.format(datetime.datetime.now(),ev,data))
                                    client.Send('> ')

            self.__ps.RegisterListener(HandlePubSub)

            self.__commands.append('subscribe')
            self.__commands.append('unsubscribe')
            self.__commands.append('list')
            self.__commands.append('trigger')

            self.__cmd_dict['subscribe'] = {
                'func': self.__subscribe,
                'short': 'Subscribe for feedback for a specific device or system event.',
                'long': 'Usage: subscribe <name>\r\nName can be a specific device, "system", or "all".',
                'visible': True,
                'access': 1,
            }
            self.__cmd_dict['unsubscribe'] = {
                'func': self.__unsubscribe,
                'short': 'Stop feedback for a specific device or system event.',
                'long': 'Usage: unsubscribe <name>\r\nName can be a specific device, "system", or "all".',
                'visible': True,
                'access': 1,
            }
            self.__cmd_dict['list'] = {
                'func': self.__list,
                'short': 'List of available devices that have registered with the event system.',
                'long': 'Usage: list\r\nThis command lists devices that have registered with the event system.\r\nThese device names can be used with the "register" command.',
                'visible': False,
                'access': 1,
            }
            self.__cmd_dict['trigger'] = {
                'func': self.__trigger,
                'short': 'Trigger an event in the system manually. Requires a device parameter and data to send.',
                'long': 'Usage: trigger <name> <data to send>\r\nThis requires specific knowledge of the program and what objects have registered for events.',
                'visible': True,
                'access': 1,
            }

        else:
            print('No PubSub object defined for Debugger Console. Hopefully you have custom commands defined.')

        if self.__consoleport.StartListen() != 'Listening':
            raise ResourceWarning('Port unavailable')

        @event(self.__consoleport,'Connected')
        def __consoleconnect(this_client, state):
            # Add the client to the list and set up an initial state
            self.__clients.append(this_client)
            self.__clientstate[this_client] = {
                'status':'login_user',              # Status holds where in the process the client is at: login_user, login_pass, logged_in
                'buffer':'',                        # Keyboard buffer
                'invalid_logins':0,                 # How many invalid logins they've had
                'temp_user':'',                     # A temporary username holder
                'auth_user':'',                     # The actual logged in user
                'access':0,                         # The user's access level
                'subscriptions':[],                 # Active subscriptions
                }
            if self.__ps is not None:
                self.__ps.TriggerEvent('System',{'event': 'client_connect', 'msg': 'Incoming connection from {} on console port. {} connections.'.format(this_client.IPAddress,len(self.__clients))})
            self.__disable_client_echo(this_client)
            this_client.Send('{} (ExtronLib v{})\r\nUsername: '.format(self.__title,Version()))
        
        @event(self.__consoleport,'Disconnected')
        def __consoledisconnect(this_client, state):
            # Remove the client from the list and delete its state data
            self.__clients.remove(this_client)
            self.__clientstate.pop(this_client, None)
            if self.__ps is not None:
                self.__ps.TriggerEvent('System',{'event': 'client_disconnect', 'msg':'{} disconnected from console. {} connections.'.format(this_client.IPAddress,len(self.__clients))})

        @event(self.__consoleport,'ReceiveData')
        def __consolereceive(this_client, data):
            cs = self.__clientstate[this_client]                                                     # Create a pointer variable so we don't have to type so much
            
            for char in data:
                if char == 8 and len(cs['buffer']):                                             # Backspace
                    cs['buffer'] = cs['buffer'][:-1]
                    if not cs['status'] == 'login_pass':                                        # We're not echoing back during password anyway
                        this_client.Send(chr(8))
                        this_client.Send(' ')
                        this_client.Send(chr(8))
                elif char == 13 or (char == 10 and self.__lastchar[this_client] != 13):              # CR or LF without a CR before it
                    if cs['status'] == 'login_user':                                            # is the user logging in?
                        if len(cs['buffer']):                                                   # Have they typed anything?
                            cs['temp_user'] = str(cs['buffer'])                                 # Store the username for later
                            cs['buffer'] = ''                                                   # Clear the buffer
                            cs['status'] = 'login_pass'                                         # Set the client state to now listen for a password
                            this_client.Send('\r\nPassword: ')
                        else:
                            cs['buffer'] = ''
                            this_client.Send('Username: ')
                    elif cs['status'] == 'login_pass':                                          # Check for password
                        # Check if the user exists in the user table and if the password matches
                        if cs['temp_user'] in self.__usertable and cs['buffer'] == self.__usertable[cs['temp_user']]['password']:       # CORRECT LOGIN
                            cs['auth_user'] = str(cs['temp_user'])                              # Set logged in username
                            cs['access'] = int(self.__usertable[cs['auth_user']]['access'])     # Set user access level
                            cs['buffer'] = ''
                            cs['status'] = 'logged_in'                                          # Set client status
                            this_client.Send('\r\n\r\nWelcome, {}.\r\n> '.format(cs['auth_user']))
                            if self.__ps is not None:
                                self.__ps.TriggerEvent('System',{'event': 'valid_login', 'msg': '{} logged in from {}.'.format(cs['auth_user'],this_client.IPAddress)})
                            self.__set_clientIds()
                        else:                                                                   # Invalid username or password
                            cs['invalid_logins'] = cs['invalid_logins'] + 1
                            if cs['invalid_logins'] < 3:
                                if self.__ps is not None:
                                    self.__ps.TriggerEvent('System',{'event': 'invalid_login', 'msg':'Invalid login from {} using username: {}'.format(this_client.IPAddress,cs['temp_user'])})
                                this_client.Send('\r\nInvalid login.\r\n\r\nUsername: ')
                                cs['status'] = 'login_user'                                     # Reset the status to listen for username
                                cs['temp_user'] = ''
                                cs['buffer'] = ''
                            else:
                                if self.__ps is not None:
                                    self.__ps.TriggerEvent('System',{'event': 'bad_login_attempt', 'msg': 'Disconnecting console port for too many login attempts: {}'.format(this_client.IPAddress)})
                                this_client.Send('\r\nToo many login attempts.')
                                self.__consoleport.Disconnect(this_client)
                    else:                                                           # User is logged in so send command off to handler
                        if len(cs['buffer']):
                            self.__handle_command(this_client,str(cs['buffer']))         # Using str() here to copy the string as a value, otherwise the next line deletes it
                            cs['buffer'] = ''
                        else:
                            this_client.Send('\r\n> ')
                elif char < 32 or char > 127:                                       # Ignore characters that aren't alphanumeric
                    pass
                else:                                                               # Add data to buffer
                    cs['buffer'] = cs['buffer'] + chr(char)
                    if not cs['status'] == 'login_pass':
                        this_client.Send(chr(char))
                self.__lastchar[this_client] = char                                          # Store previous character for stuff

    def __set_clientIds(self):
        clientId = 0
        for client in self.__clients:
            self.__clientstate[client]['clientId'] = clientId
            clientId += 1

    def __disable_client_echo(self,this_client):
        this_client.Send(b'\xFF\xFE\x01')

    def __enable_client_echo(self,this_client):
        this_client.Send(b'\xFF\xFD\x01')

    def RegisterCommand(self,cmd,callbackFunc,shortDesc,longDesc,access=1):
        if cmd not in self.__commands and cmd not in self.__custom_commands:
            self.__custom_commands.append(cmd)
            self.__custom_cmd_dict[cmd] = {
                'func': callbackFunc,
                'short': shortDesc,
                'long': longDesc,
                'visible': True,
                'access': access
            }

    def ListConnections(self):
        returnDict = {}
        for client in self.__clients:
            cs = self.__clientstate[client]
            returnDict[cs['clientId']] = {'username':cs['auth_user'], 'ip': client.IPAddress, 'access': cs['access']}

    def DisconnectClient(self,clientId):
        for client in self.__clients:
            if self.__clientstate['clientId'] == clientId:
                client.Send('\r\nYou have been disconnected. Goodbye.')
                self.__consoleport.Disconnect(client)

    def DisconnectAll(self):
        for client in self.__clients:
            client.Send('\r\nYou have been disconnected. Goodbye.')
            self.__consoleport.Disconnect(client)

    def __handle_command(self,this_client,cmd):                                                  # Handle stuff here
        ca = self.__clientstate[this_client]['access']                                           # Client Access
        if ' ' in cmd:                                                                      # a command with a parameter maybe?
            cmd_data = cmd.lower().split(' ')                                               # Split the incoming command into words, after converting to lowercase just to make sure we understand what the user wants easily
            if cmd_data[0] in self.__commands and ca >= self.__cmd_dict[cmd_data[0]]['access']:    # If we have the command, call its handler function
                self.__cmd_dict[cmd_data[0]]['func'](this_client,cmd)                           # The handler is called with the original command string
            elif cmd_data[0] in self.__custom_commands and ca >= self.__custom_cmd_dict[cmd_data[0]]['access']:
                self.__custom_cmd_dict[cmd_data[0]]['func'](this_client,' '.join(cmd.split(' ')[1:]))       # Custom functions only get the parameters, however
            else:
                this_client.Send('\r\nInvalid command. Please see "help".')
        elif cmd in self.__commands and ca >= self.__cmd_dict[cmd]['access']:     # a command with no parameters
            self.__cmd_dict[cmd]['func'](this_client)
        elif cmd in self.__custom_commands and ca >= self.__custom_cmd_dict[cmd]['access']:
            self.__custom_cmd_dict[cmd]['func'](this_client)
        else:
            this_client.Send('\r\nInvalid command. Please see "help".')
        
        if this_client in self.__clients:                                                        # Make sure we're still connected in case they used "exit" or something
            this_client.Send('\r\n> ')

    def __send_client_subscriptions(self,this_client):
        cs = self.__clientstate[this_client]['subscriptions']                            # Less typing, make a smaller variable
        this_client.Send('\r\nActive subscriptions:\r\n')
        if len(cs):                                                                 # If there are subscriptions
            for ev in cs:
                this_client.Send(' {}\r\n'.format(ev))
        else:
            this_client.Send(' None.\r\n')

    def __help(self,this_client,cmd=None):                                                       # Help without parameters lists commands, help with parameters shows help for that command
        ca = self.__clientstate[this_client]['access']                                           # Client Access
        if cmd is not None:
            cmd_data = cmd.lower().split(' ')[1:]
        else:
            cmd_data = []

        if len(cmd_data):                                                                   # Were parameters passed in?
            if cmd_data[0] in self.__commands and ca >= self.__cmd_dict[cmd_data[0]]['access']:
                this_client.Send('\r\n{}\r\n'.format(self.__cmd_dict[cmd_data[0]]['long']))
            elif cmd_data[0] in self.__custom_commands and ca >= self.__custom_cmd_dict[cmd_data[0]]['access']:
                this_client.Send('\r\n{}\r\n'.format(self.__custom_cmd_dict[cmd_data[0]]['long']))
            else:
                this_client.Send('\r\nThat command doesn''t exist. Try again.\r\n')
        else:
            this_client.Send('\r\n\r\nAvailable commands:\r\n')
            for command in self.__commands:
                if self.__cmd_dict[command]['visible'] and ca >= self.__cmd_dict[command]['access']:
                    this_client.Send(' {0:16}{1}\r\n'.format(command,self.__cmd_dict[command]['short']))
            if len(self.__custom_commands):
                this_client.Send('\r\nCustom commands:\r\n')
                for command in self.__custom_commands:
                    if ca >= self.__custom_cmd_dict[command]['access']:
                        this_client.Send(' {0:16}{1}\r\n'.format(command,self.__custom_cmd_dict[command]['short']))

    def __uptime(self,this_client,cmd=None):
        time = int(GetSystemUpTime() / 60)          # get uptime in minutes
        if time < 60:                               # less than an hour
            this_client.Send('\r\nCurrent uptime is: {} minutes.'.format(time))
        elif time < 1440:                           # less than a day
            this_client.Send('\r\nCurrent uptime is: {} hours, {} minutes.'.format(int(time / 60),time % 60))
        else:                                       # more than a day
            this_client.Send('\r\nCurrent uptime is: {} days, {} hours, {} minutes.'.format(int(time / 1440),int((time % 1440) / 60),time % 60))

    def __who(self,this_client,cmd=None):
        for client in self.__clients:
            cs = self.__clientstate[client]
            this_client.Send('\r\nClient Id: {}, User: {}, IP: {}, Access level: {}'.format(cs['clientId'],cs['auth_user'],client.IPAddress,cs['access']))

    def __kickclient(self,this_client,cmd=None):
        if cmd is not None:
            cmd_data = cmd.lower().split(' ')[1:]
        else:
            cmd_data = []

        try:
            if int(cmd_data[0]) == self.__clientstate[this_client]['clientId']:
                this_client.Send('\r\nPlease don''t kick yourself. People will stare.')
            else:
                for client in self.__clients:
                    if client is not this_client and self.__clientstate[client]['clientId'] == int(cmd_data[0]):
                        client.Send('\r\nYou have been kicked. Goodbye.')
                        self.__consoleport.Disconnect(client)
        except ValueError:
            this_client.Send('\r\nPlease use the client ID shown in the WHO command.')
        except TypeError:
            this_client.Send('\r\nPlease use the client ID shown in the WHO command.')

    def __subscribe(self,this_client,cmd=None):                                                   # subscribe with one or more parameters adds an event registration to the current client
        if cmd is not None:
            cmd_data = cmd.lower().split(' ')[1:]
        else:
            cmd_data = []

        if len(cmd_data):                                                                   # Were parameters passed in?
            cs = self.__clientstate[this_client]['subscriptions']                                # Less typing, make a smaller variable
            if not 'all' in cs:                                                             # "subscribe all" is special and will listen for all events, this overrides all other event subscriptions
                if 'all' in cmd_data:
                    cs.clear()
                    cs.append('all')
                else:                                                                       # Add all events to the registration list
                    for ev in cmd_data:
                        if ev not in cs:
                            cs.append(ev)
        self.__send_client_subscriptions(this_client)                                            # Tell the user what all they're subscribeed to

    def __unsubscribe(self,this_client,cmd=None):                                                 # Unsubscribe with one or more parameters deletes those events from the registration list
        if cmd is not None:
            cmd_data = cmd.lower().split(' ')[1:]
        else:
            cmd_data = []

        if len(cmd_data):
            cs = self.__clientstate[this_client]['subscriptions']                                # Less typing, make a smaller variable
            for ev in cmd_data:
                if ev == 'all':                                                             # "unsubscribe all" deletes all events from the list
                    cs.clear()
                elif ev in cs:                                                              # Delete all events passed from the list
                    cs.remove(ev)
        self.__send_client_subscriptions(this_client)

    def __list(self,this_client,cmd=None):
        this_client.Send('\r\nAvailable devices or events:\r\n')

    def __trigger(self,this_client,cmd=None):
        if cmd is not None:
            cmd_data = cmd.split(' ')[1:]

            if len(cmd_data) > 1:                                                           # Does the event have data attached
                self.__ps.TriggerEvent(cmd_data[0],' '.join(cmd_data[1:]))                  # Referencing the original incoming cmd so that we get all the original string case
            else:
                this_client.Send('\r\nError: Trigger requires both an event name and data to be passed. Please see "help trigger".\r\n')
        else:
            this_client.Send('\r\nThis command requires extra arguments. Please see the help for ''trigger''.\r\n')


    def __exit(self,this_client,cmd=None):
        this_client.Send('\r\nGoodbye.')
        self.__consoleport.Disconnect(this_client)

