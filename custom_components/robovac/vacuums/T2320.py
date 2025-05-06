from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand


class T2320:
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        # | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
        # | VacuumEntityFeature.MAP
    )
    robovac_features = (
        # RoboVacEntityFeature.CLEANING_TIME
        # RoboVacEntityFeature.CLEANING_AREA
        RoboVacEntityFeature.DO_NOT_DISTURB
        # RoboVacEntityFeature.AUTO_RETURN
        # RoboVacEntityFeature.ROOM
        # RoboVacEntityFeature.ZONE
        | RoboVacEntityFeature.BOOST_IQ
        # RoboVacEntityFeature.MAP
        # RoboVacEntityFeature.CONSUMABLES
    )
    commands = {
        RobovacCommand.MODE: {  # works   (Start Auto and Return dock commands tested)
            "code": 152,
            "values": ["AggN", "AA==", "AggG", "BBoCCAE=", "AggO"],
        },
        RobovacCommand.STATUS: 173,  # works
        RobovacCommand.RETURN_HOME: {  # works
            "code": 153,
            "values": ["AggB"]
        },
        RobovacCommand.FAN_SPEED: {  # Works
            "code": 154,
            "values": ["AgkBCgIKAQoDCgEKBAoB"]
        },
        RobovacCommand.LOCATE: {  # Works
            "code": 153,
            "values": ["AggC"]
        },
        RobovacCommand.BATTERY: 172,  # Works
        RobovacCommand.ERROR: 169,  # works
        # These command may have been added to the base.py if not they need codes adding
        # RoboVacEntityFeature.CLEANING_TIME: 0,
        # RoboVacEntityFeature.CLEANING_AREA: 0,
        RoboVacEntityFeature.DO_NOT_DISTURB: {  # Works
            "code": 163,
            "values": ["AQ==", "AA=="],
        },
        # RoboVacEntityFeature.AUTO_RETURN: 0,
        # RoboVacEntityFeature.ROOM: 0,
        # RoboVacEntityFeature.ZONE: 0,
        RoboVacEntityFeature.BOOST_IQ: {  # Works
            "code": 161,
            "values": ["AQ==", "AA=="],
        },
        # RoboVacEntityFeature.MAP: 0,
        # RoboVacEntityFeature.CONSUMABLES: 0,
        # Unknown: 151
        #    EgYIBBgCEAEYARACEAE=
        # Unknown: 155
        #    EgIIAQ==
        # Unknown: 156
        #    CAE=
        #    EgIIAQ==
        #    CgIIAQ==
        # Unknown: 157
        #    CAE=
        #    CAI=
        #    CAM=
        # Unknown: 158
        #    CAE=
        #    CAI=
        #    CAM=
        #    CAQ=
        # Unknown: 159
        #    EgQIAhAB
        #    EgQIAxAB
        #    EgQIBBAB
        #    EgQIBRAB
        #    EgQIBhAB
        #    EgQIBxAB
        # Unknown: 160
        #    CAE=
        #    CAI=
        #    CAM=
        # Unknown: 162 (WorkModeStatus)
        #    CAA=
        #    CAE=
        #    CAI=
        #    CAM=
        #    CAQ=
        #    CAU=
        #    CAG=
        #    CAc=
        #    CAg=
        #    CAk=
        #    CAo=
        #    CAs=
        #    CAw=
        #    CA0=
        #    CA4=
        #    CA8=
        #    CBA=
        #    CBE=
        # Unknown: 164
        #    CAE=
        #    CAI=
        #    CAM=
        #    CAQ=
        #    CAU=
        #    CAG=
        #    CAc=
        #    CAg=
        #    CAk=
        #    CAo=
        #    CAs=
        #    CAw=
        #    CA0=
        #    CA4=
        #    CA8=
        # Unknown: 165
        #    EgIIAQ==
        #    CAA=
        #    CAE=
        # Unknown: 166
        #    CAE=
        #    CAI=
        # Unknown: 167
        #    CAA=
        #    CAE=
        #    CAI=
        # Unknown: 168 (CleanSpeed)
        #    CAA=
        #    CAE=
        #    CAI=
        #    CAM=
        # Unknown: 170
        #    EgIIAQ==
        # Unknown: 171
        #    EgIITA==
        #    EgIIUg==
        #    EgIIVg==
        #    EgIIQw==
        #    EgIITA==
        #    EgIIUg==
        #    EgIIVg==
        #    EgIIQw==
        # Unknown: 174
        #    CAE=
        #    CAI=
        #    CAM=
        # Unknown: 175
        #    EgIIAQ==
        # Unknown: 176
        #    EgIIAQ==
        # Unknown: 177
        #    CAE=
        #    LwoAGgBSCBoAIgIIASoAWLvdgrUGGhFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWLvdgrUGGhFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWLvdgrUGGhFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWFJYHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWFJYHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWFJYHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWFJYHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGECvdgrUG
        #    LwoAGgBSCBoAIgIIASoAWCJiHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGEPvagrUG
        #    LwoAGgBSCBoAIgIIASoAWFZiHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGEPvagrUG
        #    LwoAGgBSCBoAIgIIASoAWCJiHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGEK2YgLUG
        #    LwoAGgBSCBoAIgIIASoAWDBiHQobChFBIG5ldHdvcmsgZm9yIHlvdRoGEK2YgLUG
        # Unknown: 178
        #    DQjRidjfv9bszgESAR8=
        #    DQiMrPbd+eLszgESAVU=
        #    DQiW0dXL+uLszgESAR8=
        #    Cgiv6NbWsePszgE=
        #    DQjPuorb6eTszgESAR8=
        #    DQjayd7nsOXszgESASg=
        # Unknown: 179
        #    EBIOKgwIBRACGAEgwYyAtQY=
        #    FhIUEhIIBRABIFsowYyAtQYw74yAtQY=
        #    DhIMKgoIBhgCIPvagrUG
        #    DhIMKgoIBxgCIJLbgrUG
        #    EBIOKgwIBxADGAIg3eyCtQY=
        #    EBIOKgwIBxAEGAIgrPGCtQY=
        #    DhIMKgoICBgCILHxgrUG
        #    DhIMKgoICBADIIj6grUG
        #    DhIMKgoICBADIOqMg7UG
        #    DhIMKgoICBAEIOuMg7UG
        #    DBIKKggICSCljYO1Bg==
        #    DhIMKgoICRACIJmcg7UG
        #    FhIUEhIICRABIBoomZyDtQYw6pyDtQY=
        #    DhIMIgoICRABGO+cg7UG
        #    DhIMIgoICRABGLedg7UG
        #    IRIfCh0ICRgBMPvagrUGOMmdg7UGQKApSDhQO1gBYAdqAA==
        # Unknown: 169
        #    cwoSZXVmeSBDbGVhbiBMNjAgU0VTGhFDODpGRTowRjo3Nzo5NDo5QyIGMS4zLjI0KAVCKDM2NGFjOGNkNjQzZjllMDczZjg4NzlmNGFhOTdkZGE5OGUzMjg5NTRiFggBEgQIAhABGgQIAhABIgIIASoCCAE=
        #    s \x12eufy Clean L60 SES\x1a\x11C8:FE:0F:77:94:9C"\x061.3.24(\x05B(364ac8cd643f9e073f8879f4aa97dda98e328954b\x16\x08\x01\x12\x04\x08\x02\x10\x01\x1a\x04\x08\x02\x10\x01"\x02\x08\x01*\x02\x08\x01
    }
