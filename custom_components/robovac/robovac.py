from enum import IntEnum
from homeassistant.components.vacuum import VacuumEntityFeature
from .tuyalocalapi import TuyaDevice
from typing import Any, Dict, Optional


class RoboVacEntityFeature(IntEnum):
    """Supported features of the RoboVac entity."""

    EDGE = 1
    SMALL_ROOM = 2
    CLEANING_TIME = 4
    CLEANING_AREA = 8
    DO_NOT_DISTURB = 16
    AUTO_RETURN = 32
    CONSUMABLES = 64
    ROOM = 128
    ZONE = 256
    MAP = 512
    BOOST_IQ = 1024


ROBOVAC_SERIES = {
    "C": [
        "T2103",
        "T2117",
        "T2118",
        "T2119",
        "T2120",
        "T2123",
        "T2128",
        "T2130",
        "T2132",
    ],
    "G": [
        "T1250",
        "T2250",
        "T2251",
        "T2252",
        "T2253",
        "T2254",
        "T2150",
        "T2255",
        "T2256",
        "T2257",
        "T2258",
        "T2259",
        "T2270",
        "T2272",
        "T2273",
    ],
    "L": ["T2181", "T2182", "T2190", "T2192", "T2193", "T2194"],
    "X": ["T2261", "T2262", "T2320"],
}

HAS_MAP_FEATURE = ["T2253", *ROBOVAC_SERIES["L"], *ROBOVAC_SERIES["X"]]

HAS_CONSUMABLES = [
    "T1250",
    "T2181",
    "T2182",
    "T2190",
    "T2193",
    "T2194",
    "T2253",
    "T2256",
    "T2258",
    "T2261",
    "T2273",
    "T2320",
]

ROBOVAC_SERIES_FEATURES: Dict[str, int] = {
    "C": RoboVacEntityFeature.EDGE
    | RoboVacEntityFeature.SMALL_ROOM,
    "G": RoboVacEntityFeature.CLEANING_TIME
    | RoboVacEntityFeature.CLEANING_AREA
    | RoboVacEntityFeature.DO_NOT_DISTURB
    | RoboVacEntityFeature.AUTO_RETURN,
    "L": RoboVacEntityFeature.CLEANING_TIME
    | RoboVacEntityFeature.CLEANING_AREA
    | RoboVacEntityFeature.DO_NOT_DISTURB
    | RoboVacEntityFeature.AUTO_RETURN
    | RoboVacEntityFeature.ROOM
    | RoboVacEntityFeature.ZONE
    | RoboVacEntityFeature.BOOST_IQ,
    "X": RoboVacEntityFeature.CLEANING_TIME
    | RoboVacEntityFeature.CLEANING_AREA
    | RoboVacEntityFeature.DO_NOT_DISTURB
    | RoboVacEntityFeature.AUTO_RETURN
    | RoboVacEntityFeature.ROOM
    | RoboVacEntityFeature.ZONE
    | RoboVacEntityFeature.BOOST_IQ,
}

ROBOVAC_SERIES_FAN_SPEEDS = {
    "C": ["No Suction", "Standard", "Boost IQ", "Max"],
    "G": ["Standard", "Turbo", "Max", "Boost IQ"],
    "L": ["Quiet", "Standard", "Turbo", "Max"],
    "X": ["Pure", "Standard", "Turbo", "Max"],
}


SUPPORTED_ROBOVAC_MODELS = list(
    set([item for sublist in ROBOVAC_SERIES.values() for item in sublist])
)


class ModelNotSupportedException(Exception):
    """This model is not supported"""


class RoboVac(TuyaDevice):
    """Tuya RoboVac device."""

    def __init__(self, model_code: str, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.model_code = model_code

        if self.model_code not in SUPPORTED_ROBOVAC_MODELS:
            raise ModelNotSupportedException(
                "Model {} is not supported".format(self.model_code)
            )

    def getHomeAssistantFeatures(self) -> int:
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        supportedFeatures: int = (
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

        if self.model_code in HAS_MAP_FEATURE:
            supportedFeatures |= VacuumEntityFeature.MAP

        return supportedFeatures

    def getRoboVacFeatures(self) -> int:
        """Get the supported features of the device.

        Returns:
            An integer representing the supported features of the device.
        """
        series = self.getRoboVacSeries()
        supportedFeatures: int
        if series is None:
            # Default to empty features if series not found
            supportedFeatures = 0
        else:
            # Explicitly cast to int to satisfy mypy
            supportedFeatures = int(ROBOVAC_SERIES_FEATURES[series])

        if self.model_code in HAS_MAP_FEATURE:
            supportedFeatures |= RoboVacEntityFeature.MAP

        if self.model_code in HAS_CONSUMABLES:
            supportedFeatures |= RoboVacEntityFeature.CONSUMABLES

        return supportedFeatures

    def getRoboVacSeries(self) -> str | None:
        """Get the series of the device.

        Returns:
            A string representing the series of the device.
        """
        for series, models in ROBOVAC_SERIES.items():
            if self.model_code in models:
                return series
        return None

    def getFanSpeeds(self) -> list[str]:
        """Get the supported fan speeds of the device.

        Returns:
            A list of strings representing the supported fan speeds of the device.
        """
        series = self.getRoboVacSeries()
        if series is None:
            # Return empty list if series not found
            return []
        return ROBOVAC_SERIES_FAN_SPEEDS[series]
