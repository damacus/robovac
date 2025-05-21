from typing import Any, List, Type, cast, Dict

from .tuyalocalapi import TuyaDevice
from .vacuums import ROBOVAC_MODELS
from .vacuums.base import RobovacCommand, RobovacModelDetails


class ModelNotSupportedException(Exception):
    """This model is not supported"""


class RoboVac(TuyaDevice):
    """Tuya RoboVac device."""
    model_details: Type[RobovacModelDetails]

    def __init__(self, model_code: str, *args: Any, **kwargs: Any):
        # Determine model_details first
        if model_code not in ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                f"Model {model_code} is not supported"
            )
        current_model_details = ROBOVAC_MODELS[model_code]

        super().__init__(current_model_details, *args, **kwargs)

        self.model_code = model_code
        self.model_details = current_model_details

    def getHomeAssistantFeatures(self) -> int:
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        return self.model_details.homeassistant_features

    def getRoboVacFeatures(self) -> int:
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        return self.model_details.robovac_features

    def getFanSpeeds(self) -> list[str]:
        """Get the supported fan speeds of the device.

        Returns:
            A list of strings representing the supported fan speeds of the device.
        """
        fan_speed_command = self.model_details.commands.get(RobovacCommand.FAN_SPEED)
        if isinstance(fan_speed_command, dict):
            values = fan_speed_command.get("values")
            if isinstance(values, list):
                return cast(List[str], values)
        return []

    def getSupportedCommands(self) -> list[str]:
        return list(self.model_details.commands.keys())

    def getDpsCodes(self) -> dict[str, str]:
        """Get the DPS codes for this model based on command codes.

        Maps command names to their corresponding DPS code names and returns
        a dictionary of DPS codes for status updates.

        Returns:
            A dictionary mapping DPS code names to their values.
        """
        # Map command names to DPS code names
        command_to_dps = {
            "STATUS": "STATE",
            "BATTERY": "BATTERY_LEVEL",
            "ERROR": "ERROR_CODE",
            "DO_NOT_DISTURB": "DO_NOT_DISTURB",
            "CLEANING_AREA": "CLEANING_AREA",
            "CLEANING_TIME": "CLEANING_TIME",
            "AUTO_RETURN": "AUTO_RETURN",
            "BOOST_IQ": "BOOST_IQ",
            "CONSUMABLES": "CONSUMABLES"
            # FAN_SPEED and MODE typically use the same code names
        }

        codes = {}
        # Extract codes from commands dictionary
        for key, value in self.model_details.commands.items():
            # Get the DPS name from the mapping, or use the command name if not in mapping
            dps_name = command_to_dps.get(key.name, key.name)

            # Extract code value based on whether it's a direct value or in a dictionary
            if isinstance(value, dict) and "code" in value:
                # If it has a code property, use that
                codes[dps_name] = str(value["code"])
            elif isinstance(value, dict):
                # Skip dictionaries without code property (like when only 'values' is present)
                continue
            else:
                # For direct values, use the value itself
                codes[dps_name] = str(value)

        return codes
