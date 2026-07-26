"""Immutable identity and compatibility metadata for localization resources."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import RESOURCE_CONTRACT_VERSION, require_resource_id
from .exceptions import ResourceCompatibilityError


@dataclass(frozen=True, slots=True)
class ResourceMetadata:
    """Version and compatibility metadata for one resource package."""

    resource_id: str
    version: str
    contract_version: str = RESOURCE_CONTRACT_VERSION
    description: str = ""

    def __post_init__(self) -> None:
        require_resource_id(self.resource_id)
        if re.fullmatch(r"\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?", self.version) is None:
            raise ValueError(f"invalid resource version: {self.version!r}")
        if re.fullmatch(r"\d+\.\d+", self.contract_version) is None:
            raise ValueError(
                f"invalid resource contract version: {self.contract_version!r}"
            )

    def require_compatible(self) -> None:
        """Require exact support for the published resource contract."""
        if self.contract_version != RESOURCE_CONTRACT_VERSION:
            raise ResourceCompatibilityError(
                f"resource {self.resource_id!r} uses contract "
                f"{self.contract_version!r}; supported contract is "
                f"{RESOURCE_CONTRACT_VERSION!r}"
            )
