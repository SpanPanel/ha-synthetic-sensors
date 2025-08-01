"""Tests for mixed variable and direct entity reference patterns using real YAML fixtures."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from ha_synthetic_sensors.dependency_parser import DependencyParser
from ha_synthetic_sensors.name_resolver import NameResolver


class TestMixedVariableAndDirectPatterns:
    """Test dependency parsing with modern patterns using real YAML fixtures."""

    @pytest.fixture
    def parser(self, mock_hass, mock_entity_registry, mock_states):
        """Create a dependency parser instance."""
        return DependencyParser(mock_hass)

    @pytest.fixture
    def storage_complex_config(self):
        """Load the complex storage test config with comprehensive patterns."""
        config_path = Path(__file__).parent.parent / "yaml_fixtures" / "storage_test_complex.yaml"
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def reference_patterns_config(self):
        """Load the reference patterns config with direct entity references."""
        config_path = Path(__file__).parent.parent / "yaml_fixtures" / "reference_patterns.yaml"
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f)

    def test_variable_extraction_from_collection_patterns(
        self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 1: Variable extraction from collection patterns."""
        sensors = storage_complex_config["sensors"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test basic variable in collection pattern
            dynamic_sum = sensors["dynamic_device_sum"]
            extracted_vars = parser.extract_variables(dynamic_sum["formula"])
            assert "device_type" in extracted_vars, "Should extract variable from collection pattern"
            assert "device_class" in extracted_vars, "Should extract collection keyword"

            # Test multiple variables in collection pattern
            area_avg = sensors["area_device_average"]
            extracted_vars = parser.extract_variables(area_avg["formula"])
            assert "target_area" in extracted_vars, "Should extract area variable"
            assert "device_type" in extracted_vars, "Should extract device_type variable"

    def test_dot_notation_variable_extraction(
        self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 2: Variable extraction from dot notation attribute access."""
        sensors = storage_complex_config["sensors"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test the battery_class.battery_level pattern
            battery_ratio = sensors["power_to_battery_ratio"]
            extracted_vars = parser.extract_variables(battery_ratio["formula"])
            assert "battery_class" in extracted_vars, "Should extract variable from dot notation"
            assert "min_battery" in extracted_vars, "Should extract threshold variable"
            assert "power_type" in extracted_vars, "Should extract power_type variable"

            # Test temperature range with dot notation
            temp_range = sensors["temperature_range_monitor"]
            extracted_vars = parser.extract_variables(temp_range["formula"])
            assert "temp_sensors" in extracted_vars, "Should extract temp_sensors variable"
            assert "min_temp" in extracted_vars, "Should extract min_temp variable"
            assert "max_temp" in extracted_vars, "Should extract max_temp variable"

    def test_attribute_formulas_with_shared_variables(
        self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 3: Attribute formulas using shared variables."""
        sensors = storage_complex_config["sensors"]
        energy_suite = sensors["energy_analysis_suite"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test main formula
            main_extracted = parser.extract_variables(energy_suite["formula"])
            assert "primary_energy_type" in main_extracted, "Main formula should use primary_energy_type"

            # Test attribute formulas use different variables from the shared pool
            attributes = energy_suite["attributes"]

            # secondary_consumption uses secondary_energy_type
            secondary_extracted = parser.extract_variables(attributes["secondary_consumption"]["formula"])
            assert "secondary_energy_type" in secondary_extracted, "Attribute should use secondary_energy_type"

            # high_usage_count uses dot notation with variables
            high_usage_extracted = parser.extract_variables(attributes["high_usage_count"]["formula"])
            assert "primary_devices" in high_usage_extracted, "Should extract variable from dot notation"
            assert "alert_threshold" in high_usage_extracted, "Should extract threshold variable"

    def test_direct_entity_references(self, parser, reference_patterns_config, mock_hass, mock_entity_registry, mock_states):
        """Test Pattern 4: Direct entity ID references."""
        sensors = reference_patterns_config["sensors"]

        # Test sensor with direct entity references in main formula
        grid_analysis = sensors["grid_dependency_analysis"]
        formula = grid_analysis["formula"]

        # Patch er.async_get to return the mock entity registry
        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            entity_refs = parser.extract_entity_references(formula)
            assert "sensor.span_panel_instantaneous_power" in entity_refs, "Should extract direct entity reference"
            assert "sensor.energy_cost_analysis" in entity_refs, "Should extract second entity reference"

        # Test mixed variables and entity references
        enhanced_power = sensors["enhanced_power_analysis"]
        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            extracted_vars = parser.extract_variables(enhanced_power["formula"])
            entity_refs = parser.extract_entity_references(enhanced_power["formula"])
            assert "base_power_analysis" in extracted_vars, "Should extract variable"
            assert "efficiency_factor" in extracted_vars, "Should extract efficiency variable"

    def test_attribute_reference_patterns(
        self, parser, reference_patterns_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 5: Different attribute reference patterns."""
        sensors = reference_patterns_config["sensors"]
        energy_cost = sensors["energy_cost_analysis"]
        attributes = energy_cost["attributes"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test entity_id reference in attribute formula
            annual_formula = attributes["annual_projected"]["formula"]
            entity_refs = parser.extract_entity_references(annual_formula)
            assert "sensor.energy_cost_analysis" in entity_refs, "Should extract entity_id reference"

            # Test comprehensive analysis with all reference types
            comprehensive = sensors["comprehensive_analysis"]
            comp_attributes = comprehensive["attributes"]

            # annual_entity_ref uses direct entity_id
            annual_entity_formula = comp_attributes["annual_entity_ref"]["formula"]
            entity_refs = parser.extract_entity_references(annual_entity_formula)
            assert "sensor.comprehensive_analysis" in entity_refs, "Should extract entity_id in attribute"

    def test_mixed_entity_and_variable_patterns(
        self, parser, reference_patterns_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 6: Mixed entity references and variables with dot notation."""
        sensors = reference_patterns_config["sensors"]
        power_efficiency = sensors["power_efficiency"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test main formula with variables
            main_extracted = parser.extract_variables(power_efficiency["formula"])
            assert "current_power" in main_extracted, "Should extract current_power variable"
            assert "device_efficiency" in main_extracted, "Should extract device_efficiency variable"

            # Test attribute with mixed entity_id and variable dot notation
            attributes = power_efficiency["attributes"]
            battery_formula = attributes["battery_adjusted"]["formula"]

            entity_refs = parser.extract_entity_references(battery_formula)
            extracted_vars = parser.extract_variables(battery_formula)

            assert "sensor.energy_cost_analysis" in entity_refs, "Should extract direct entity reference"
            assert "backup_device" in extracted_vars, "Should extract variable from dot notation"

    def test_dependency_extraction_comprehensive(
        self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 7: Comprehensive dependency extraction."""
        sensors = storage_complex_config["sensors"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test complex formula with multiple pattern types
            enhanced_power = sensors["enhanced_power_analysis"]
            dependencies = parser.extract_dependencies(enhanced_power["formula"])

            # Should include all variables
            assert "device_type" in dependencies, "Should include device_type variable"
            assert "rate_multiplier" in dependencies, "Should include rate_multiplier variable"
            assert "base_consumption" in dependencies, "Should include base_consumption variable"

            # Test efficiency analysis with mathematical operations
            efficiency = sensors["efficiency_analysis"]
            dependencies = parser.extract_dependencies(efficiency["formula"])
            assert "primary_type" in dependencies, "Should include primary_type variable"
            assert "secondary_type" in dependencies, "Should include secondary_type variable"

    def test_name_resolver_with_real_fixtures(self, mock_hass, mock_entity_registry, mock_states, reference_patterns_config):
        """Test NameResolver with real fixture configurations."""
        sensors = reference_patterns_config["sensors"]

        for sensor_id, sensor_config in sensors.items():
            variables = sensor_config.get("variables", {})
            if variables:  # Only test sensors with variables
                resolver = NameResolver(mock_hass, variables)

                class MockNode:
                    def __init__(self, name):
                        self.id = name

                # Test that all variables can be resolved
                for var_name, entity_id in variables.items():
                    resolved_value = resolver.resolve_name(MockNode(var_name))

    def test_or_pattern_variables(self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states):
        """Test Pattern 8: OR pattern variable extraction."""
        sensors = storage_complex_config["sensors"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test OR pattern with variables
            or_pattern = sensors["or_separated_regex"]
            extracted_vars = parser.extract_variables(or_pattern["formula"])
            assert "circuit_pattern" in extracted_vars, "Should extract circuit_pattern variable"
            assert "kitchen_pattern" in extracted_vars, "Should extract kitchen_pattern variable"

    def test_edge_cases_and_complex_patterns(
        self, parser, storage_complex_config, mock_hass, mock_entity_registry, mock_states
    ):
        """Test Pattern 9: Edge cases and complex patterns."""
        sensors = storage_complex_config["sensors"]

        with patch("ha_synthetic_sensors.constants_entities.er.async_get", return_value=mock_entity_registry):
            # Test complex nested patterns
            complex_analysis = sensors["comprehensive_device_analysis"]
            dependencies = parser.extract_dependencies(complex_analysis["formula"])
            # The formula is sum("device_class:power") which extracts device_class and power
            assert "device_class" in dependencies, "Should extract device_class from complex pattern"
            assert "power" in dependencies, "Should extract power from complex pattern"
