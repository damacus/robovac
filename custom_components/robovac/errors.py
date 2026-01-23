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
