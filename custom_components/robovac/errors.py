ERROR_MESSAGES = {
    "IP_ADDRESS": "IP Address not set - Please configure the vacuum's IP address in the integration settings",
    "CONNECTION_FAILED": "Connection to the vacuum failed - Check if the vacuum is online and the IP address is correct",
    "UNSUPPORTED_MODEL": "This model is not supported - Please check the documentation or create an issue on GitHub",
    "INITIALIZATION_FAILED": "Failed to initialize vacuum connection - Check network connectivity and vacuum status",
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
    19: "Laser sensor stuck",
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


def getErrorMessageWithContext(code: str | int, model_code: str = "") -> str:
    """Get an enhanced error message with additional context.

    Args:
        code: The error code to look up.
        model_code: The vacuum model code for additional context.

    Returns:
        Enhanced error message with troubleshooting context.
    """
    base_message = ERROR_MESSAGES.get(code, str(code))

    # Add model-specific context for common issues
    if code in [1, 2, 3, 4, 5, 6]:  # Physical obstruction errors
        context = " - Please check and clear any obstructions, then restart the vacuum"
    elif code in [8, "N_enough_pow"]:  # Battery issues
        context = " - Please place the vacuum on the charging dock"
    elif code in [12, 13, 20]:  # Sensor issues
        context = " - Please clean the sensors with a soft, dry cloth"
    elif code in [17, 9]:  # Navigation/boundary issues
        context = " - Check for magnetic strips or virtual boundaries"
    elif code == "UNSUPPORTED_MODEL" and model_code:
        context = f" - Model {model_code} needs to be added to the integration"
    else:
        context = ""

    return base_message + context
