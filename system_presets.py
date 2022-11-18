# ---------------------------------------------------------------------------------------------------------------------
# System Preset Definitions
# ---------------------------------------------------------------------------------------------------------------------
ShowReady_Mode_Preset = {
    # Dest: Source
    'video': {
        1:      1,
        2:      3,
        3:      4,
        4:      5,
        5:      7,
        6:      8,
        7:      9,
        8:      10,
        9:      11,
        10:     12,
        11:     13,
        12:     14,
        13:     17,
        14:     18,
        15:     19,
        16:     20,
        17:     21,
        18:     22,
        19:     17,
        20:     18,
        21:     19,
        22:     20,
        23:     21,
        24:     22,
    },
    'audio': {
        'tesira': {
            'WELCOME_LEV':          { 'level': -20, 'mute': False },
            'THEATER_WPLEV':        { 'level': -20, 'mute': True },
            'IGLOO_LEV':            { 'level': -20, 'mute': False },
            'INFRA_LEV':            { 'level': -20, 'mute': False },
            'CITZ_LEV':             { 'level': -20, 'mute': False },
            'EDGE_LEV':             { 'level': -20, 'mute': False },
            'CMD_LEV':              { 'level': -20, 'mute': False },
            'CLOSING_LEV':          { 'level': -20, 'mute': False },
        },
        'ssp200': {
            'Volume':   50,
            'Mute':     False,
        }
    },
    'lights': {
        'Bank 1': {
            'G1-100': '255:1'
        },
        'Bank 2': {
            'G1-100': '255:1'
        },
    },
}

Shutdown_Mode_Preset = {
    # Dest: Source
    'video': {
        1:      0,
        2:      0,
        3:      0,
        4:      0,
        5:      0,
        6:      0,
        7:      0,
        8:      0,
        9:      0,
        10:     0,
        11:     0,
        12:     0,
        13:     0,
        14:     0,
        15:     0,
        16:     0,
        17:     0,
        18:     0,
        19:     0,
        20:     0,
        21:     0,
        22:     0,
        23:     0,
        24:     0,
    },
    'audio': {
        'tesira': {
            'WELCOME_LEV':          { 'level': -40, 'mute': True },
            'THEATER_WPLEV':        { 'level': -40, 'mute': True },
            'IGLOO_LEV':            { 'level': -40, 'mute': True },
            'INFRA_LEV':            { 'level': -40, 'mute': True },
            'CITZ_LEV':             { 'level': -40, 'mute': True },
            'EDGE_LEV':             { 'level': -40, 'mute': True },
            'CMD_LEV':              { 'level': -40, 'mute': True },
            'CLOSING_LEV':          { 'level': -40, 'mute': True },
        },
        'ssp200': {
            'Volume':   50,
            'Mute':     True,
        }

    },
    'lights': {
        'Bank 1': {
            'G1-100': '0:1'
        },
        'Bank 2': {
            'G1-100': '0:1'
        },
    },
}
