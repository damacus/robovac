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
        super().__init__(*args, **kwargs)
        self.model_code = model_code

        if self.model_code not in ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                f"Model {self.model_code} is not supported"
            )
        self.model_details = ROBOVAC_MODELS[self.model_code]

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

    def getRoboVacSeries(self) -> str | None:
        """Get the series of the device.

        Returns:
            A string representing the series of the device.
        """
        return self.model_code

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
