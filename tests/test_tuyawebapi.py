import pytest
from custom_components.robovac.tuyawebapi import TuyaAPISession

def test_generate_new_device_id():
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

def test_get_signature():
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
