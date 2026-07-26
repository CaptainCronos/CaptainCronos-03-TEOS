"""Immutable language and script definitions."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .contracts import PageDirection
from .exceptions import LocaleError


@dataclass(frozen=True, slots=True)
class Script:
    """A writing system and its default page flow."""

    code: str
    name: str = ""
    direction: PageDirection = PageDirection.LEFT_TO_RIGHT

    def __post_init__(self) -> None:
        code = self.code.title()
        if re.fullmatch(r"[A-Z][a-z]{3}", code) is None:
            raise LocaleError(f"invalid script code: {self.code!r}")
        object.__setattr__(self, "code", code)


@dataclass(frozen=True, slots=True)
class Language:
    """One language supported by a localization resource."""

    code: str
    name: str
    native_name: str
    script: Script | str = "Latn"
    direction: PageDirection = PageDirection.LEFT_TO_RIGHT

    def __post_init__(self) -> None:
        code = self.code.lower()
        script = (
            self.script
            if isinstance(self.script, Script)
            else Script(self.script, direction=self.direction)
        )
        if re.fullmatch(r"[a-z]{2,3}", code) is None:
            raise LocaleError(f"invalid language code: {self.code!r}")
        if not self.name.strip() or not self.native_name.strip():
            raise LocaleError("language names cannot be empty")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "script", script)
