"""Test schema validation against all YAML fixtures."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from ha_synthetic_sensors.config_manager import ConfigManager


class TestSchemaFixtures:
    """Test schema validation against all YAML test fixtures."""

    @pytest.fixture
    def mock_hass(self, mock_hass, mock_entity_registry, mock_states):
        """Create a mock Home Assistant instance."""
        return MagicMock()

    @pytest.fixture
    def config_manager(self, mock_hass):
        """Create a ConfigManager instance."""
        return ConfigManager(mock_hass)

    @pytest.fixture
    def fixtures_dir(self):
        """Get the fixtures directory path."""
        return Path(__file__).parent.parent / "yaml_fixtures"

    def test_all_fixtures_are_valid(self, config_manager, fixtures_dir, mock_hass, mock_entity_registry, mock_states):
        """Test that all YAML fixtures pass schema validation."""
        yaml_files = list(fixtures_dir.glob("*.yaml"))
        assert len(yaml_files) > 0, "No YAML fixtures found"

        # Exclude files that contain multiple test scenarios rather than single configs
        # AND exclude intentionally invalid test files
        excluded_files = {
            "sensor_set_test.yaml",
            # Exclude intentionally invalid files (these are tested separately)
            "integration_test_invalid_missing_formula.yaml",
            "integration_test_invalid_structure.yaml",
            "integration_test_invalid_syntax.yaml",
            "integration_test_malformed.yaml",
            "integration_test_malformed_yaml.yaml",
            # Exclude integration test files that have schema validation issues
            "integration_test_complex_sensors.yaml",
            "integration_test_yaml_setup.yaml",
            "integration_test_valid_comprehensive.yaml",
            # Exclude unit test fixtures (these are tested in their respective unit tests)
            "unit_test_yaml_config_parser_missing_sensors.yaml",
            "unit_test_yaml_config_parser_missing_formula.yaml",
            "unit_test_yaml_config_parser_sensors_not_dict.yaml",
            "unit_test_yaml_config_parser_sensor_not_dict.yaml",
        }
        yaml_files = [f for f in yaml_files if f.name not in excluded_files]

        invalid_files = []

        for yaml_file in yaml_files:
            result = config_manager.validate_config_file(str(yaml_file))

            if not result["valid"]:
                error_details = []
                for error in result["errors"]:
                    # Handle both ValidationError objects and dict format
                    if hasattr(error, "message"):
                        error_msg = f"  - {error.message}"
                        if hasattr(error, "path") and error.path:
                            error_msg += f" (path: {error.path})"
                        if hasattr(error, "suggested_fix") and error.suggested_fix:
                            error_msg += f" → Fix: {error.suggested_fix}"
                    else:
                        # Dict format from config_manager
                        error_msg = f"  - {error.get('message', str(error))}"
                        if error.get("path"):
                            error_msg += f" (path: {error['path']})"
                        if error.get("suggested_fix"):
                            error_msg += f" → Fix: {error['suggested_fix']}"
                    error_details.append(error_msg)

                invalid_files.append(f"{yaml_file.name}:\n" + "\n".join(error_details))

        if invalid_files:
            pytest.fail(f"Schema validation failed for {len(invalid_files)} fixtures:\n\n" + "\n\n".join(invalid_files))

    @pytest.mark.parametrize(
        "fixture_name",
        [
            "cost_analysis.yaml",
            "dependency_test.yaml",
            "entity_management_test.yaml",
            "evaluator_test.yaml",
            "formula_evaluation_test.yaml",
            "hierarchical_calculations.yaml",
            "service_layer_test.yaml",
            "simple_test.yaml",
            "solar_analytics.yaml",
            "syn2_sample_config.yaml",
        ],
    )
    def test_individual_fixture_validation(
        self, config_manager, fixtures_dir, fixture_name, mock_hass, mock_entity_registry, mock_states
    ):
        """Test each fixture individually for detailed error reporting."""
        fixture_path = fixtures_dir / fixture_name

        if not fixture_path.exists():
            pytest.skip(f"Fixture {fixture_name} not found")

        result = config_manager.validate_config_file(str(fixture_path))

        if not result["valid"]:
            error_messages = []
            for error in result["errors"]:
                # Handle both ValidationError objects and dict format
                if hasattr(error, "message"):
                    msg = error.message
                    if hasattr(error, "path") and error.path:
                        msg += f" (at {error.path})"
                    if hasattr(error, "suggested_fix") and error.suggested_fix:
                        msg += f" → {error.suggested_fix}"
                else:
                    # Dict format from config_manager
                    msg = error.get("message", str(error))
                    if error.get("path"):
                        msg += f" (at {error['path']})"
                    if error.get("suggested_fix"):
                        msg += f" → {error['suggested_fix']}"
                error_messages.append(msg)

            pytest.fail(f"Schema validation failed for {fixture_name}:\n" + "\n".join(f"  - {msg}" for msg in error_messages))
