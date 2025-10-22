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


TROUBLESHOOTING_CONTEXT = {
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
