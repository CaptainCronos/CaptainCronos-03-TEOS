"""Typed failures raised by the TEOS localization framework."""


class LocalizationError(Exception):
    """Base class for all localization framework failures."""


class LocaleError(LocalizationError):
    """Raised for invalid or unsupported language and locale definitions."""


class TranslationError(LocalizationError):
    """Raised when a translation resource or interpolation is invalid."""


class ResourceLoadError(LocalizationError):
    """Raised when a localization resource cannot be decoded or constructed."""


class ResourceRegistrationError(LocalizationError):
    """Raised when localization resource registration is ambiguous."""


class ResourceCompatibilityError(LocalizationError):
    """Raised when a resource does not support the framework contract."""


class FormattingError(LocalizationError):
    """Raised when a value cannot be formatted under locale conventions."""


class FallbackResolutionError(LocalizationError):
    """Raised when a locale fallback graph is broken or cyclic."""
