"""Common contract implemented by TEOS validation stages."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


ValidationInput = TypeVar("ValidationInput")


class Validator(ABC, Generic[ValidationInput]):
    """A validation stage that raises a diagnostic exception on failure."""

    @abstractmethod
    def validate(self, value: ValidationInput) -> None:
        """Validate a value or raise a repository diagnostic."""
