"""Process entry point for the TEOS command-line interface."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from typing import TextIO

from .application import CliApplication
from .configuration import load_configuration
from .context import CliContext, PipelineServices
from .exceptions import CliError, PipelineError
from .logging import StructuredLogger, logging_threshold
from .output import OutputWriter
from .parser import parse_arguments
from .progress import TextProgressReporter


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    environ: Mapping[str, str] | None = None,
    services: PipelineServices | None = None,
) -> int:
    """Run one CLI invocation and return its process exit status."""
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr
    arguments = tuple(sys.argv[1:] if argv is None else argv)
    writer = OutputWriter(
        output_stream,
        error_stream,
        json_output="--json" in arguments,
    )
    try:
        parsed = parse_arguments(arguments)
        configuration = load_configuration(
            parsed.configuration_path,
            overrides=dict(parsed.overrides),
            environ=environ,
        )
        writer = OutputWriter(
            output_stream,
            error_stream,
            json_output=configuration.json_output,
        )
        logger = StructuredLogger(
            error_stream,
            logging_threshold(
                configuration.logging_level,
                verbose=configuration.verbose,
                debug=configuration.debug,
            ),
        )
        progress = TextProgressReporter(
            error_stream, enabled=configuration.progress
        )
        context_values = {
            "configuration": configuration,
            "logger": logger,
            "progress": progress,
            "output": writer,
        }
        if services is not None:
            context_values["services"] = services
        CliApplication(CliContext(**context_values)).execute(parsed.request)
        return 0
    except PipelineError as error:
        details: dict[str, object] = {"stage": error.stage}
        cause = error.cause
        if hasattr(cause, "source") and getattr(cause, "source") is not None:
            details["source"] = getattr(cause, "source")
        if hasattr(cause, "path") and getattr(cause, "path"):
            details["location"] = ".".join(
                str(part) for part in getattr(cause, "path")
            )
        writer.diagnostic(str(error), details=details)
        return error.exit_code
    except CliError as error:
        writer.diagnostic(str(error))
        return error.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
