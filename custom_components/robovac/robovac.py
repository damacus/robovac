from typing import Any, List, Type, cast

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

    def getCommandCodes(self) -> dict[str, str]:
        command_codes = {}
        for key, value in self.model_details.commands.items():
            if isinstance(value, dict):
                command_codes[key.name] = str(value["code"])
            else:
                command_codes[key.name] = str(value)

        return command_codes
