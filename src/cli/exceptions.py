"""CLI-specific failures and stable process exit status mapping."""

from __future__ import annotations


class CliError(Exception):
    """Base class for failures owned by the command-line boundary."""

    exit_code = 1


class ConfigurationError(CliError):
    """Operational configuration is absent, malformed, or contradictory."""

    exit_code = 2


class CommandError(CliError):
    """A recognized command cannot be completed as requested."""

    exit_code = 3


class PipelineError(CliError):
    """An existing engine stage failed while the CLI was coordinating it."""

    exit_code = 4

    def __init__(self, stage: str, cause: Exception) -> None:
        self.stage = stage
        self.cause = cause
        super().__init__(f"{stage} failed: {cause}")


class OutputError(CliError):
    """The CLI could not present a result or diagnostic."""

    exit_code = 5


class UserInputError(CliError):
    """Command syntax or a user-supplied value is invalid."""

    exit_code = 2
