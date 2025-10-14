"""Configuration management for the Foxhole Stockpiles Client."""

import json
from functools import lru_cache
from pathlib import Path
from typing import Self

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from foxhole_stockpiles.enums.auth_type import AuthType


class KeybindSettings(BaseModel):
    """Settings for keyboard keybinds."""

    key: str | None = Field(description="Key to take a screenshot", default=None)


class ServerSettings(BaseModel):
    """Settings for server connection."""

    url: str = Field(description="API URL", default="https://backend.com/fs/ocr/scan_image")
    auth_type: AuthType | None = Field(
        description="Authentication type (None, BASIC, BEARER)", default=None
    )
    username: str | None = Field(description="Username for basic auth", default=None)
    password: str | None = Field(description="Password for basic auth", default=None)
    token: str | None = Field(description="Token for bearer auth", default=None)

    @model_validator(mode="after")
    def validate_auth_configuration(self) -> Self:
        """Validate that authentication fields match the auth_type.

        Returns:
            The validated model instance

        Raises:
            ValueError: If authentication configuration is invalid
        """
        if self.auth_type == AuthType.BASIC:
            if not self.username or not self.password:
                raise ValueError("Username and password are required when auth_type is BASIC")
            if self.token is not None:
                raise ValueError("Token must be None when auth_type is BASIC")
        elif self.auth_type == AuthType.BEARER:
            if not self.token:
                raise ValueError("Token is required when auth_type is BEARER")
            if self.username is not None or self.password is not None:
                raise ValueError("Username and password must be None when auth_type is BEARER")
        elif self.auth_type is None:
            if self.username is not None or self.password is not None or self.token is not None:
                raise ValueError(
                    "Username, password, and token must be None when auth_type is None"
                )

        return self


class WebhookSettings(BaseModel):
    """Settings for webhook forward auth."""

    token: str | None = Field(description="Webhook forward auth token", default=None)
    header: str | None = Field(description="Header name for webhook token", default=None)

    @model_validator(mode="after")
    def validate_webhook_configuration(self) -> Self:
        """Validate that webhook token and header are both set or both None.

        Returns:
            The validated model instance

        Raises:
            ValueError: If webhook configuration is invalid
        """
        if self.token and not self.header:
            raise ValueError("Header name is required when webhook token is set")
        if self.header and not self.token:
            raise ValueError("Webhook token is required when header name is set")

        return self


class AppSettings(BaseSettings):
    """Main application settings."""

    model_config = SettingsConfigDict(extra="ignore")

    keybind: KeybindSettings = Field(default_factory=KeybindSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    webhook: WebhookSettings = Field(default_factory=WebhookSettings)

    @classmethod
    def from_json(cls, file_path: str = "config.json") -> Self:
        """Read the settings from a JSON file.

        Args:
            file_path: The path to the JSON file

        Returns:
            AppSettings: The settings instance
        """
        config_file = Path(file_path)
        if not config_file.exists():
            # Return default settings if file doesn't exist
            return cls()

        with open(config_file) as f:
            data = json.load(f)

        return cls(**data)

    def save(self, file_path: str = "config.json") -> None:
        """Save the settings to a JSON file.

        Args:
            file_path: The path to the JSON file
        """
        config_file = Path(file_path)

        # Create a dictionary with only the values we want to save
        data = self.model_dump(mode="json")

        with open(config_file, "w") as f:
            json.dump(data, f, indent=2)


@lru_cache
def get_settings() -> AppSettings:
    """Get or create the application settings singleton.

    Returns:
        AppSettings: The application settings instance.
    """
    return AppSettings.from_json()


settings = get_settings()
