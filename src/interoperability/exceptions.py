"""Documented failures raised by the interoperability framework."""


class ImportExportError(Exception):
    """Base class for import and export failures."""


class ImportError(ImportExportError):
    """An external representation could not be imported."""


class ExportError(ImportExportError):
    """A public TEOS response could not be exported."""


class FormatError(ImportExportError):
    """An external representation has invalid format or syntax."""


class CompatibilityError(ImportExportError):
    """A requested format or framework version is unsupported."""


class TranslationError(ImportExportError):
    """Values could not be translated across the public API boundary."""
