"""eufy Clean L60 SES (T2277)"""
# TODO: Replace the base64 string lookup tables for MODE (DPS 152) and STATUS (DPS 153)
#       with proper protobuf parsing based on the official Eufy proto schemas:
#         - DPS 152 (MODE)   → proto.cloud.ModeCtrlRequest  (control.proto)
#         - DPS 153 (STATUS) → proto.cloud.WorkStatus       (work_status.proto)
#         - DPS 177 (ERROR)  → proto.cloud.ErrorCode        (error_code.proto)
#                              error codes enum in error_code_list_t2265.proto
#       Source: https://github.com/terabyte128/eufy-mqtt-vacuum/tree/main/proto/cloud
#       The current approach cannot handle new firmware variants that encode the same
#       logical state with different seq/suction values in field_2, and will always
#       produce unknown-value warnings for unseen base64 strings.
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails


class T2277(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.BATTERY
        | VacuumEntityFeature.CLEAN_SPOT
        | VacuumEntityFeature.FAN_SPEED
        | VacuumEntityFeature.LOCATE
        | VacuumEntityFeature.PAUSE
        | VacuumEntityFeature.RETURN_HOME
        | VacuumEntityFeature.SEND_COMMAND
        | VacuumEntityFeature.START
        | VacuumEntityFeature.STATE
        | VacuumEntityFeature.STOP
    )
    robovac_features = (
        RoboVacEntityFeature.DO_NOT_DISTURB
        | RoboVacEntityFeature.BOOST_IQ
    )
    commands = {
        RobovacCommand.MODE: {
            # DPS code 152. Payload format: [length_prefix_byte] + protobuf (ModeCtrlRequest)
            #
            # Proto schema (control.proto — ModeCtrlRequest):
            #   field_1 [varint]  method — the command being sent:
            #                       6=START_GOHOME, 12=STOP_TASK, 13=PAUSE_TASK,
            #                       14=RESUME_TASK, 0=START_AUTO_CLEAN (via field_3 param)
            #   field_2 [varint]  seq    — request sequence number for response matching.
            #                       NOT a suction level. Values like 104/108/112 are
            #                       coincidental sequence numbers from observed captures.
            #   field_3 [message] param  — oneof Param, present for START_AUTO_CLEAN:
            #                       AutoClean { field_1 clean_times=1 }
            #
            # NOTE: What was previously labelled "nosweep" is actually method=RESUME_TASK (14).
            #       What was previously labelled "stop" is actually method=START_GOHOME (6),
            #       i.e. it sends the robot home rather than stopping in place.
            #
            # TODO: Replace reverse lookup with protobuf decode of field_1 (method enum).
            #       field_2 (seq) should be ignored in reverse lookups as it varies per call.
            "code": 152,
            "values": {
                # --- Commands (human-readable → protobuf) ---
                "standby": "AA==",      # empty payload
                "pause": "AggN",        # method=PAUSE_TASK (13)
                "stop": "AggG",         # method=START_GOHOME (6) — sends robot home, not stop-in-place
                "return": "AggG",       # method=START_GOHOME (6) — same as stop on this model
                "auto": "BBoCCAE=",     # param.auto_clean={clean_times=1}
                "nosweep": "AggO",      # method=RESUME_TASK (14) — resumes a paused task

                # --- Reverse lookup (protobuf → human-readable) ---
                # TODO: These will miss any payload where field_2 (seq) has a different value.
                #       Proper fix: decode field_1 (method) only, ignore field_2 (seq).
                "AA==": "standby",
                "AggN": "pause",        # method=PAUSE_TASK (13), no seq
                "AggG": "stop",         # method=START_GOHOME (6), no seq
                "BBoCCAE=": "auto",     # param.auto_clean={clean_times=1}
                "AggO": "nosweep",      # method=RESUME_TASK (14), no seq

                # method=RESUME_TASK (14) with seq=112 — same logical action as "nosweep"/resume,
                # seq value is irrelevant for state interpretation.
                # TODO: with proper protobuf parsing this would just decode to method=RESUME_TASK.
                "AhBw": "auto",         # seq=112 only, no method field — likely a BoostIQ param update

                # method=PAUSE_TASK (13) with seq=104
                # TODO: with proper protobuf parsing this would just decode to method=PAUSE_TASK.
                "BAgNEGg=": "pause",    # method=PAUSE_TASK (13), seq=104

                # method=RESUME_TASK (14) with seq=104 (standard suction run)
                # TODO: with proper protobuf parsing this would just decode to method=RESUME_TASK.
                "BAgOEGg=": "nosweep",  # method=RESUME_TASK (14), seq=104

                # method=RESUME_TASK (14) with seq=108 (turbo suction run)
                # TODO: with proper protobuf parsing this would just decode to method=RESUME_TASK.
                "BAgOEGw=": "nosweep",  # method=RESUME_TASK (14), seq=108
            },
        },
        RobovacCommand.START_PAUSE: {  # via mode command
            "code": 152,
            "values": {
                "pause": "AggN",        # method=PAUSE_TASK (13)
            },
        },
        RobovacCommand.RETURN_HOME: {  # via mode command
            "code": 152,
            "values": {
                "return": "AggG",       # method=START_GOHOME (6)
            },
        },
        RobovacCommand.STATUS: {
            # DPS code 153. Payload format: [length_prefix_byte] + protobuf (WorkStatus)
            #
            # Proto schema (work_status.proto — WorkStatus):
            #   field_1  [message] Mode      { field_1 value: 0=AUTO, 1=SELECT_ROOM, 2=SELECT_ZONE,
            #                                  3=SPOT, 4=FAST_MAPPING, 5=GLOBAL_CRUISE, ... }
            #   field_2  [varint]  State       0=STANDBY, 1=SLEEP, 2=FAULT, 3=CHARGING,
            #                                  4=FAST_MAPPING, 5=CLEANING, 6=REMOTE_CTRL,
            #                                  7=GO_HOME, 8=CRUISING
            #   field_3  [message] Charging  { field_1: 0=DOING, 1=DONE, 2=ABNORMAL }
            #   field_6  [message] Cleaning  { field_1 RunState: 0=DOING, 1=PAUSED;
            #                                  field_2 Mode: 0=CLEANING, 1=RELOCATING, 2=GOTO_POS, 3=POOP }
            #   field_8  [message] GoHome    { field_1 RunState: 0=DOING, 1=PAUSED;
            #                                  field_2 Mode: 0=COMPLETE_TASK, 1=COLLECT_DUST, 10=OTHERS }
            #   field_10 [message] Relocating { field_1: 0=DOING } — robot relocalizing on map
            #   field_11 [message] Breakpoint  { field_1: 0=DOING } — resume-after-charge pending
            #
            # NOTE: "spot" mode maps to Mode.value=SELECT_ZONE (2), not SPOT (3).
            #       "positioning" = state=CLEANING + Relocating present (not a separate state).
            #       "going_to_recharge" / "recharging" = GoHome/Charging + Breakpoint present.
            #
            # TODO: Replace base64 string lookup with protobuf decode of WorkStatus.
            #       Decode logic: check State (field_2) first, then Mode (field_1), then
            #       sub-state messages (Cleaning, GoHome, Charging, Relocating, Breakpoint).
            #       This would handle all firmware variants without needing new b64 entries.
            "code": 153,
            "values": {
                # --- Commands (human-readable → protobuf) ---
                "auto": "BgoAEAUyAA==",
                "positioning": "BgoAEAVSAA==",
                "Paused": "CAoAEAUyAggB",          # capitalized in vacuum.py
                "room": "CAoCCAEQBTIA",
                "room_positioning": "CAoCCAEQBVIA",
                "room_pause": "CgoCCAEQBTICCAE=",
                "spot": "CAoCCAIQBTIA",
                "spot_positioning": "CAoCCAIQBVIA",
                "spot_pause": "CgoCCAIQBTICCAE=",
                "start_manual": "BAoAEAY=",
                "going_to_charge": "BBAHQgA=",
                "going_to_recharge": "CAoAEAdCAFoA",
                "Charging": "BBADGgA=",            # capitalized in vacuum.py
                "recharging": "CAoAEAMaAFoA",
                "completed": "BhADGgIIAQ==",
                "Standby": "AA==",                 # capitalized in vacuum.py
                "Sleeping": "AhAB",                # capitalized in vacuum.py

                # --- Reverse lookup (protobuf → human-readable) ---
                # TODO: Replace with protobuf decode. Each entry below corresponds to a specific
                #       combination of WorkStatus fields; with proper parsing these would be
                #       derived from the decoded struct rather than matched as opaque strings.

                # WorkStatus { mode=AUTO(0), state=CLEANING(5), cleaning={DOING, CLEANING} }
                # The === and == variants are identical payloads; firmware sends both
                # depending on version, differing only in base64 padding characters.
                "BgoAEAUyAA===": "auto",
                "BgoAEAUyAA==": "auto",

                # WorkStatus { mode=AUTO(0), state=CLEANING(5), relocating={DOING} }
                # relocating = Relocating sub-state, robot is relocalizing on the map.
                # Same padding inconsistency as auto above.
                "BgoAEAVSAA===": "positioning",
                "BgoAEAVSAA==": "positioning",

                # WorkStatus { mode=AUTO(0), state=CLEANING(5), cleaning={PAUSED, CLEANING} }
                "CAoAEAUyAggB": "Paused",          # capitalized in vacuum.py

                # WorkStatus { mode=SELECT_ROOM(1), state=CLEANING(5), cleaning={DOING, CLEANING} }
                "CAoCCAEQBTIA": "room",
                # WorkStatus { mode=SELECT_ROOM(1), state=CLEANING(5), relocating={DOING} }
                "CAoCCAEQBVIA": "room_positioning",
                # WorkStatus { mode=SELECT_ROOM(1), state=CLEANING(5), cleaning={PAUSED, CLEANING} }
                "CgoCCAEQBTICCAE=": "room_pause",

                # WorkStatus { mode=SELECT_ZONE(2), state=CLEANING(5), cleaning={DOING, CLEANING} }
                # Note: mode value 2 = SELECT_ZONE, not SPOT (3). Spot cleans are zone-based.
                "CAoCCAIQBTIA": "spot",
                # WorkStatus { mode=SELECT_ZONE(2), state=CLEANING(5), relocating={DOING} }
                "CAoCCAIQBVIA": "spot_positioning",
                # WorkStatus { mode=SELECT_ZONE(2), state=CLEANING(5), cleaning={PAUSED, CLEANING} }
                "CgoCCAIQBTICCAE=": "spot_pause",

                # WorkStatus { mode=AUTO(0), state=REMOTE_CTRL(6) }
                "BAoAEAY=": "start_manual",

                # WorkStatus { state=GO_HOME(7), go_home={DOING, COMPLETE_TASK} }
                # Robot returning to dock after clean is fully finished.
                "BBAHQgA=": "going_to_charge",
                # WorkStatus { mode=AUTO(0), state=GO_HOME(7), go_home={DOING, COMPLETE_TASK},
                #              breakpoint={DOING} }
                # Robot returning to dock mid-clean; breakpoint flag means it will resume after charging.
                "CAoAEAdCAFoA": "going_to_recharge",

                # WorkStatus { state=CHARGING(3), charging={DOING} }
                # Normal charging after a completed clean or manual dock.
                "BBADGgA=": "Charging",            # capitalized in vacuum.py
                # WorkStatus { mode=AUTO(0), state=CHARGING(3), charging={DOING},
                #              breakpoint={DOING} }
                # Charging mid-clean; breakpoint flag means it will resume after charge completes.
                "CAoAEAMaAFoA": "recharging",
                # WorkStatus { state=CHARGING(3), charging={DONE} }
                # Charging complete (clean was fully finished before docking).
                "BhADGgIIAQ==": "completed",

                # WorkStatus { } — empty, all fields default (STANDBY=0)
                "AA==": "Standby",                 # capitalized in vacuum.py
                # WorkStatus { state=SLEEP(1) }
                "AhAB": "Sleeping",                # capitalized in vacuum.py
            },
        },

        RobovacCommand.FAN_SPEED: {
            "code": 158,
            "values": {
                "quiet": "Quiet",
                "standard": "Standard",
                "turbo": "Turbo",
                "max": "Max",
            },
        },

        RobovacCommand.LOCATE: {
            "code": 160,
            "values": {
                "locate": "true",
            }
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        # TODO: Re-enable ERROR (DPS 177) with proper protobuf parsing.
        #       The base64 string lookup approach cannot work here because field_1 is
        #       a CLOCK_MONOTONIC nanosecond uptime timestamp that changes every packet.
        #
        #       Correct decode approach for ErrorCode (error_code.proto):
        #         1. Strip length prefix byte
        #         2. Decode protobuf:
        #            field_1 [uint64] last_time — nanoseconds since boot (CLOCK_MONOTONIC), ignore
        #            field_3 [repeated uint32] warn — active warning codes (varint list)
        #            field_10 [message] new_code — newly triggered codes since last report:
        #              field_1 [repeated uint32] error
        #              field_2 [repeated uint32] warn
        #         3. Look up each code against ErrorCodeList enum (error_code_list_t2265.proto):
        #            e.g. 2213=SIDE_BRUSH_STUCK, 7000=ROBOT_TRAPPED
        #         4. Return empty / "no_error" when field_3 is absent or empty
        #
        # RobovacCommand.ERROR: {
        #    "code": 177,
        # },
    }
