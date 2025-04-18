ERROR_MESSAGES = {
    "IP_ADDRESS": "IP Address not set",
    "CONNECTION_FAILED": "Connection to the vacuum failed",
    "UNSUPPORTED_MODEL": "This model is not supported",
    "no_error": "None",
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
    19: "Laser sesor stuck",
    20: "Laser sensor blocked",
    21: "Base blocked",
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


def getErrorMessage(code: str | int) -> str:
    """Get the error message for a given error code.

    Args:
        code: The error code to look up.

    Returns:
        The error message string or the original code if not found.
    """
    return ERROR_MESSAGES.get(code, str(code))
