"""Integration tests for Idiom 3: Attribute Access Patterns."""

import pytest
from unittest.mock import MagicMock
from ha_synthetic_sensors.config_manager import ConfigManager
from ha_synthetic_sensors.sensor_manager import SensorManager, SensorManagerConfig
from ha_synthetic_sensors.exceptions import MissingDependencyError


class TestIdiom3AttributeAccess:
    """Test Idiom 3: Attribute Access Patterns."""

    @pytest.fixture
    def config_manager(self, mock_hass, mock_entity_registry, mock_states):
        """Create a config manager with mock HA."""
        return ConfigManager(mock_hass)

    @pytest.fixture
    def basic_attribute_yaml(self):
        """Load the basic attribute YAML file."""
        yaml_path = "examples/idiom_3_basic_attribute.yaml"
        with open(yaml_path, "r", encoding="utf-8") as file:
            return file.read()

    @pytest.fixture
    def multiple_attributes_yaml(self):
        """Load the multiple attributes YAML file."""
        yaml_path = "examples/idiom_3_multiple_attributes.yaml"
        with open(yaml_path, "r", encoding="utf-8") as file:
            return file.read()

    @pytest.fixture
    def nested_attributes_yaml(self):
        """Load the nested attributes YAML file."""
        yaml_path = "examples/idiom_3_nested_attributes.yaml"
        with open(yaml_path, "r", encoding="utf-8") as file:
            return file.read()

    @pytest.fixture
    def missing_attribute_yaml(self):
        """Load the missing attribute YAML file."""
        yaml_path = "examples/idiom_3_missing_attribute.yaml"
        with open(yaml_path, "r", encoding="utf-8") as file:
            return file.read()

    def test_basic_attribute_access(self, config_manager, basic_attribute_yaml, mock_hass, mock_entity_registry, mock_states):
        """Test formula accesses entity attribute using dot notation."""
        config = config_manager.load_from_yaml(basic_attribute_yaml)
        sensor = config.sensors[0]

        # Create sensor manager with data provider that returns data with attributes
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {"voltage": 240.0, "current": 4.17, "power_factor": 0.95},
                }
            elif entity_id == "sensor.backup_device":
                return {
                    "value": 85.0,  # Battery level as main state
                    "exists": True,
                    "attributes": {"battery_level": 85.0, "status": "charging"},
                }
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power", "sensor.backup_device"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"battery_efficiency": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Main formula should succeed: state.voltage * state.current = 240 * 4.17 = 1000.8
        assert main_result["success"] is True

    def test_multiple_attribute_access(
        self, config_manager, multiple_attributes_yaml, mock_hass, mock_entity_registry, mock_states
    ):
        """Test formula accesses multiple attributes from same entity."""
        config = config_manager.load_from_yaml(multiple_attributes_yaml)
        sensor = config.sensors[0]

        # Create sensor manager with data provider that returns data with attributes
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {"voltage": 240.0, "current": 4.17, "power_factor": 0.95, "frequency": 60.0},
                }
            elif entity_id == "sensor.power_meter":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {"voltage": 240.0, "current": 4.17, "power_factor": 0.95, "frequency": 60.0},
                }
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power", "sensor.power_meter"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"comprehensive_analysis": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Main formula should succeed: state.voltage * state.current * state.power_factor = 240 * 4.17 * 0.95
        assert main_result["success"] is True

    def test_nested_attribute_access(
        self, config_manager, nested_attributes_yaml, mock_hass, mock_entity_registry, mock_states
    ):
        """Test formula accesses nested attribute structures."""
        config = config_manager.load_from_yaml(nested_attributes_yaml)
        sensor = config.sensors[0]

        # Create sensor manager with data provider that returns data with nested attributes
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {
                        "voltage": 240.0,
                        "current": 4.17,
                        "device_info": {"manufacturer": "SpanPanel", "model": "SPAN-200"},
                        "power_factor": {"value": 0.95, "unit": "ratio"},
                    },
                }
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"nested_attribute_test": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Main formula should succeed: state.attributes.voltage * state.attributes.current = 240 * 4.17 = 1000.8
        assert main_result["success"] is True

    def test_missing_attribute_error(
        self, config_manager, missing_attribute_yaml, mock_hass, mock_entity_registry, mock_states
    ):
        """Test formula references non-existent attribute."""
        config = config_manager.load_from_yaml(missing_attribute_yaml)
        sensor = config.sensors[0]

        # Create sensor manager with data provider that returns data without the referenced attribute
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {
                        "voltage": 240.0,
                        "current": 4.17,
                        # Missing "nonexistent_attribute"
                    },
                }
            elif entity_id == "sensor.power_meter":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {
                        "voltage": 240.0,
                        "current": 4.17,
                        # Missing "nonexistent_attribute"
                    },
                }
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power", "sensor.power_meter"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"missing_attr_test": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        # Should fail because the attribute doesn't exist
        with pytest.raises(MissingDependencyError) as exc_info:
            evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Should fail due to missing attribute
        error_message = str(exc_info.value)
        assert "nonexistent_attribute" in error_message or "not found" in error_message.lower()

    def test_attribute_access_in_variables(
        self, config_manager, nested_attributes_yaml, mock_hass, mock_entity_registry, mock_states
    ):
        """Test accessing nested attributes in variables."""
        config = config_manager.load_from_yaml(nested_attributes_yaml)

        # Find the sensor with variables
        sensor = next(s for s in config.sensors if s.unique_id == "nested_variable_test")
        assert sensor is not None

        # Create sensor manager with data provider
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {"value": 1000.0, "exists": True, "attributes": {"voltage": 240.0, "current": 4.17}}
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"nested_variable_test": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Main formula should succeed: voltage_attr * current_attr = 240 * 4.17 = 1000.8
        assert main_result["success"] is True

    def test_attribute_access_in_attributes(
        self, config_manager, nested_attributes_yaml, mock_hass, mock_entity_registry, mock_states
    ):
        """Test accessing nested attributes in attribute formulas."""
        config = config_manager.load_from_yaml(nested_attributes_yaml)

        # Find the sensor with attributes
        sensor = next(s for s in config.sensors if s.unique_id == "nested_attribute_formula")
        assert sensor is not None

        # Create sensor manager with data provider
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {
                    "value": 1000.0,
                    "exists": True,
                    "attributes": {
                        "voltage": 240.0,
                        "current": 4.17,
                        "device_info": {"manufacturer": "SpanPanel", "model": "SPAN-200"},
                        "power_factor": {"value": 0.95, "unit": "ratio"},
                    },
                }
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"nested_attribute_formula": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation first
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]
        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)
        assert main_result["success"] is True
        assert main_result["value"] == 1100.0  # state * 1.1 = 1000 * 1.1 = 1100

        # Test attribute formula evaluation with context from main result
        if len(sensor.formulas) > 1:
            attribute_formula = sensor.formulas[1]
            context = {"state": main_result["value"]}

            attr_result = evaluator.evaluate_formula_with_sensor_config(attribute_formula, context, sensor)
            assert attr_result["success"] is True

    def test_simple_state_token_works(self, config_manager, mock_hass, mock_entity_registry, mock_states):
        """Test that basic state token access works (supported feature)."""
        from pathlib import Path

        yaml_fixture_path = (
            Path(__file__).parent.parent / "yaml_fixtures" / "unit_test_idioms_attribute_access_simple_state.yaml"
        )
        with open(yaml_fixture_path, "r") as f:
            yaml_content = f.read()
        config = config_manager.load_from_yaml(yaml_content)
        sensor = config.sensors[0]

        # Create sensor manager with data provider
        def mock_data_provider(entity_id: str):
            if entity_id == "sensor.span_panel_instantaneous_power":
                return {"value": 1000.0, "exists": True}
            return {"value": None, "exists": False}

        mock_add_entities = MagicMock()
        sensor_manager = SensorManager(
            config_manager._hass,
            MagicMock(),  # name_resolver
            mock_add_entities,  # add_entities_callback
            SensorManagerConfig(data_provider_callback=mock_data_provider),
        )

        # Register the backing entity
        sensor_manager.register_data_provider_entities({"sensor.span_panel_instantaneous_power"})

        # Register the sensor-to-backing mapping
        sensor_to_backing_mapping = {"simple_power": "sensor.span_panel_instantaneous_power"}
        sensor_manager.register_sensor_to_backing_mapping(sensor_to_backing_mapping)

        # Test main formula evaluation
        evaluator = sensor_manager._evaluator
        main_formula = sensor.formulas[0]

        main_result = evaluator.evaluate_formula_with_sensor_config(main_formula, None, sensor)

        # Main formula should succeed: state * 1.1 = 1000 * 1.1 = 1100
        assert main_result["success"] is True
        assert main_result["value"] == 1100.0
