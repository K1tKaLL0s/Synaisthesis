from pathlib import Path

import pytest

from synaisthesis.config.loaders import load_settings
from synaisthesis.config.settings import Settings
from synaisthesis.config.validation import SettingsValidationError, validate_settings

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIGS_DIR = REPO_ROOT / "configs"


def test_load_settings_reads_default_yaml():
    data = load_settings(CONFIGS_DIR / "default.yaml")
    assert data["platform"]["environment"] == "development"
    assert data["platform"]["api_port"] == 8000


def test_load_settings_reads_test_yaml():
    data = load_settings(CONFIGS_DIR / "test.yaml")
    assert data["platform"]["environment"] == "test"


def test_load_settings_missing_file_raises():
    with pytest.raises(FileNotFoundError):
        load_settings(CONFIGS_DIR / "does_not_exist.yaml")


def test_validate_settings_accepts_default_config():
    settings = validate_settings(load_settings(CONFIGS_DIR / "default.yaml"))
    assert isinstance(settings, Settings)
    assert settings.platform.environment == "development"
    assert settings.platform.api_port == 8000
    assert settings.platform.workspace_root == Path("workspace")


def test_validate_settings_rejects_unknown_key():
    data = load_settings(CONFIGS_DIR / "default.yaml")
    data["platform"]["unknown_field"] = "x"
    with pytest.raises(SettingsValidationError):
        validate_settings(data)


def test_validate_settings_rejects_out_of_range_port():
    data = load_settings(CONFIGS_DIR / "default.yaml")
    data["platform"]["api_port"] = 70000
    with pytest.raises(SettingsValidationError):
        validate_settings(data)


def test_validate_settings_rejects_invalid_log_level():
    data = load_settings(CONFIGS_DIR / "default.yaml")
    data["platform"]["log_level"] = "VERBOSE"
    with pytest.raises(SettingsValidationError):
        validate_settings(data)


def test_validate_settings_rejects_missing_section():
    with pytest.raises(SettingsValidationError):
        validate_settings({})


def test_validate_settings_rejects_wrong_type():
    data = load_settings(CONFIGS_DIR / "default.yaml")
    data["platform"]["api_port"] = "not-a-port"
    with pytest.raises(SettingsValidationError):
        validate_settings(data)
