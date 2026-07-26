"""Document-generation exception hierarchy."""


class GenerationError(Exception):
    """Base class for document-generation failures."""


class UnsupportedGeneratorError(GenerationError):
    """Raised when no generator supports a requested output format."""


class OutputError(GenerationError):
    """Raised when an output destination is invalid."""


class FileCreationError(OutputError):
    """Raised when physical output cannot be created atomically."""


class AssetEmbeddingError(GenerationError):
    """Raised when a declared asset cannot be loaded or embedded."""


class TemplateMismatchError(GenerationError):
    """Raised when generation inputs disagree with the rendered artifact."""


class MissingResourceError(GenerationError):
    """Raised when an optional encoder dependency is unavailable."""
