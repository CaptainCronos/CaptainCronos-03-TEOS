"""Argument parser construction for the TEOS command model."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from .commands import CommandName, CommandRequest
from .exceptions import UserInputError


class CliArgumentParser(argparse.ArgumentParser):
    """Argument parser that reports syntax failures through the CLI hierarchy."""

    def error(self, message: str) -> None:
        """Raise a user-input diagnostic instead of terminating internally."""
        raise UserInputError(message)


@dataclass(frozen=True, slots=True)
class ParsedInvocation:
    """Parsed command plus configuration source and explicit overrides."""

    request: CommandRequest
    configuration_path: Path | None
    overrides: tuple[tuple[str, Any], ...]


def create_parser() -> CliArgumentParser:
    """Create the complete deterministic TEOS argument parser."""
    parser = CliArgumentParser(
        prog="teos",
        description="Technical Education Operating System command line",
    )
    parser.add_argument("--config", type=Path, help="JSON configuration file")
    parser.add_argument(
        "--repository", type=Path, help="repository file or directory"
    )
    parser.add_argument(
        "--output",
        type=Path,
        dest="output_directory",
        help="generated artifact directory",
    )
    parser.add_argument(
        "--renderer",
        choices=("docx", "pdf", "html", "markdown"),
        help="rendering format",
    )
    parser.add_argument(
        "--generator",
        choices=("docx", "pdf", "html", "markdown"),
        help="document generator format",
    )
    parser.add_argument(
        "--institution-profile", help="institution profile UUID"
    )
    parser.add_argument(
        "--institution-profile-version", help="exact profile version"
    )
    parser.add_argument("--academic-calendar", help="academic calendar UUID")
    parser.add_argument(
        "--academic-calendar-version", help="exact calendar version"
    )
    parser.add_argument(
        "--log-level",
        dest="logging_level",
        choices=("debug", "info", "warning", "error"),
    )
    parser.add_argument(
        "--verbose", action="store_true", default=None, help="verbose logs"
    )
    parser.add_argument(
        "--debug", action="store_true", default=None, help="debug logs"
    )
    parser.add_argument(
        "--timing",
        action="store_true",
        default=None,
        help="include stage timing",
    )
    parser.add_argument(
        "--no-progress",
        action="store_false",
        dest="progress",
        default=None,
        help="disable progress output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        default=None,
        help="emit machine-readable results",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    for name in (
        CommandName.VALIDATE,
        CommandName.COMPILE,
        CommandName.SCHEDULE,
        CommandName.RENDER,
        CommandName.GENERATE,
        CommandName.BUILD,
        CommandName.INFO,
        CommandName.VERSION,
        CommandName.DOCTOR,
    ):
        subcommands.add_parser(name.value, help=f"{name.value} TEOS inputs")
    list_parser = subcommands.add_parser(
        CommandName.LIST.value, help="list available components"
    )
    list_parser.add_argument(
        "target",
        nargs="?",
        choices=("all", "renderers", "generators"),
        default="all",
    )
    return parser


def parse_arguments(argv: Sequence[str] | None = None) -> ParsedInvocation:
    """Parse arguments into immutable command and configuration values."""
    namespace = create_parser().parse_args(argv)
    values = vars(namespace)
    request = CommandRequest(
        CommandName(values.pop("command")), values.pop("target", None)
    )
    configuration_path = values.pop("config")
    overrides = tuple(
        sorted(
            (
                (key, value)
                for key, value in values.items()
                if value is not None
            ),
            key=lambda item: item[0],
        )
    )
    return ParsedInvocation(request, configuration_path, overrides)
