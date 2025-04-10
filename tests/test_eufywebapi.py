"""Tests for the Eufy web API integration."""

import json
from unittest.mock import patch, MagicMock
import pytest
import requests

from custom_components.robovac.eufywebapi import EufyLogon


@pytest.fixture
def mock_requests_post():
    """Create a mock for requests.post."""
    with patch("requests.post") as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_get():
    """Create a mock for requests.get."""
    with patch("requests.get") as mock_get:
        yield mock_get


@pytest.fixture
def mock_requests_request():
    """Create a mock for requests.request."""
    with patch("requests.request") as mock_request:
        yield mock_request


@pytest.fixture
def mock_successful_login_response():
    """Create a mock successful login response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "res_code": 1,
        "user_info": {
            "id": "test_user_id",
            "email": "test@example.com",
            "nick_name": "Test User",
            "phone_code": "44",
            "phone": "1234567890",
            "country": "GB",
            "language": "en",
            "request_host": "test-api.eufylife.com",
            "timezone": "Europe/London",
        },
        "access_token": "test_access_token",
    }
    return response


@pytest.fixture
def mock_device_info_response():
    """Create a mock device info response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "items": [
            {
                "device": {
                    "id": "test_device_id",
                    "name": "RoboVac 15C",
                    "alias_name": "Test RoboVac",
                    "product": {
                        "product_code": "T2118",
                        "appliance": "Cleaning",
                    },
                    "wifi": {
                        "mac": "AA:BB:CC:DD:EE:FF",
                    },
                },
            }
        ]
    }
    return response


@pytest.fixture
def mock_user_settings_response():
    """Create a mock user settings response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "setting": {
            "home_setting": {
                "tuya_home": {
                    "tuya_region_code": "EU",
                }
            }
        }
    }
    return response


def test_init():
    """Test EufyLogon initialization."""
    eufy = EufyLogon("test@example.com", "password123")
    assert eufy.username == "test@example.com"
    assert eufy.password == "password123"


def test_get_user_info(mock_requests_post, mock_successful_login_response):
    """Test get_user_info method."""
    # Set up the mock
    mock_requests_post.return_value = mock_successful_login_response

    # Call the method
    eufy = EufyLogon("test@example.com", "password123")
    response = eufy.get_user_info()

    # Verify the response
    assert response.status_code == 200
    assert response.json()["res_code"] == 1
    assert response.json()["user_info"]["id"] == "test_user_id"
    assert response.json()["access_token"] == "test_access_token"

    # Verify the request
    mock_requests_post.assert_called_once()
    args, kwargs = mock_requests_post.call_args
    assert args[0] == "https://home-api.eufylife.com/v1/user/email/login"
    assert kwargs["json"]["email"] == "test@example.com"
    assert kwargs["json"]["password"] == "password123"
    # The eufyheaders don't include app_version, so we shouldn't check for it
    assert "User-Agent" in kwargs["headers"]


def test_get_device_info(mock_requests_request, mock_device_info_response):
    """Test get_device_info method."""
    # Set up the mock
    mock_requests_request.return_value = mock_device_info_response

    # Call the method
    eufy = EufyLogon("test@example.com", "password123")
    response = eufy.get_device_info(
        "https://test-api.eufylife.com", "test_user_id", "test_access_token"
    )

    # Verify the response
    assert response.status_code == 200
    assert "items" in response.json()
    assert response.json()["items"][0]["device"]["id"] == "test_device_id"

    # Verify the request
    mock_requests_request.assert_called_once()
    args, kwargs = mock_requests_request.call_args
    assert "test-api.eufylife.com" in args[1]  # Second arg is the URL
    assert kwargs["headers"]["token"] == "test_access_token"
    # The eufyheaders don't include app_version, so we shouldn't check for it
    assert "User-Agent" in kwargs["headers"]


def test_get_user_settings(mock_requests_request, mock_user_settings_response):
    """Test get_user_settings method."""
    # Set up the mock
    mock_requests_request.return_value = mock_user_settings_response

    # Call the method
    eufy = EufyLogon("test@example.com", "password123")
    response = eufy.get_user_settings(
        "https://test-api.eufylife.com", "test_user_id", "test_access_token"
    )

    # Verify the response
    assert response.status_code == 200
    assert "setting" in response.json()
    assert (
        response.json()["setting"]["home_setting"]["tuya_home"]["tuya_region_code"]
        == "EU"
    )

    # Verify the request
    mock_requests_request.assert_called_once()
    args, kwargs = mock_requests_request.call_args
    assert "test-api.eufylife.com" in args[1]  # Second arg is the URL
    assert kwargs["headers"]["token"] == "test_access_token"
    # The eufyheaders don't include app_version, so we shouldn't check for it
    assert "User-Agent" in kwargs["headers"]


def test_failed_login():
    """Test failed login."""
    # Create a mock response for a failed login
    mock_response = MagicMock()
    mock_response.status_code = 401
    mock_response.json.return_value = {"res_code": 0, "msg": "Invalid credentials"}

    with patch("requests.post", return_value=mock_response):
        eufy = EufyLogon("test@example.com", "wrong_password")
        response = eufy.get_user_info()

        # Verify the response
        assert response.status_code == 401
        assert response.json()["res_code"] == 0


def test_connection_error():
    """Test connection error handling."""
    # We need to modify the EufyLogon class to handle connection errors
    # For now, let's patch the get_user_info method to handle the error
    with patch("requests.post", side_effect=requests.exceptions.ConnectionError):
        # Create a try/except block to catch the ConnectionError
        try:
            eufy = EufyLogon("test@example.com", "password123")
            response = eufy.get_user_info()
            # If we get here, the exception was handled internally
            assert response is None
        except requests.exceptions.ConnectionError:
            # If we get here, the exception wasn't handled, so the test should fail
            pytest.fail("ConnectionError was not handled by the EufyLogon class")
