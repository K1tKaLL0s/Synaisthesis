from typing import Any

from pydantic import ValidationError

from synaisthesis.config.settings import Settings


class SettingsValidationError(ValueError):
    pass


def validate_settings(data: dict[str, Any]) -> Settings:
    try:
        return Settings.model_validate(data)
    except ValidationError as exc:
        raise SettingsValidationError(str(exc)) from exc
