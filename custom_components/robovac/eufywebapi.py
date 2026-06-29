"""Eufy Web API integration for RoboVac.

Original Work from: Andre Borie https://gitlab.com/Rjevski/eufy-device-id-and-local-key-grabber
"""

from typing import Optional
import requests

eufyheaders = {
    "User-Agent": "EufyHome-Android-2.4.0",
    "timezone": "Europe/London",
    "category": "Home",
    "token": "",
    "uid": "",
    "openudid": "sdk_gphone64_arm64",
    "clientType": "2",
    "language": "en",
    "country": "US",
    "Accept-Encoding": "gzip",
}


class EufyLogon:
    """Class to handle Eufy API authentication and requests."""

    def __init__(self, username: str, password: str) -> None:
        """Initialize the EufyLogon class.

        Args:
            username: The user's email address
            password: The user's password
        """
        self.username = username
        self.password = password

    def get_user_info(self) -> Optional[requests.Response]:
        """Get user information from Eufy API.

        Returns:
            Response object or None if connection error occurs.
        """
        login_url = "https://home-api.eufylife.com/v1/user/email/login"
        login_auth = {
            "client_Secret": "GQCpr9dSp3uQpsOMgJ4xQ",
            "client_id": "eufyhome-app",
            "email": self.username,
            "password": self.password,
        }

        try:
            # Create a local copy of headers to prevent cross-session data leakage
            headers = eufyheaders.copy()
            return requests.post(login_url, json=login_auth, headers=headers, timeout=10)
        except requests.exceptions.RequestException:
            return None

    def get_user_settings(
        self, url: str, userid: str, token: str
    ) -> Optional[requests.Response]:
        """Get user settings from Eufy API.

        Args:
            url: Base URL for the API
            userid: User ID
            token: Authentication token

        Returns:
            Response object or None if connection error occurs.
        """
        setting_url = url + "/v1/user/setting"
        # Create a local copy of headers to prevent cross-session data leakage
        headers = eufyheaders.copy()
        headers["token"] = token
        headers["id"] = userid
        try:
            return requests.request(
                "GET", setting_url, headers=headers, timeout=10
            )
        except requests.exceptions.RequestException:
            return None

    def get_device_info(
        self, url: str, userid: str, token: str
    ) -> Optional[requests.Response]:
        """Get device information from Eufy API.

        Args:
            url: Base URL for the API
            userid: User ID
            token: Authentication token

        Returns:
            Response object or None if connection error occurs.
        """
        device_url = url + "/v1/device/v2"
        devices_and_groups_url = (
            "https://home-api.eufylife.com/v1/device/list/devices-and-groups"
        )
        # Create a local copy of headers to prevent cross-session data leakage
        headers = eufyheaders.copy()
        headers["token"] = token
        headers["id"] = userid
        try:
            response = requests.request("GET", device_url, headers=headers, timeout=10)
            if self._has_device_records(response):
                return response

            return requests.request(
                "GET", devices_and_groups_url, headers=headers, timeout=10
            )
        except requests.exceptions.RequestException:
            return None

    @staticmethod
    def _has_device_records(response: requests.Response) -> bool:
        """Return True when a Eufy device response contains device records."""
        try:
            payload = response.json()
        except ValueError:
            return False

        devices = payload.get("devices")
        if isinstance(devices, list) and devices:
            return True

        items = payload.get("items")
        if not isinstance(items, list):
            return False

        return any(
            isinstance(item, dict) and isinstance(item.get("device"), dict)
            for item in items
        )
