"""Immutable localization resource packages and built-in English data."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import ResourceLayer, locale_language, normalize_locale
from .exceptions import LocaleError, TranslationError
from .language import Language
from .locale import CurrencyFormat, DocumentConventions, Locale
from .metadata import ResourceMetadata
from .pluralization import ENGLISH_PLURAL_RULE, PluralRule
from .terminology import Terminology
from .translation import Translation


@dataclass(frozen=True, slots=True)
class LocalizationResource:
    """One versioned immutable language, locale, or override package."""

    metadata: ResourceMetadata
    locale_id: str
    layer: ResourceLayer
    translations: tuple[Translation, ...] = ()
    terminology: tuple[Terminology, ...] = ()
    language: Language | None = None
    locale: Locale | None = None
    plural_rule: PluralRule = PluralRule()

    @property
    def name(self) -> str:
        """Return the stable name consumed by the plugin registry."""
        return self.metadata.resource_id

    def __post_init__(self) -> None:
        locale_id = normalize_locale(self.locale_id)
        if self.locale is not None and self.locale.identifier != locale_id:
            raise LocaleError("resource locale definition does not match locale_id")
        if self.language is not None and self.language.code != locale_language(
            locale_id
        ):
            raise LocaleError("resource language does not match locale_id")
        translation_keys = tuple(item.key for item in self.translations)
        term_keys = tuple(item.canonical for item in self.terminology)
        if len(translation_keys) != len(set(translation_keys)):
            raise TranslationError("resource contains duplicate translation keys")
        if len(term_keys) != len(set(term_keys)):
            raise TranslationError("resource contains duplicate terminology keys")
        self.metadata.require_compatible()
        object.__setattr__(self, "locale_id", locale_id)
        object.__setattr__(
            self, "translations", tuple(sorted(self.translations, key=lambda item: item.key))
        )
        object.__setattr__(
            self,
            "terminology",
            tuple(sorted(self.terminology, key=lambda item: item.canonical)),
        )

    def translation(self, key: str) -> Translation | None:
        """Return an exact translation from this resource."""
        return next((item for item in self.translations if item.key == key), None)

    def term(self, canonical: str) -> str | None:
        """Return an exact terminology label from this resource."""
        item = next(
            (item for item in self.terminology if item.canonical == canonical),
            None,
        )
        return item.label if item else None


TranslationResource = LocalizationResource


BUILTIN_ENGLISH = LocalizationResource(
    metadata=ResourceMetadata(
        "teos.builtin.en-us",
        "1.0.0",
        description="Built-in English safety fallback",
    ),
    locale_id="en-US",
    layer=ResourceLayer.BUILTIN,
    language=Language("en", "English", "English"),
    locale=Locale(
        "en-US",
        "en",
        "English (United States)",
        DocumentConventions(currencies=(CurrencyFormat("USD", "$"),)),
    ),
    plural_rule=ENGLISH_PLURAL_RULE,
    translations=(
        Translation.singular("document.course_title", "Course"),
        Translation.singular("document.generated_on", "Generated on {date}"),
        Translation(
            "count.sessions",
            (("one", "{count} session"), ("other", "{count} sessions")),
        ),
    ),
    terminology=tuple(Terminology(term, term) for term in sorted((
        "Assessment",
        "Certificate",
        "Course",
        "Instructor",
        "Lab",
        "Lesson",
        "Module",
        "Quiz",
        "Student",
        "Workshop",
    ))),
)
