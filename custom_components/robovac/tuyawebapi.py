"""Tuya Web API client for Eufy RoboVac integration.

This module provides functionality to interact with the Tuya cloud API,
which is used by Eufy devices. It handles authentication, encryption,
and API requests needed to control Eufy RoboVac devices.

Original work from: https://gitlab.com/Rjevski/eufy-device-id-and-local-key-grabber
"""

from __future__ import annotations

# Standard library imports
from hashlib import md5, sha256
import hmac
import json
import math
import random
import string
import time
import uuid
from typing import Any, Dict, Optional

# Third-party imports
from cryptography.hazmat.backends.openssl import backend as openssl_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import requests
# Local imports
from .countries import get_phone_code_by_region

TUYA_INITIAL_BASE_URL = "https://a1.tuyaeu.com"

EUFY_HMAC_KEY = (
    "A_cepev5pfnhua4dkqkdpmnrdxx378mpjr_s8x78u7xwymasd9kqa7a73pjhxqsedaj".encode()
)


def unpadded_rsa(key_exponent: int, key_n: int, plaintext: bytes) -> bytes:
    """Perform RSA encryption without padding.

    Args:
        key_exponent: The RSA key exponent.
        key_n: The RSA key modulus.
        plaintext: The plaintext to encrypt.

    Returns:
        The encrypted plaintext.
    """
    keylength = math.ceil(key_n.bit_length() / 8)
    input_nr = int.from_bytes(plaintext, byteorder="big")
    crypted_nr = pow(input_nr, key_exponent, key_n)
    return crypted_nr.to_bytes(keylength, byteorder="big")


def shuffled_md5(value: str) -> str:
    """Shuffle the MD5 hash of a string.

    Args:
        value: The string to shuffle.

    Returns:
        The shuffled MD5 hash of the string.
    """
    _hash = md5(value.encode("utf-8")).hexdigest()
    return _hash[8:16] + _hash[0:8] + _hash[24:32] + _hash[16:24]


TUYA_PASSWORD_INNER_CIPHER = Cipher(
    algorithms.AES(
        bytearray(
            [36, 78, 109, 138, 86, 172, 135, 145, 36, 67, 45, 139, 108, 188, 162, 196]
        )
    ),
    modes.CBC(
        bytearray(
            [119, 36, 86, 242, 167, 102, 76, 243, 57, 44, 53, 151, 233, 62, 87, 71]
        )
    ),
    backend=openssl_backend,
)

DEFAULT_TUYA_HEADERS: Dict[str, str] = {"User-Agent": "TY-UA=APP/Android/2.4.0/SDK/null"}

SIGNATURE_RELEVANT_PARAMETERS = {
    "a",
    "v",
    "lat",
    "lon",
    "lang",
    "deviceId",
    "appVersion",
    "ttid",
    "isH5",
    "h5Token",
    "os",
    "clientId",
    "postData",
    "time",
    "requestId",
    "et",
    "n4h5",
    "sid",
    "sp",
}

DEFAULT_TUYA_QUERY_PARAMS = {
    "appVersion": "2.4.0",
    "deviceId": "",
    "platform": "sdk_gphone64_arm64",
    "clientId": "yx5v9uc3ef9wg3v9atje",
    "lang": "en",
    "osSystem": "12",
    "os": "Android",
    "timeZoneId": "",
    "ttid": "android",
    "et": "0.0.1",
    "sdkVersion": "3.0.8cAnker",
}


class TuyaAPISession:
    """Session handler for Tuya API authentication and requests.

    This class manages the authentication state and provides methods to
    interact with the Tuya API endpoints used by Eufy devices. It handles
    session creation, token acquisition, and making authenticated requests
    to the Tuya cloud API.

    Attributes:
        username: The username for the Tuya API account.
        country_code: The country code for the Tuya API account.
        session_id: The current session ID for API requests.
        base_url: The base URL for the Tuya API.
        session: The requests session object for making HTTP requests.
        default_query_params: Default query parameters for API requests.
    """

    username: Optional[str] = None
    country_code: Optional[str] = None
    session_id: Optional[str] = None
    base_url: str
    session: requests.Session
    default_query_params: Dict[str, str]

    def __init__(self, username: str, region: str, timezone: str, phone_code: str) -> None:
        """Initialize the TuyaAPISession.

        Args:
            username: The username for the Tuya API.
            region: The region code (AZ, AY, IN, EU).
            timezone: The timezone ID.
            phone_code: The phone country code.
        """
        self.session = requests.session()
        # Use update instead of direct assignment to avoid type errors
        self.session.headers.update(DEFAULT_TUYA_HEADERS)
        self.default_query_params = DEFAULT_TUYA_QUERY_PARAMS.copy()
        self.default_query_params["deviceId"] = self.generate_new_device_id()
        self.username = username
        self.country_code = phone_code
        self.base_url = {
            "AZ": "https://a1.tuyaus.com",
            "AY": "https://a1.tuyacn.com",
            "IN": "https://a1.tuyain.com",
            "EU": "https://a1.tuyaeu.com",
        }.get(region, "https://a1.tuyaeu.com")

        DEFAULT_TUYA_QUERY_PARAMS["timeZoneId"] = timezone

    @staticmethod
    def generate_new_device_id() -> str:
        """Generate a new random device ID for the Tuya API.

        Returns:
            A string containing the generated device ID.
        """
        expected_length = 44
        base64_characters = string.ascii_letters + string.digits
        device_id_dependent_part = "8534c8ec0ed0"
        return device_id_dependent_part + "".join(
            random.choice(base64_characters)
            for _ in range(expected_length - len(device_id_dependent_part))
        )

    @staticmethod
    def get_signature(query_params: dict, encoded_post_data: str) -> str:
        """Generate a signature for the Tuya API request.

        Args:
            query_params: The query parameters for the request.
            encoded_post_data: The encoded post data.

        Returns:
            The generated signature string.
        """
        query_params = query_params.copy()
        if encoded_post_data:
            query_params["postData"] = encoded_post_data
        sorted_pairs = sorted(query_params.items())
        filtered_pairs = filter(
            lambda p: p[0] and p[0] in SIGNATURE_RELEVANT_PARAMETERS, sorted_pairs
        )
        mapped_pairs = map(
            # postData is pre-emptively hashed (for performance reasons?),
            # everything else is included as-is
            lambda p: p[0] + "=" + (
                shuffled_md5(p[1]) if p[0] == "postData" else p[1]
            ),
            filtered_pairs,
        )
        message = "||".join(mapped_pairs)
        return hmac.HMAC(
            key=EUFY_HMAC_KEY, msg=message.encode("utf-8"), digestmod=sha256
        ).hexdigest()

    def _request(
        self,
        action: str,
        version: str = "1.0",
        data: Optional[Dict[str, Any]] = None,
        query_params: Optional[Dict[str, str]] = None,
        _requires_session: bool = True,
    ) -> Dict[str, Any]:
        """Make a request to the Tuya API.

        This method handles the construction of the API request, including
        authentication, request signing, and response parsing. It will automatically
        acquire a session if one is not already active and the request requires it.

        Args:
            action: The API action to perform (e.g., "tuya.m.device.get").
            version: The API version to use (default: "1.0").
            data: The data to send in the request body as a dictionary.
            query_params: Additional query parameters to include in the request.
            _requires_session: Whether this request requires an active session.
                Set to False for authentication requests.

        Returns:
            The JSON response from the API as a dictionary containing the result.

        Raises:
            ValueError: If the session is required but could not be acquired.
            requests.HTTPError: If the HTTP request fails with an HTTP error status.
            RuntimeError: If the API request fails for other reasons.
            TypeError: If the response is not a valid JSON object.
            KeyError: If the response does not contain a 'result' key.
        """
        if not self.session_id and _requires_session:
            if not self.username or not self.country_code:
                raise ValueError("Username and country code must be set for session-based requests")
            self.acquire_session()

        current_time = time.time()
        request_id = uuid.uuid4()
        extra_query_params = {
            "time": str(int(current_time)),
            "requestId": str(request_id),
            "a": action,
            "v": version,
            **(query_params or {}),
        }
        query_params = {**self.default_query_params, **extra_query_params}
        encoded_post_data = json.dumps(data, separators=(",", ":")) if data else ""

        try:
            resp = self.session.post(
                self.base_url + "/api.json",
                params={
                    **query_params,
                    "sign": self.get_signature(query_params, encoded_post_data),
                },
                data={"postData": encoded_post_data} if encoded_post_data else None,
            )
            resp.raise_for_status()
            response_data: Dict[str, Any] = resp.json()
        except requests.RequestException as e:
            # Re-raise the original exception if it's already an HTTPError
            if isinstance(e, requests.HTTPError):
                raise
            # Otherwise, raise a RuntimeError with our custom message
            raise RuntimeError(f"API request to {action} failed: {str(e)}") from e
        except json.JSONDecodeError as e:
            raise TypeError(f"Invalid JSON response from API: {str(e)}") from e

        if "result" not in response_data:
            raise KeyError(
                f"No 'result' key in the response - the entire response is {response_data}"
            )

        result: Dict[str, Any] = response_data["result"]
        return result

    def request_token(self, username: str, country_code: str) -> Dict[str, Any]:
        """Request a token from the Tuya API.

        Args:
            username: The username for the Tuya API.
            country_code: The country code.

        Returns:
            A dictionary containing the token response.
        """
        return self._request(
            action="tuya.m.user.uid.token.create",
            data={"uid": username, "countryCode": country_code},
            _requires_session=False,
        )

    def determine_password(self, username: str) -> str:
        """Determine the password for the given username.

        Args:
            username: The username to determine the password for.

        Returns:
            The determined password as a string.
        """
        new_uid = username
        padded_size = 16 * math.ceil(len(new_uid) / 16)
        password_uid = new_uid.zfill(padded_size)
        encryptor = TUYA_PASSWORD_INNER_CIPHER.encryptor()
        encrypted_uid = encryptor.update(password_uid.encode("utf8"))
        encrypted_uid += encryptor.finalize()
        return md5(encrypted_uid.hex().upper().encode("utf-8")).hexdigest()

    def request_session(self, username: str, password: str, country_code: str) -> Dict[str, Any]:
        """Request a session from the Tuya API.

        Args:
            username: The username for the Tuya API.
            password: The password for the Tuya API.
            country_code: The country code.

        Returns:
            A dictionary containing the session response.
        """
        token_response = self.request_token(username, country_code)
        encrypted_password = unpadded_rsa(
            key_exponent=int(token_response["exponent"]),
            key_n=int(token_response["publicKey"]),
            plaintext=password.encode("utf-8"),
        )
        data = {
            "uid": username,
            "createGroup": True,
            "ifencrypt": 1,
            "passwd": encrypted_password.hex(),
            "countryCode": country_code,
            "options": '{"group": 1}',
            "token": token_response["token"],
        }

        try:
            return self._request(
                action="tuya.m.user.uid.password.login.reg",
                data=data,
                _requires_session=False,
            )
        except Exception as e:
            error_password = md5("12345678".encode("utf8")).hexdigest()

            if password != error_password:
                return self.request_session(username, error_password, country_code)
            else:
                raise e

    def acquire_session(self) -> None:
        """Acquire a session from the Tuya API.

        This method acquires a session from the Tuya API.
        """
        if self.username is None:
            raise ValueError("Username is not set")
        if self.country_code is None:
            raise ValueError("Country code is not set")

        password = self.determine_password(self.username)
        session_response = self.request_session(
            self.username, password, self.country_code
        )
        self.session_id = self.default_query_params["sid"] = session_response["sid"]
        self.base_url = session_response["domain"]["mobileApiUrl"]
        self.country_code = (
            session_response["phoneCode"]
            if session_response["phoneCode"]
            else get_phone_code_by_region(session_response["domain"]["regionCode"])
        )

    def list_homes(self) -> dict:
        """List homes from the Tuya API.

        Returns:
            A dictionary containing the list of homes.
        """
        return self._request(action="tuya.m.location.list", version="2.1")

    def get_device(self, devId: str) -> dict:
        """Get device information from the Tuya API.

        Args:
            devId: The device ID to get information for.

        Returns:
            A dictionary containing the device information.
        """
        return self._request(
            action="tuya.m.device.get", version="1.0", data={"devId": devId}
        )
