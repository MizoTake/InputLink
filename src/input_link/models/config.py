"""Configuration models with validation."""

from __future__ import annotations

import ipaddress
from pathlib import Path
from typing import Dict, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from .controller import InputMethod


class ControllerConfig(BaseModel):
    """Individual controller configuration."""

    assigned_number: int = Field(..., ge=1, le=8)
    input_method: InputMethod = Field(default=InputMethod.XINPUT)
    enabled: bool = Field(default=True)
    display_name: Optional[str] = Field(default=None, max_length=100)


class WindowsConfig(BaseModel):
    """Windows-specific configuration."""

    use_vigem: bool = Field(default=True)
    vigem_driver_path: Optional[Path] = Field(default=None)


class MacOSConfig(BaseModel):
    """macOS-specific configuration."""

    use_pygame_virtual: bool = Field(default=True)
    request_accessibility_permissions: bool = Field(default=True)


class PlatformSpecificConfig(BaseModel):
    """Platform-specific configuration options."""

    windows: WindowsConfig = Field(default_factory=WindowsConfig)
    macos: MacOSConfig = Field(default_factory=MacOSConfig)


class SenderConfig(BaseModel):
    """Sender application configuration."""

    receiver_host: str = Field(..., description="IP address or hostname of receiver")
    receiver_port: int = Field(default=8765, ge=1024, le=65535)
    polling_rate: int = Field(default=60, ge=10, le=240, description="Input polling rate in Hz")
    retry_interval: float = Field(default=1.0, ge=0.1, le=30.0)
    max_retry_attempts: int = Field(default=10, ge=1, le=100)
    controllers: Dict[str, ControllerConfig] = Field(default_factory=dict)

    @field_validator("receiver_host")
    @classmethod
    def validate_host(cls, v: str) -> str:
        """Validate host is valid IP address or hostname."""
        v = v.strip()
        if not v:
            raise ValueError("Receiver host cannot be empty")

        # Try to parse as IP address
        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass

        # Validate as hostname (basic check)
        if not all(c.isalnum() or c in ".-_" for c in v):
            raise ValueError("Invalid hostname format")

        return v


class ReceiverConfig(BaseModel):
    """Receiver application configuration."""

    listen_host: str = Field(default="0.0.0.0", description="IP address to bind the server")
    listen_port: int = Field(default=8765, ge=1024, le=65535)
    max_controllers: int = Field(default=4, ge=1, le=8)
    auto_create_virtual: bool = Field(default=True)
    connection_timeout: float = Field(default=30.0, ge=5.0, le=300.0)
    platform_specific: PlatformSpecificConfig = Field(default_factory=PlatformSpecificConfig)

    @field_validator("listen_host")
    @classmethod
    def validate_listen_host(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Listen host cannot be empty")

        # Accept 0.0.0.0 (all interfaces) or valid IP/hostname
        if v == "0.0.0.0":
            return v

        try:
            ipaddress.ip_address(v)
            return v
        except ValueError:
            pass

        if not all(c.isalnum() or c in ".-_" for c in v):
            raise ValueError("Invalid listen hostname format")
        return v


class ConfigModel(BaseModel):
    """Main configuration model."""

    sender_config: SenderConfig
    receiver_config: ReceiverConfig
    debug_logging: bool = Field(default=False)
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")

    @model_validator(mode="after")
    def validate_config_consistency(self) -> ConfigModel:
        """Validate cross-config consistency."""
        # Ensure sender and receiver ports don't conflict if running on same machine
        if hasattr(self.sender_config, "receiver_host"):
            if (self.sender_config.receiver_host in ("127.0.0.1", "localhost") and
                hasattr(self.receiver_config, "listen_port")):
                if self.sender_config.receiver_port != self.receiver_config.listen_port:
                    raise ValueError(
                        f"Port mismatch: sender expects {self.sender_config.receiver_port}, "
                        f"receiver listens on {self.receiver_config.listen_port}",
                    )

        return self

    @classmethod
    def create_default(cls) -> ConfigModel:
        """Create default configuration."""
        return cls(
            sender_config=SenderConfig(receiver_host="127.0.0.1"),
            receiver_config=ReceiverConfig(),
        )

    def save_to_file(self, path: Path) -> None:
        """Save configuration to JSON file."""
        path.write_text(self.model_dump_json(indent=2))

    @classmethod
    def load_from_file(cls, path: Path) -> ConfigModel:
        """Load configuration from JSON file."""
        if not path.exists():
            config = cls.create_default()
            config.save_to_file(path)
            return config

        return cls.model_validate_json(path.read_text())

    model_config = {
        "str_strip_whitespace": True,
        "validate_assignment": True,
        "use_enum_values": True,
    }
