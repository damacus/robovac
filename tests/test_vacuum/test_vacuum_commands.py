"""Tests for the RoboVac vacuum entity commands."""

import pytest
from typing import Any
from unittest.mock import patch, MagicMock, AsyncMock, call

from homeassistant.const import (
    CONF_ACCESS_TOKEN,
    CONF_DESCRIPTION,
    CONF_ID,
    CONF_IP_ADDRESS,
    CONF_MAC,
    CONF_MODEL,
    CONF_NAME,
)

from custom_components.robovac.proto_decode import decode_clean_param_response
from custom_components.robovac.robovac import RoboVac
from custom_components.robovac.vacuum import RoboVacEntity


@pytest.mark.asyncio
async def test_async_locate(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_locate method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Initialize the entity's tuyastatus attribute
        mock_robovac._dps = {"103": False}
        entity.tuyastatus = mock_robovac._dps

        # Act
        await entity.async_locate()

        # Assert
        mock_robovac.async_set.assert_called_once_with({"103": True})

        # Reset mock
        mock_robovac.async_set.reset_mock()

        # Test when locate is on
        mock_robovac._dps = {"103": True}
        entity.tuyastatus = mock_robovac._dps

        # Act
        await entity.async_locate()

        # Assert
        mock_robovac.async_set.assert_called_once_with({"103": False})


@pytest.mark.asyncio
async def test_async_return_to_base(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_return_to_base method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        await entity.async_return_to_base()

        # Assert
        mock_robovac.async_set.assert_called_once_with({"101": "return"})


@pytest.mark.asyncio
async def test_async_start(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_start method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        await entity.async_start()

        # Assert
        assert entity._attr_mode == "auto"
        mock_robovac.async_set.assert_called_once_with({"5": "Auto"})


@pytest.mark.asyncio
async def test_async_start_model_specific(mock_robovac, mock_vacuum_data: Any, mock_l60, mock_l60_data) -> None:
    """Test that async_start uses the correct code for different models."""
    # Test with standard model (should use code "5")
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        await entity.async_start()
        mock_robovac.async_set.assert_called_once_with({"5": "Auto"})
        mock_robovac.async_set.reset_mock()

    # Test with L60 model (should use code "152")
    # Mock should return "152" for the MODE code
    mock_l60.getDpsCodes.return_value = {"MODE": "152"}
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_l60):
        entity = RoboVacEntity(mock_l60_data)
        await entity.async_start()
        # Now that we've updated the implementation, L60 should send base64 value "BBoCCAE="
        # instead of "auto" for the MODE command
        mock_l60.async_set.assert_called_once_with({"152": "BBoCCAE="})


@pytest.mark.asyncio
async def test_async_start_sends_start_pause_for_boolean_models(
    mock_vacuum_data,
) -> None:
    """Test async_start also sends START_PAUSE for models with boolean toggle.

    GH-303: Models like T2128 use boolean START_PAUSE (True=start, False=pause).
    async_start must send both MODE and START_PAUSE for these models.
    """
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2128",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    robovac.async_set = AsyncMock(return_value=True)

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        await entity.async_start()

        robovac.async_set.assert_called_once_with({"5": "Auto", "2": True})


@pytest.mark.asyncio
async def test_async_pause_sends_boolean_for_toggle_models(
    mock_vacuum_data,
) -> None:
    """Test async_pause sends boolean False for models with boolean START_PAUSE.

    GH-303: Models like T2128 need False (not string 'pause') sent to DPS code 2.
    """
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2128",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    robovac.async_set = AsyncMock(return_value=True)

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        await entity.async_pause()

        robovac.async_set.assert_called_once_with({"2": False})


@pytest.mark.asyncio
async def test_async_pause_sends_mode_payload_when_model_requires_it(
    mock_vacuum_data,
) -> None:
    """Test async_pause sends model-specific mode payloads with boolean pause."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    robovac.async_set = AsyncMock(return_value=True)

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        await entity.async_pause()

        robovac.async_set.assert_called_once_with({"2": False, "152": "AggN"})


@pytest.mark.asyncio
async def test_async_return_to_base_sends_mode_payload_when_model_requires_it(
    mock_vacuum_data,
) -> None:
    """Test return-to-base updates mode DPS for models with encoded mode payloads."""
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        robovac = RoboVac(
            model_code="T2320",
            device_id="test_id",
            host="192.168.1.100",
            local_key="test_key",
        )
    robovac.async_set = AsyncMock(return_value=True)

    with patch("custom_components.robovac.vacuum.RoboVac", return_value=robovac):
        entity = RoboVacEntity(mock_vacuum_data)
        await entity.async_return_to_base()

        robovac.async_set.assert_called_once_with({"153": True, "152": "AggG", "2": True})


@pytest.mark.asyncio
async def test_async_set_clean_param_uses_model_default_before_dps154_read() -> None:
    """Test T2320 clean-param settings can be changed before DPS 154 is read."""
    data = {
        CONF_NAME: "Test X9",
        CONF_ID: "test_x9_id",
        CONF_MODEL: "T2320",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "X9 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:99",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(data)
    assert entity.vacuum is not None
    entity.vacuum._dps = {}
    entity.tuyastatus = {}
    entity.vacuum.async_set = AsyncMock(return_value=True)

    await entity.async_set_clean_param(clean_type="mop_only", mop_level="low")

    entity.vacuum.async_set.assert_called_once()
    payload = entity.vacuum.async_set.call_args.args[0]
    assert list(payload) == ["154"]
    clean_param = decode_clean_param_response(payload["154"])["clean_param"]
    assert clean_param["clean_type"] == "mop_only"
    assert clean_param["mop_level"] == "low"
    assert entity.tuyastatus["154"] == payload["154"]
    assert entity.vacuum._dps["154"] == payload["154"]
    assert entity.clean_type == "mop_only"
    assert entity.mop_level == "low"


@pytest.mark.asyncio
async def test_update_entity_values_does_not_display_default_before_dps154_read() -> None:
    """Test T2320 clean-param display values wait for a real DPS 154 read."""
    data = {
        CONF_NAME: "Test X9",
        CONF_ID: "test_x9_id",
        CONF_MODEL: "T2320",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "X9 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:99",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(data)
    assert entity.vacuum is not None
    entity.vacuum._dps = {
        "151": True,
        "156": True,
        "158": "Standard",
        "159": True,
        "160": False,
        "161": 80,
        "163": 29,
    }

    entity.update_entity_values()

    assert entity.clean_type is None
    assert entity.mop_level is None
    assert entity.edge_hugging_mopping is None


@pytest.mark.asyncio
async def test_update_entity_values_preserves_clean_params_on_partial_update() -> None:
    """Test battery-only updates do not clear the last real DPS 154 decode."""
    data = {
        CONF_NAME: "Test X9",
        CONF_ID: "test_x9_id",
        CONF_MODEL: "T2320",
        CONF_IP_ADDRESS: "192.168.1.100",
        CONF_ACCESS_TOKEN: "test_key",
        CONF_DESCRIPTION: "X9 Pro",
        CONF_MAC: "aa:bb:cc:dd:ee:99",
    }
    with patch("custom_components.robovac.robovac.TuyaDevice.__init__", return_value=None):
        entity = RoboVacEntity(data)
    assert entity.vacuum is not None
    entity.vacuum._dps = {
        "154": "JgoOCgIIAhIAGgAiAggCKgASABoAIhAKAggCGgAiAggCKgAyAggB",
        "163": 29,
    }

    entity.update_entity_values()
    assert entity.clean_type == "sweep_and_mop"
    assert entity.edge_hugging_mopping is False

    entity.vacuum._dps = {"163": 30}
    entity.update_entity_values()

    assert entity.clean_type == "sweep_and_mop"
    assert entity.edge_hugging_mopping is False


@pytest.mark.asyncio
async def test_async_pause(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_pause method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        await entity.async_pause()

        # Assert
        mock_robovac.async_set.assert_called_once_with({"2": "pause"})


@pytest.mark.asyncio
async def test_async_stop(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_stop method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Mock the async_return_to_base method
        with patch.object(entity, "async_return_to_base") as mock_return:
            # Act
            await entity.async_stop()

            # Assert
            mock_return.assert_called_once()


@pytest.mark.asyncio
async def test_async_clean_spot(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_clean_spot method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        await entity.async_clean_spot()

        # Assert
        mock_robovac.async_set.assert_called_once_with({"5": "Spot"})


@pytest.mark.asyncio
async def test_async_set_fan_speed(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_set_fan_speed method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Test cases for fan speed conversion
        test_cases = [
            ("Turbo", "Turbo"),                # Input normalized to "turbo" -> maps to "Turbo"
            ("Max", "Max"),                    # Input normalized to "max" -> maps to "Max"
            ("Standard", "Standard"),          # Input normalized to "standard" -> maps to "Standard"
            ("Quiet", "quiet"),                # Input normalized to "quiet" -> not in mapping, returns input
            ("Boost_IQ", "Boost IQ"),          # Input normalized to "boost_iq" -> maps to "Boost IQ"
            ("No_suction", "No Suction"),  # Input normalized to "no_suction" -> maps to "No Suction"
        ]

        for input_speed, expected_output in test_cases:
            # Reset mock
            mock_robovac.async_set.reset_mock()

            # Act
            await entity.async_set_fan_speed(input_speed)

            # Assert
            mock_robovac.async_set.assert_called_once_with({"102": expected_output})


@pytest.mark.asyncio
async def test_async_send_command(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_send_command method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Test edge clean command
        await entity.async_send_command("edgeClean")
        mock_robovac.async_set.assert_called_once_with({"5": "Edge"})
        mock_robovac.async_set.reset_mock()

        # Test small room clean command
        await entity.async_send_command("smallRoomClean")
        mock_robovac.async_set.assert_called_once_with({"5": "SmallRoom"})
        mock_robovac.async_set.reset_mock()

        # Test auto clean command
        await entity.async_send_command("autoClean")
        mock_robovac.async_set.assert_called_once_with({"5": "Auto"})
        mock_robovac.async_set.reset_mock()

        # Test auto return command (when off - should toggle to on)
        entity._attr_auto_return = False
        await entity.async_send_command("autoReturn")
        mock_robovac.async_set.assert_called_once_with({"135": True})
        mock_robovac.async_set.reset_mock()

        # Test auto return command (when on - should toggle to off)
        entity._attr_auto_return = True
        await entity.async_send_command("autoReturn")
        mock_robovac.async_set.assert_called_once_with({"135": False})
        mock_robovac.async_set.reset_mock()

        # Test do not disturb command (when off - should toggle to on)
        entity._attr_do_not_disturb = False
        await entity.async_send_command("doNotDisturb")
        mock_robovac.async_set.assert_called_once_with({"107": True})
        mock_robovac.async_set.reset_mock()

        # Test do not disturb command (when on - should toggle to off)
        entity._attr_do_not_disturb = True
        await entity.async_send_command("doNotDisturb")
        mock_robovac.async_set.assert_called_once_with({"107": False})
        mock_robovac.async_set.reset_mock()

        # Test boost IQ command (when off - should toggle to on)
        entity._attr_boost_iq = False
        await entity.async_send_command("boostIQ")
        mock_robovac.async_set.assert_called_once_with({"118": True})
        mock_robovac.async_set.reset_mock()

        # Test boost IQ command (when on - should toggle to off)
        entity._attr_boost_iq = True
        await entity.async_send_command("boostIQ")
        mock_robovac.async_set.assert_called_once_with({"118": False})


@pytest.mark.asyncio
async def test_async_update(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_update method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act - normal update
        await entity.async_update()

        # Assert
        mock_robovac.async_get.assert_called_once()

        # Reset mock
        mock_robovac.async_get.reset_mock()

        # Test with unsupported model
        entity.error_code = "UNSUPPORTED_MODEL"
        await entity.async_update()
        mock_robovac.async_get.assert_not_called()

        # Reset error code
        entity.error_code = None

        # Test with empty IP address
        entity._attr_ip_address = ""
        await entity.async_update()
        assert entity.error_code == "IP_ADDRESS"
        mock_robovac.async_get.assert_not_called()


@pytest.mark.asyncio
async def test_async_will_remove_from_hass(mock_robovac, mock_vacuum_data) -> None:
    """Test the async_will_remove_from_hass method."""
    # Arrange
    with patch("custom_components.robovac.vacuum.RoboVac", return_value=mock_robovac):
        entity = RoboVacEntity(mock_vacuum_data)

        # Act
        await entity.async_will_remove_from_hass()

        # Assert
        mock_robovac.async_disable.assert_called_once()
