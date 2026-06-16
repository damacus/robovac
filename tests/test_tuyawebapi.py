import pytest
from unittest.mock import patch, MagicMock
from custom_components.robovac.tuyawebapi import TuyaAPISession


def test_generate_new_device_id() -> None:
    """Test generating a new device ID."""
    device_id = TuyaAPISession.generate_new_device_id()
    assert isinstance(device_id, str)
    assert len(device_id) == 44
    assert device_id.startswith("8534c8ec0ed0")

    # Verify all characters are valid base64 (alphanumeric for this purpose)
    import string
    allowed_chars = string.ascii_letters + string.digits
    for char in device_id:
        assert char in allowed_chars, f"Invalid character '{char}' in device ID"


def test_get_signature() -> None:
    """Test generating a signature for the Tuya API request."""
    query_params = {
        "a": "tuya.m.device.get",
        "v": "1.0",
        "time": "1234567890",
        "deviceId": "test_device_id",
        "appVersion": "2.4.0",
        "clientId": "test_client_id"
    }
    encoded_post_data = '{"key":"value"}'

    signature = TuyaAPISession.get_signature(query_params, encoded_post_data)

    assert isinstance(signature, str)
    assert len(signature) == 64  # SHA256 hex digest length
    # Check that signature is hex
    int(signature, 16)


def test_unpadded_rsa() -> None:
    from custom_components.robovac.tuyawebapi import unpadded_rsa
    # Small numbers for fast testing
    # Plaintext "A" = 65
    res = unpadded_rsa(3, 33, b"A")
    assert isinstance(res, bytes)


def test_shuffled_md5() -> None:
    from custom_components.robovac.tuyawebapi import shuffled_md5
    res = shuffled_md5("test")
    assert isinstance(res, str)
    assert len(res) == 32


@patch("custom_components.robovac.tuyawebapi.requests.Session.post")
def test_tuya_api_session_request(mock_post) -> None:
    """Test _request method of TuyaAPISession."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"result": {"success": True}}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    session = TuyaAPISession("username", "EU", "Europe/London", "44")
    # Setting session ID so it doesn't try to acquire one
    session.session_id = "test_sid"

    res = session._request("test.action", version="1.0", data={"key": "value"})
    assert res == {"success": True}
    mock_post.assert_called_once()

    # Check that query string gets sign
    args, kwargs = mock_post.call_args
    assert "sign" in kwargs["params"]


def test_tuya_api_session_determine_password() -> None:
    session = TuyaAPISession("username", "EU", "Europe/London", "44")
    res = session.determine_password("username")
    assert isinstance(res, str)
    assert len(res) == 32
