"""Immutable identity and compatibility metadata for theme packages."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import (
    THEME_CONTRACT_VERSION,
    ThemeLayer,
    require_identifier,
    require_semver,
)
from .exceptions import ThemeCompatibilityError


@dataclass(frozen=True, slots=True)
class ThemeMetadata:
    """Stable identity, version, ownership, and compatibility metadata."""

    theme_id: str
    version: str
    layer: ThemeLayer = ThemeLayer.THEME
    contract_version: str = THEME_CONTRACT_VERSION
    description: str = ""

    def __post_init__(self) -> None:
        require_identifier(self.theme_id, label="theme identifier")
        require_semver(self.version)
        if re.fullmatch(r"\d+\.\d+", self.contract_version) is None:
            raise ValueError(
                f"invalid theme contract version: {self.contract_version!r}"
            )

    def require_compatible(self) -> None:
        """Require exact support for the published theme contract."""
        if self.contract_version != THEME_CONTRACT_VERSION:
            raise ThemeCompatibilityError(
                f"theme {self.theme_id!r} uses contract "
                f"{self.contract_version!r}; supported contract is "
                f"{THEME_CONTRACT_VERSION!r}"
            )
