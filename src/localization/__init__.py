"""Public immutable localization and internationalization framework."""

from .contracts import (
    FRAMEWORK_VERSION,
    RESOURCE_CONTRACT_VERSION,
    DateOrder,
    DiagnosticSeverity,
    HourCycle,
    LocalizationDiagnostic,
    MeasurementSystem,
    PageDirection,
    ResourceLayer,
    normalize_locale,
)
from .exceptions import (
    FallbackResolutionError,
    FormattingError,
    LocaleError,
    LocalizationError,
    ResourceCompatibilityError,
    ResourceLoadError,
    ResourceRegistrationError,
    TranslationError,
)
from .formatting import LocaleFormatter
from .language import Language, Script
from .loader import LocalizationResourceLoader
from .locale import Culture, CurrencyFormat, DocumentConventions, Locale, Region
from .manager import LocalizationManager
from .metadata import ResourceMetadata
from .pluralization import (
    ENGLISH_PLURAL_RULE,
    PluralCase,
    PluralCondition,
    PluralOperands,
    PluralRule,
)
from .registry import LocalizationRegistry
from .resolver import LocalizationResolver
from .resources import (
    BUILTIN_ENGLISH,
    LocalizationResource,
    TranslationResource,
)
from .terminology import CANONICAL_TERMS, Terminology
from .translation import Translation

__all__ = [
    "BUILTIN_ENGLISH",
    "CANONICAL_TERMS",
    "ENGLISH_PLURAL_RULE",
    "FRAMEWORK_VERSION",
    "RESOURCE_CONTRACT_VERSION",
    "CurrencyFormat",
    "Culture",
    "DateOrder",
    "DiagnosticSeverity",
    "DocumentConventions",
    "FallbackResolutionError",
    "FormattingError",
    "HourCycle",
    "Language",
    "Locale",
    "LocaleError",
    "LocaleFormatter",
    "LocalizationDiagnostic",
    "LocalizationError",
    "LocalizationManager",
    "LocalizationRegistry",
    "LocalizationResolver",
    "LocalizationResource",
    "LocalizationResourceLoader",
    "MeasurementSystem",
    "PageDirection",
    "PluralCase",
    "PluralCondition",
    "PluralOperands",
    "PluralRule",
    "Region",
    "ResourceCompatibilityError",
    "ResourceLayer",
    "ResourceLoadError",
    "ResourceMetadata",
    "ResourceRegistrationError",
    "Script",
    "Terminology",
    "Translation",
    "TranslationResource",
    "TranslationError",
    "normalize_locale",
]
