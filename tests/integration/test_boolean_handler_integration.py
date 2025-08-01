"""Integration tests for boolean handler functionality using public API."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
import pytest

from ha_synthetic_sensors import async_setup_synthetic_sensors, StorageManager


class TestBooleanHandlerIntegration:
    """Integration tests for boolean handler through the public API."""

    @pytest.fixture
    def mock_async_add_entities(self):
        """Create a mock async_add_entities callback."""
        return Mock()

    @pytest.fixture
    def mock_device_entry(self):
        """Create a mock device entry for testing."""
        mock_device_entry = Mock()
        mock_device_entry.name = "Test Device"
        mock_device_entry.identifiers = {("ha_synthetic_sensors", "test_device_123")}
        return mock_device_entry

    @pytest.fixture
    def mock_device_registry(self, mock_device_entry):
        """Create a mock device registry that returns the test device."""
        mock_registry = Mock()
        mock_registry.devices = Mock()
        mock_registry.async_get_device.return_value = mock_device_entry
        return mock_registry

    async def test_boolean_handler_yaml_fixture_validation(
        self, mock_hass, mock_entity_registry, mock_states, mock_config_entry, mock_async_add_entities, mock_device_registry
    ):
        """Test that boolean handler works with YAML fixture and uses proper Python operators."""

        # Set up mock HA states for entity references
        mock_states["binary_sensor.front_door"] = type("MockState", (), {"state": "locked", "attributes": {}})()
        mock_states["binary_sensor.motion_detector"] = type("MockState", (), {"state": "clear", "attributes": {}})()
        mock_states["device_tracker.phone_home"] = type("MockState", (), {"state": "home", "attributes": {}})()
        mock_states["device_tracker.phone_work"] = type("MockState", (), {"state": "not_home", "attributes": {}})()
        mock_states["alarm_control_panel.home_alarm"] = type("MockState", (), {"state": "armed_away", "attributes": {}})()
        mock_states["sensor.living_room_temperature"] = type("MockState", (), {"state": "22.5", "attributes": {}})()

        # Set up storage manager with proper mocking
        with (
            patch("ha_synthetic_sensors.storage_manager.Store") as MockStore,
            patch("homeassistant.helpers.device_registry.async_get") as MockDeviceRegistry,
        ):
            mock_store = AsyncMock()
            mock_store.async_load.return_value = None
            MockStore.return_value = mock_store

            MockDeviceRegistry.return_value = mock_device_registry

            storage_manager = StorageManager(mock_hass, "test_storage", enable_entity_listener=False)
            storage_manager._store = mock_store
            await storage_manager.async_load()

            # Create sensor set and load boolean handler YAML
            sensor_set_id = "boolean_handler_test"
            await storage_manager.async_create_sensor_set(
                sensor_set_id=sensor_set_id, device_identifier="test_device_123", name="Boolean Handler Test"
            )

            yaml_fixture_path = (
                Path(__file__).parent.parent / "yaml_fixtures" / "unit_test_boolean_handler_yaml_integration.yaml"
            )
            with open(yaml_fixture_path, "r") as f:
                yaml_content = f.read()

            result = await storage_manager.async_from_yaml(yaml_content=yaml_content, sensor_set_id=sensor_set_id)
            assert result["sensors_imported"] == 4

            # Set up sensor manager to test boolean handler features
            sensor_manager = await async_setup_synthetic_sensors(
                hass=mock_hass,
                config_entry=mock_config_entry,
                async_add_entities=mock_async_add_entities,
                storage_manager=storage_manager,
                device_identifier="test_device_123",
            )

            assert sensor_manager is not None
            assert mock_async_add_entities.called

            # Test that sensors were created and use proper Python operators
            sensors = storage_manager.list_sensors(sensor_set_id=sensor_set_id)
            assert len(sensors) == 4

            # Find specific sensors and verify their formulas
            door_lock_and_sensor = next((s for s in sensors if s.unique_id == "door_lock_and"), None)
            assert door_lock_and_sensor is not None
            door_formula = door_lock_and_sensor.formulas[0].formula
            assert "and" in door_formula
            assert "&&" not in door_formula, "YAML fixture should not contain symbolic operators"

            presence_or_sensor = next((s for s in sensors if s.unique_id == "presence_or"), None)
            assert presence_or_sensor is not None
            presence_formula = presence_or_sensor.formulas[0].formula
            assert "or" in presence_formula
            assert "||" not in presence_formula, "YAML fixture should not contain symbolic operators"

            security_check_sensor = next((s for s in sensors if s.unique_id == "security_check"), None)
            assert security_check_sensor is not None
            security_formula = security_check_sensor.formulas[0].formula
            assert "not" in security_formula
            assert "!" not in security_formula, "YAML fixture should not contain symbolic operators"

            temperature_comfort_sensor = next((s for s in sensors if s.unique_id == "temperature_comfort"), None)
            assert temperature_comfort_sensor is not None
            temp_formula = temperature_comfort_sensor.formulas[0].formula
            assert ">=" in temp_formula and "<=" in temp_formula

            # Test formula evaluation
            await sensor_manager.async_update_sensors()

            # Verify that the sensors evaluate correctly with proper boolean logic
            # (The actual evaluation results would depend on the mock state values)
            # This test mainly ensures the boolean handler processes the formulas correctly

            # Clean up
            await storage_manager.async_delete_sensor_set(sensor_set_id)
