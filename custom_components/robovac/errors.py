ERROR_MESSAGES = {
    "IP_ADDRESS": "IP Address not set",
    "CONNECTION_FAILED": "Connection to the vacuum failed",
    "UNSUPPORTED_MODEL": "This model is not supported",
    "no_error": "None",
    # Legacy error codes (T20xx and older models)
    1: "Front bumper stuck",
    2: "Wheel stuck",
    3: "Side brush",
    4: "Rolling brush bar stuck",
    5: "Device trapped",
    6: "Device trapped",
    7: "Wheel suspended",
    8: "Low battery",
    9: "Magnetic boundary",
    12: "Right wall sensor",
    13: "Device tilted",
    14: "Insert dust collector",
    17: "Restricted area detected",
    18: "Laser cover stuck",
    19: "Laser sensor stuck",
    20: "Laser sensor blocked",
    21: "Base blocked",
    # T2320 (X9 Pro) specific error codes (from proto-reference/error_code_list_t2320.proto)
    # These codes are used by vacuums with auto-clean stations
    26: "Low battery - scheduled start failed",
    31: "Foreign objects stuck in suction port",
    32: "Mop holder rotating motor stuck - clear tangled objects from mop",
    33: "Mop bracket lift motor stuck - clear foreign objects from lifting bracket",
    39: "Positioning failed - cleaning ended, check if map matches environment",
    40: "Mop cloth dislodged",
    41: "Air drying device heater abnormal",
    50: "Machine accidentally on carpet",
    51: "Camera blocked",
    52: "Unable to leave station - check surroundings",
    55: "Station exploration failed",
    70: "Please clean dust collector and filter",
    71: "Wall sensor abnormal",
    72: "Robot water tank insufficient",
    73: "Station dirty water tank full",
    74: "Station clean water tank insufficient",
    75: "Station water tank missing",
    76: "Camera abnormal",
    77: "3D TOF sensor abnormal",
    78: "Ultrasonic sensor abnormal",
    79: "Station clean tray not installed",
    80: "Robot and station communication abnormal",
    81: "Dirty water tank leaking",
    82: "Please clean station wash tray",
    83: "Poor charging contact",
    101: "Battery abnormal",
    102: "Wheel module abnormal",
    103: "Side brush module abnormal",
    104: "Fan abnormal",
    105: "Roller brush motor abnormal",
    106: "Water pump abnormal",
    107: "Laser sensor abnormal",
    111: "Rotation motor abnormal",
    112: "Lift motor abnormal",
    113: "Water spraying device abnormal",
    114: "Water pumping device abnormal",
    117: "Ultrasonic sensor abnormal",
    119: "WiFi or Bluetooth abnormal",
    # T2320 (X9 Pro) prompt codes (informational messages from error_code_list_t2320.proto)
    # These are sent on the ERROR DPS but are status messages, not errors
    "P001": "Starting scheduled cleaning",
    "P003": "Battery low - returning to base station",
    "P004": "Positioning failed - rebuilding map, starting new cleaning",
    "P005": "Positioning failed - returning to base station",
    "P006": "Some areas unreachable - not cleaned",
    "P007": "Path planning failed - cannot reach designated area",
    "P009": "Base station exploration failed - returned to starting point",
    "P010": "Positioning successful",
    "P011": "Task finished - returning to base station",
    "P012": "Cannot start task while on station",
    "P013": "Scheduled cleaning failed - task in progress",
    "P014": "Map data updating - please try again later",
    "P015": "Mop washing complete - resuming cleaning",
    "P016": "Low battery - please charge and try again",
    "P017": "Mop cleaning completed",
    # T22xx series error codes (from proto-reference/error_code_list_t2265.proto)
    # Wheel errors (1xxx)
    1010: "Left wheel open circuit",
    1011: "Left wheel short circuit",
    1012: "Left wheel error",
    1013: "Left wheel stuck",
    1020: "Right wheel open circuit",
    1021: "Right wheel short circuit",
    1022: "Right wheel error",
    1023: "Right wheel stuck",
    1030: "Both wheels open circuit",
    1031: "Both wheels short circuit",
    1032: "Both wheels error",
    1033: "Both wheels stuck",
    # Fan and brush errors (2xxx)
    2010: "Suction fan open circuit",
    2013: "Suction fan RPM error",
    2110: "Roller brush open circuit",
    2111: "Roller brush short circuit",
    2112: "Roller brush stuck",
    2210: "Side brush open circuit",
    2211: "Side brush short circuit",
    2212: "Side brush error",
    2213: "Side brush stuck",
    2310: "Dustbin and filter not installed",
    2311: "Dustbin not cleaned for too long",
    # Water system errors (3xxx)
    3010: "Water pump open circuit",
    3013: "Water tank insufficient",
    # Sensor errors (4xxx)
    4010: "Laser sensor error",
    4011: "Laser sensor blocked",
    4012: "Laser sensor stuck or entangled",
    4111: "Left bumper stuck",
    4112: "Right bumper stuck",
    4130: "Laser cover stuck",
    # Power and communication errors (5xxx)
    5014: "Low battery shutdown",
    5015: "Low battery - cannot schedule cleaning",
    5110: "WiFi or Bluetooth error",
    5112: "Station communication error",
    # Station errors (6xxx)
    6113: "Dust bag not installed",
    6310: "Hair cutting interrupted",
    6311: "Hair cutting component stuck",
    # Navigation and positioning errors (7xxx)
    7000: "Robot trapped",
    7001: "Robot partly suspended",
    7002: "Robot fully suspended (picked up)",
    7003: "Robot suspended during startup self-check",
    7010: "Entered no-go zone",
    7020: "Positioning failed - starting new cleaning",
    7021: "Positioning failed - returning to station",
    7031: "Docking failed",
    7032: "Station exploration failed - returning to start point",
    7033: "Return to station failed - stopped working",
    7034: "Cannot find start point - stopped working",
    7040: "Undocking failed",
    7050: "Some areas inaccessible - not cleaned",
    7051: "Scheduled cleaning failed - task in progress",
    7052: "Route planning failed - cannot reach designated area",
    # String-based error codes
    "S1": "Battery",
    "S2": "Wheel Module",
    "S3": "Side Brush",
    "S4": "Suction Fan",
    "S5": "Rolling Brush",
    "S8": "Path Tracking Sensor",
    "Wheel_stuck": "Wheel stuck",
    "R_brush_stuck": "Rolling brush stuck",
    "Crash_bar_stuck": "Front bumper stuck",
    "sensor_dirty": "Sensor dirty",
    "N_enough_pow": "Low battery",
    "Stuck_5_min": "Device trapped",
    "Fan_stuck": "Fan stuck",
    "S_brush_stuck": "Side brush stuck",
}


TROUBLESHOOTING_CONTEXT = {
    # Legacy error codes
    1: {
        "troubleshooting": [
            "Check front bumper for obstructions",
            "Clean bumper sensors",
            "Ensure bumper moves freely",
        ],
        "common_causes": [
            "Hair or debris blocking bumper",
            "Damaged bumper spring",
            "Sensor misalignment",
        ],
    },
    2: {
        "troubleshooting": [
            "Check wheels for obstructions",
            "Clean wheel sensors",
            "Ensure wheels rotate freely",
        ],
        "common_causes": [
            "Hair wrapped around wheel",
            "Debris in wheel mechanism",
            "Damaged wheel motor",
        ],
    },
    8: {
        "troubleshooting": [
            "Charge the vacuum fully",
            "Check charging contacts for dirt",
            "Ensure dock is properly positioned",
        ],
        "common_causes": [
            "Battery depleted",
            "Poor charging connection",
            "Faulty charging dock",
        ],
    },
    19: {
        "troubleshooting": [
            "Remove any stickers or tape from laser sensor",
            "Clean laser sensor cover",
            "Check for physical damage to sensor",
            "Restart vacuum",
        ],
        "common_causes": [
            "Protective film not removed",
            "Dust or debris on sensor",
            "Physical damage to sensor cover",
        ],
    },
    # T22xx series error codes
    1013: {
        "troubleshooting": [
            "Check left wheel for hair or debris",
            "Ensure wheel rotates freely",
            "Clean wheel axle area",
            "Restart vacuum",
        ],
        "common_causes": [
            "Hair wrapped around wheel",
            "Debris blocking wheel movement",
            "Wheel motor issue",
        ],
    },
    1023: {
        "troubleshooting": [
            "Check right wheel for hair or debris",
            "Ensure wheel rotates freely",
            "Clean wheel axle area",
            "Restart vacuum",
        ],
        "common_causes": [
            "Hair wrapped around wheel",
            "Debris blocking wheel movement",
            "Wheel motor issue",
        ],
    },
    1033: {
        "troubleshooting": [
            "Check both wheels for hair or debris",
            "Ensure both wheels rotate freely",
            "Clean wheel axle areas",
            "Move vacuum to a flat surface",
        ],
        "common_causes": [
            "Hair wrapped around wheels",
            "Vacuum stuck on obstacle",
            "Both wheel motors affected",
        ],
    },
    2112: {
        "troubleshooting": [
            "Remove and clean the roller brush",
            "Check for hair or string wrapped around brush",
            "Inspect brush bearings",
            "Reinstall brush securely",
        ],
        "common_causes": [
            "Hair tangled in roller brush",
            "Debris blocking brush rotation",
            "Worn brush bearings",
        ],
    },
    2213: {
        "troubleshooting": [
            "Remove and clean the side brush",
            "Check for hair wrapped around brush stem",
            "Ensure brush is properly attached",
        ],
        "common_causes": [
            "Hair or debris on side brush",
            "Damaged side brush motor",
            "Side brush not properly seated",
        ],
    },
    2310: {
        "troubleshooting": [
            "Ensure dustbin is properly installed",
            "Check that filter is in place",
            "Clean dustbin sensors",
            "Reinstall dustbin securely",
        ],
        "common_causes": [
            "Dustbin not fully inserted",
            "Filter missing or misaligned",
            "Dirty dustbin sensors",
        ],
    },
    4011: {
        "troubleshooting": [
            "Clean the laser sensor cover",
            "Remove any obstructions above laser turret",
            "Check for dust or debris on sensor",
            "Wipe with soft, dry cloth",
        ],
        "common_causes": [
            "Dust on laser sensor",
            "Object blocking laser view",
            "Dirty sensor cover",
        ],
    },
    4012: {
        "troubleshooting": [
            "Check laser turret can rotate freely",
            "Remove any hair or debris from turret base",
            "Ensure nothing is tangled around sensor",
            "Restart vacuum",
        ],
        "common_causes": [
            "Hair wrapped around laser turret",
            "Debris blocking turret rotation",
            "Mechanical obstruction",
        ],
    },
    4130: {
        "troubleshooting": [
            "Check laser cover for obstructions",
            "Ensure cover moves freely",
            "Clean around laser cover area",
        ],
        "common_causes": [
            "Debris blocking laser cover",
            "Cover mechanism jammed",
            "Physical damage to cover",
        ],
    },
    5014: {
        "troubleshooting": [
            "Place vacuum on charging dock",
            "Charge fully before next use",
            "Check charging contacts are clean",
        ],
        "common_causes": [
            "Battery depleted during cleaning",
            "Long cleaning session",
            "Battery not holding charge",
        ],
    },
    7000: {
        "troubleshooting": [
            "Move vacuum to open area",
            "Remove obstacles around vacuum",
            "Check for narrow spaces vacuum cannot exit",
            "Restart cleaning cycle",
        ],
        "common_causes": [
            "Vacuum stuck under furniture",
            "Too many obstacles in area",
            "Vacuum wedged in tight space",
        ],
    },
    7002: {
        "troubleshooting": [
            "Place vacuum on floor",
            "Ensure all wheels touch ground",
            "Start cleaning from flat surface",
        ],
        "common_causes": [
            "Vacuum lifted during operation",
            "Vacuum balanced on obstacle edge",
            "Cliff sensors triggered incorrectly",
        ],
    },
    7010: {
        "troubleshooting": [
            "Move vacuum outside no-go zone",
            "Check no-go zone boundaries in app",
            "Adjust no-go zone if needed",
        ],
        "common_causes": [
            "Vacuum drifted into restricted area",
            "No-go zone boundaries too close to path",
            "Mapping inaccuracy",
        ],
    },
    7031: {
        "troubleshooting": [
            "Clear area around charging dock",
            "Ensure dock is against wall",
            "Clean charging contacts on vacuum and dock",
            "Check dock has power",
        ],
        "common_causes": [
            "Obstacles blocking dock access",
            "Dirty charging contacts",
            "Dock moved from mapped location",
        ],
    },
    # T2320 (X9 Pro) specific error codes
    32: {
        "troubleshooting": [
            "Remove mop pads and check for tangled hair or debris",
            "Clean the mop holder rotating mechanism",
            "Ensure mop pads are properly attached",
            "Restart vacuum",
        ],
        "common_causes": [
            "Hair or string wrapped around mop holder",
            "Debris blocking rotation",
            "Mop pads incorrectly installed",
        ],
    },
    33: {
        "troubleshooting": [
            "Check mop lifting bracket for foreign objects",
            "Clean around lift motor area",
            "Ensure nothing is blocking the lift mechanism",
            "Restart vacuum",
        ],
        "common_causes": [
            "Debris in lifting mechanism",
            "Foreign objects blocking lift",
            "Mechanical obstruction",
        ],
    },
    40: {
        "troubleshooting": [
            "Reattach mop cloth securely",
            "Check mop holder clips are engaged",
            "Inspect mop cloth for damage",
            "Replace mop cloth if worn",
        ],
        "common_causes": [
            "Mop cloth not properly attached",
            "Worn mop cloth velcro",
            "Mop holder clips damaged",
        ],
    },
    52: {
        "troubleshooting": [
            "Clear area around station",
            "Check for obstacles blocking exit path",
            "Ensure station is on flat surface",
            "Clean station sensors",
        ],
        "common_causes": [
            "Obstacles blocking station exit",
            "Station misaligned",
            "Dirty sensors",
        ],
    },
    73: {
        "troubleshooting": [
            "Empty the dirty water tank",
            "Clean dirty water tank",
            "Ensure tank is properly seated",
            "Check tank sensors are clean",
        ],
        "common_causes": [
            "Dirty water tank full",
            "Tank sensor dirty",
            "Tank not properly inserted",
        ],
    },
    74: {
        "troubleshooting": [
            "Refill station clean water tank",
            "Check tank is properly seated",
            "Ensure water inlet is not blocked",
        ],
        "common_causes": [
            "Clean water tank empty",
            "Tank not properly inserted",
            "Water inlet blocked",
        ],
    },
    75: {
        "troubleshooting": [
            "Install clean water tank in station",
            "Install dirty water tank in station",
            "Ensure both tanks are properly seated",
        ],
        "common_causes": [
            "Water tank removed for cleaning",
            "Tank not properly inserted",
            "Tank detection sensor dirty",
        ],
    },
    79: {
        "troubleshooting": [
            "Install wash tray in station",
            "Ensure tray is properly seated",
            "Clean tray sensors",
        ],
        "common_causes": [
            "Wash tray removed for cleaning",
            "Tray not properly inserted",
            "Tray sensor dirty",
        ],
    },
    80: {
        "troubleshooting": [
            "Ensure vacuum is properly docked",
            "Clean charging contacts",
            "Restart both vacuum and station",
            "Check station power connection",
        ],
        "common_causes": [
            "Poor contact between vacuum and station",
            "Dirty charging contacts",
            "Station power issue",
        ],
    },
    82: {
        "troubleshooting": [
            "Remove and clean station wash tray",
            "Rinse tray thoroughly",
            "Check for debris buildup",
            "Reinstall tray",
        ],
        "common_causes": [
            "Accumulated dirt on wash tray",
            "Mop debris buildup",
            "Regular maintenance needed",
        ],
    },
    83: {
        "troubleshooting": [
            "Clean charging contacts on vacuum",
            "Clean charging pins on station",
            "Ensure vacuum is properly aligned on dock",
            "Check for debris on dock",
        ],
        "common_causes": [
            "Dirty charging contacts",
            "Vacuum misaligned on dock",
            "Debris on charging area",
        ],
    },
    # Additional T2320 (X9 Pro) troubleshooting contexts
    26: {
        "troubleshooting": [
            "Charge vacuum before scheduled cleaning time",
            "Adjust schedule to allow more charging time",
            "Check if battery is holding charge properly",
        ],
        "common_causes": [
            "Vacuum not docked before scheduled time",
            "Battery not fully charged",
            "Short charging window before schedule",
        ],
    },
    31: {
        "troubleshooting": [
            "Check suction port for debris",
            "Remove any stuck objects from suction area",
            "Clean around the suction inlet",
            "Restart vacuum",
        ],
        "common_causes": [
            "Large debris blocking suction",
            "Foreign object stuck in inlet",
            "Hair or string wrapped around inlet",
        ],
    },
    39: {
        "troubleshooting": [
            "Verify map matches current room layout",
            "Delete and rebuild map if furniture moved",
            "Ensure good lighting for camera-based positioning",
            "Clean sensors and camera lens",
        ],
        "common_causes": [
            "Room layout changed since mapping",
            "Furniture moved significantly",
            "Poor lighting conditions",
            "Dirty camera or sensors",
        ],
    },
    41: {
        "troubleshooting": [
            "Check air drying unit for blockages",
            "Ensure station has proper ventilation",
            "Contact support if error persists",
        ],
        "common_causes": [
            "Heater malfunction",
            "Blocked ventilation",
            "Hardware fault",
        ],
    },
    50: {
        "troubleshooting": [
            "Move vacuum off carpet manually",
            "Update carpet avoidance settings in app",
            "Check if mop is attached (should avoid carpet when mopping)",
        ],
        "common_causes": [
            "Vacuum drifted onto carpet while mopping",
            "Carpet detection settings incorrect",
            "Mop attached with carpet in cleaning area",
        ],
    },
    51: {
        "troubleshooting": [
            "Clean camera lens with soft dry cloth",
            "Remove any obstructions above camera",
            "Check for protective film on camera",
        ],
        "common_causes": [
            "Dirty camera lens",
            "Object blocking camera view",
            "Protective film not removed",
        ],
    },
    55: {
        "troubleshooting": [
            "Clear area around station",
            "Ensure station is properly positioned against wall",
            "Restart vacuum and station",
            "Try manual docking first",
        ],
        "common_causes": [
            "Obstacles near station",
            "Station moved from mapped location",
            "Poor lighting for navigation",
        ],
    },
    70: {
        "troubleshooting": [
            "Remove and empty dust collector",
            "Clean or replace filter",
            "Check filter is properly installed",
        ],
        "common_causes": [
            "Dust collector full",
            "Filter clogged with dust",
            "Regular maintenance needed",
        ],
    },
    71: {
        "troubleshooting": [
            "Clean wall sensor on side of vacuum",
            "Check for debris blocking sensor",
            "Restart vacuum",
        ],
        "common_causes": [
            "Dirty wall sensor",
            "Debris blocking sensor",
            "Sensor malfunction",
        ],
    },
    72: {
        "troubleshooting": [
            "Refill robot's onboard water tank",
            "Check water tank is properly seated",
            "Ensure water inlet is not blocked",
        ],
        "common_causes": [
            "Water tank empty",
            "Tank not properly inserted",
            "Water consumption higher than expected",
        ],
    },
    76: {
        "troubleshooting": [
            "Clean camera lens",
            "Restart vacuum",
            "Contact support if error persists",
        ],
        "common_causes": [
            "Camera hardware issue",
            "Software glitch",
            "Camera damaged",
        ],
    },
    77: {
        "troubleshooting": [
            "Clean 3D TOF sensor area",
            "Restart vacuum",
            "Contact support if error persists",
        ],
        "common_causes": [
            "Sensor obstruction",
            "Hardware malfunction",
            "Sensor damaged",
        ],
    },
    78: {
        "troubleshooting": [
            "Clean ultrasonic sensors",
            "Check for damage to sensor covers",
            "Restart vacuum",
        ],
        "common_causes": [
            "Dirty ultrasonic sensors",
            "Sensor obstruction",
            "Hardware malfunction",
        ],
    },
    81: {
        "troubleshooting": [
            "Check dirty water tank seal",
            "Ensure tank is properly seated",
            "Inspect tank for cracks or damage",
            "Replace tank if damaged",
        ],
        "common_causes": [
            "Tank seal damaged",
            "Tank not properly seated",
            "Cracked tank",
        ],
    },
    101: {
        "troubleshooting": [
            "Restart vacuum",
            "Let battery fully discharge then recharge",
            "Contact support if error persists",
        ],
        "common_causes": [
            "Battery communication error",
            "Battery degradation",
            "Temperature extreme",
        ],
    },
    102: {
        "troubleshooting": [
            "Check wheels for obstructions",
            "Clean wheel axles",
            "Restart vacuum",
        ],
        "common_causes": [
            "Wheel motor issue",
            "Debris in wheel mechanism",
            "Wheel sensor malfunction",
        ],
    },
    103: {
        "troubleshooting": [
            "Remove and clean side brush",
            "Check side brush motor area for debris",
            "Replace side brush if worn",
        ],
        "common_causes": [
            "Side brush motor issue",
            "Debris blocking brush",
            "Worn side brush",
        ],
    },
    104: {
        "troubleshooting": [
            "Clean dust collector and filter",
            "Check for blockages in airway",
            "Restart vacuum",
        ],
        "common_causes": [
            "Clogged filter restricting airflow",
            "Fan motor issue",
            "Debris in fan housing",
        ],
    },
    105: {
        "troubleshooting": [
            "Remove and clean roller brush",
            "Check brush bearings",
            "Remove hair and debris from brush area",
        ],
        "common_causes": [
            "Roller brush motor strain",
            "Excessive debris buildup",
            "Worn brush bearings",
        ],
    },
    106: {
        "troubleshooting": [
            "Check water tank is properly seated",
            "Ensure water lines are not kinked",
            "Restart vacuum",
        ],
        "common_causes": [
            "Water pump malfunction",
            "Air in water lines",
            "Blocked water pathway",
        ],
    },
    107: {
        "troubleshooting": [
            "Clean laser sensor cover",
            "Check laser turret rotates freely",
            "Remove any obstructions from turret",
        ],
        "common_causes": [
            "Laser sensor malfunction",
            "Turret motor issue",
            "Sensor damage",
        ],
    },
    111: {
        "troubleshooting": [
            "Check mop pad attachment area",
            "Remove debris from rotation mechanism",
            "Restart vacuum",
        ],
        "common_causes": [
            "Rotation motor malfunction",
            "Debris blocking rotation",
            "Motor strain from obstruction",
        ],
    },
    112: {
        "troubleshooting": [
            "Check mop lifting mechanism for obstructions",
            "Remove debris from lift area",
            "Restart vacuum",
        ],
        "common_causes": [
            "Lift motor malfunction",
            "Debris blocking lift mechanism",
            "Motor strain",
        ],
    },
    113: {
        "troubleshooting": [
            "Check water spray nozzles for blockages",
            "Ensure water tank has water",
            "Restart vacuum",
        ],
        "common_causes": [
            "Spray nozzle clogged",
            "Water pump issue",
            "Empty water tank",
        ],
    },
    114: {
        "troubleshooting": [
            "Check water pumping mechanism",
            "Ensure water tank is properly seated",
            "Restart vacuum",
        ],
        "common_causes": [
            "Pump malfunction",
            "Blocked water lines",
            "Air in system",
        ],
    },
    117: {
        "troubleshooting": [
            "Clean ultrasonic sensors",
            "Check for debris or damage",
            "Restart vacuum",
        ],
        "common_causes": [
            "Sensor obstruction",
            "Sensor damage",
            "Hardware malfunction",
        ],
    },
    119: {
        "troubleshooting": [
            "Restart vacuum",
            "Check WiFi signal strength",
            "Re-pair vacuum with app if needed",
            "Restart router",
        ],
        "common_causes": [
            "WiFi connectivity issue",
            "Bluetooth interference",
            "Communication module fault",
        ],
    },
}


def getErrorMessage(code: str | int) -> str:
    """Get the error message for a given error code.

    Args:
        code: The error code to look up.

    Returns:
        The error message string or the original code if not found.
    """
    return ERROR_MESSAGES.get(code, str(code))


def getErrorMessageWithContext(
    code: str | int, model_code: str | None = None
) -> dict[str, str | list[str]]:
    """Get error message with troubleshooting context.

    Provides users with actionable troubleshooting steps and common causes
    for error codes. Optionally includes model-specific guidance.

    Args:
        code: The error code to look up.
        model_code: Optional model code for model-specific guidance.

    Returns:
        Dictionary containing:
        - message: The error message
        - troubleshooting: List of troubleshooting steps (if available)
        - common_causes: List of common causes (if available)
    """
    message = getErrorMessage(code)
    context: dict[str, str | list[str]] = {"message": message}

    # Add troubleshooting context if available (only for integer codes)
    if isinstance(code, int) and code in TROUBLESHOOTING_CONTEXT:
        context_data = TROUBLESHOOTING_CONTEXT[code]
        if "troubleshooting" in context_data:
            context["troubleshooting"] = context_data["troubleshooting"]
        if "common_causes" in context_data:
            context["common_causes"] = context_data["common_causes"]

    return context
