"""Private immutable configuration for the application-service layer."""

from dataclasses import dataclass


API_VERSION = "1.0.0"
ENGINE_VERSION = "1.1.0"
SUPPORTED_CONTRACT_VERSION = "1.0"


@dataclass(frozen=True, slots=True)
class ApplicationConfiguration:
    """Compatibility configuration shared by facade operations."""

    api_version: str = API_VERSION
    engine_version: str = ENGINE_VERSION
    supported_contract_version: str = SUPPORTED_CONTRACT_VERSION

