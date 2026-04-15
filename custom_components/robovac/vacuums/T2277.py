"""eufy Clean L60 SES (T2277)"""
import logging
from homeassistant.components.vacuum import VacuumEntityFeature
from .base import RoboVacEntityFeature, RobovacCommand, RobovacModelDetails

_LOGGER = logging.getLogger(__name__)


class T2277(RobovacModelDetails):
    homeassistant_features = (
        VacuumEntityFeature.CLEAN_SPOT
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
            # DPS 152 — ModeCtrlRequest (control.proto)
            # field_1 [varint]  method: 6=START_GOHOME, 12=STOP_TASK, 13=PAUSE_TASK,
            #                          14=RESUME_TASK, 0=START_AUTO_CLEAN (needs field_3)
            # field_2 [varint]  seq:    request sequence number (ignored in decoding)
            # field_3 [message] param:  AutoClean { clean_times=1 } for START_AUTO_CLEAN
            # Decoded by decode_dps() via proto_decode.decode_mode_ctrl().
            "code": 152,
            "values": {
                "standby": "AA==",      # empty payload
                "pause": "AggN",      # method=PAUSE_TASK (13)
                "stop": "AggG",      # method=START_GOHOME (6)
                "return": "AggG",      # method=START_GOHOME (6)
                "auto": "BBoCCAE=",  # param.auto_clean={clean_times=1}
                "nosweep": "AggO",      # method=RESUME_TASK (14)
            },
        },
        RobovacCommand.START_PAUSE: {
            "code": 152,
            "values": {
            	"start": "AggO",			# method=RESUME_TASK (14)
                "pause": "AggN",         # method=PAUSE_TASK (13)
            },
        },
        RobovacCommand.RETURN_HOME: {
            "code": 152,
            "values": {
                "return": "AggG",        # method=START_GOHOME (6)
            },
        },
        RobovacCommand.STATUS: {
            # DPS 153 — WorkStatus (work_status.proto)
            # field_1  [message] Mode      { value: 0=AUTO, 1=SELECT_ROOM, 2=SELECT_ZONE, 3=SPOT }
            # field_2  [varint]  State:    0=STANDBY, 1=SLEEP, 2=FAULT, 3=CHARGING,
            #                             4=FAST_MAPPING, 5=CLEANING, 6=REMOTE_CTRL,
            #                             7=GO_HOME, 8=CRUISING
            # field_3  [message] Charging  { 0=DOING, 1=DONE, 2=ABNORMAL }
            # field_6  [message] Cleaning  { RunState: 0=DOING, 1=PAUSED }
            # field_8  [message] GoHome    { RunState: 0=DOING, 1=PAUSED }
            # field_10 [message] Relocating — robot relocalizing on map
            # field_11 [message] Breakpoint — will resume after charge
            # Decoded by decode_dps() via proto_decode.decode_work_status().
            "code": 153,
        },
        RobovacCommand.CLEAN_PARAM: {
            # DPS 154 — CleanParamResponse (clean_param.proto)
            # field_1 CleanParam  clean_param         — global default params
            # field_3 CleanParam  area_clean_param    — area-specific params
            # field_4 CleanParam  running_clean_param — currently active params
            # CleanParam: fan (0=QUIET…4=MAX_PLUS), clean_type (0=SWEEP_ONLY…),
            #             clean_extent (0=NORMAL, 1=NARROW), mop_level (0=LOW…2=HIGH)
            # Decoded by decode_dps() via proto_decode.decode_clean_param_response().
            "code": 154,
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
            },
        },
        RobovacCommand.BATTERY: {
            "code": 163,
        },
        RobovacCommand.CLEAN_RECORDS: {
            # DPS 164 — CleanRecordList (repeated outer field_4 entries)
            # Each entry: timestamp (Unix seconds) + status code.
            # Decoded by decode_dps() via proto_decode.decode_clean_record_list().
            "code": 164,
        },
        RobovacCommand.ANALYSIS_STATS: {
            # DPS 167 — AnalysisStatistics subset (analysis.proto)
            # Raw integer counters per field for clean / gohome / relocate sub-sessions.
            # Decoded by decode_dps() via proto_decode.decode_analysis_stats().
            "code": 167,
        },
        RobovacCommand.CONSUMABLES: {
            # DPS 168 — ConsumableResponse (consumable.proto)
            # ConsumableRuntime hours: side_brush, rolling_brush, filter_mesh,
            #   scrape, sensor, mop, dustbag, dirty_watertank, dirty_waterfilter.
            # Decoded by decode_dps() via proto_decode.decode_consumable_response().
            "code": 168,
        },
        RobovacCommand.DEVICE_INFO: {
            # DPS 169 — DeviceInfo (app_device_info.proto)
            # Fields: product_name, device_mac, software (firmware), hardware, wifi_name.
            # Decoded by decode_dps() via proto_decode.decode_device_info().
            "code": 169,
        },
        RobovacCommand.WORK_STATUS_V2: {
            # DPS 173 — outer-wrapped WorkStatus used by station-aware firmware variants
            # Outer field_1 = WorkStatus; may omit explicit State/Mode when sub-state
            # messages (Cleaning, GoHome, GoWash) can be used to infer overall state.
            # Decoded by decode_dps() via proto_decode.decode_work_status_v2().
            "code": 173,
        },
        RobovacCommand.UNISETTING: {
            # DPS 176 — UnisettingResponse (unisetting.proto)
            # Fields: wifi_ssid, wifi_signal_pct (0–100), multi_map, custom_clean_mode,
            #         map_valid, children_lock.
            # Decoded by decode_dps() via proto_decode.decode_unisetting_response().
            "code": 176,
        },
        RobovacCommand.ERROR: {
            # DPS 177 — ErrorCode (error_code.proto)
            # field_3  [repeated uint32] warn    — active warning codes
            # field_10 [message]         new_code — newly triggered error/warn codes
            # Codes mapped via T2277_ERROR_CODES in proto_decode.py.
            # Decoded by decode_dps() via proto_decode.decode_error_code().
            "code": 177,
        },
        RobovacCommand.ACTIVE_ERRORS: {
            # DPS 178 — ErrorCode (error_code.proto) with packed field_2 error codes
            # field_2  [packed uint32]   error   — active system error codes
            # Codes mapped via T2277_ERROR_CODES in proto_decode.py.
            # Decoded by decode_dps() via proto_decode.decode_error_code().
            "code": 178,
        },
        RobovacCommand.LAST_CLEAN: {
            # DPS 179 — AnalysisResponse (analysis.proto)
            # Statistics for the most recently completed clean session:
            #   clean_id, success, mode, clean_time_s, clean_area_m2, room_count.
            # Decoded by decode_dps() via proto_decode.decode_analysis_response().
            "code": 179,
        },
    }

    @classmethod
    def decode_dps(cls, dps_code: int, raw_b64: str) -> str | None:
        """Decode a T2277 DPS value using protobuf. Returns None to fall back to lookup table."""
        from custom_components.robovac.proto_decode import (
            decode_mode_ctrl,
            decode_work_status,
            decode_work_status_v2,
            decode_error_code,
            decode_clean_param_response,
            decode_consumable_response,
            decode_device_info,
            decode_unisetting_response,
            decode_analysis_response,
            decode_clean_record_list,
            decode_analysis_stats,
        )

        try:
            if dps_code == 152:
                return decode_mode_ctrl(raw_b64)
            if dps_code == 153:
                return decode_work_status(raw_b64)
            if dps_code == 154:
                d = decode_clean_param_response(raw_b64)
                rcp = d.get("running_clean_param") or d.get("clean_param") or {}
                return rcp.get("fan") or str(d) if d else None
            if dps_code == 164:
                records = decode_clean_record_list(raw_b64)
                return f"{len(records)} record(s)" if records else None
            if dps_code == 167:
                d = decode_analysis_stats(raw_b64)
                return str(d) if d else None
            if dps_code == 168:
                hours = decode_consumable_response(raw_b64)
                if not hours:
                    return None
                return " | ".join(f"{k}: {v}h" for k, v in hours.items())
            if dps_code == 169:
                d = decode_device_info(raw_b64)
                return str(d) if d else None
            if dps_code == 173:
                return decode_work_status_v2(raw_b64)
            if dps_code == 176:
                d = decode_unisetting_response(raw_b64)
                return str(d) if d else None
            if dps_code == 177:
                return decode_error_code(raw_b64)
            if dps_code == 178:
                return decode_error_code(raw_b64)
            if dps_code == 179:
                d = decode_analysis_response(raw_b64)
                return str(d) if d else None
        except Exception as exc:
            _LOGGER.warning("proto_decode failed for DPS %d value %r: %s", dps_code, raw_b64, exc)
        return None
