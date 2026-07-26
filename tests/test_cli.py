"""Command parsing, configuration, orchestration, and CLI diagnostics."""

from __future__ import annotations

import io
import json
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.cli.application import CliApplication
from src.cli.commands import CommandName, CommandRequest
from src.cli.configuration import CliConfiguration, load_configuration
from src.cli.context import CliContext, PipelineServices
from src.cli.exceptions import PipelineError, UserInputError
from src.cli.logging import LogLevel, StructuredLogger
from src.cli.main import main
from src.cli.output import OutputWriter
from src.cli.parser import create_parser, parse_arguments
from src.cli.progress import (
    ProgressEvent,
    ProgressState,
    TextProgressReporter,
)
from src.repository.exceptions import RepositoryError
from tests.test_scheduler import compiled_fixture


GENERATED_AT = datetime(2026, 7, 25, 12, tzinfo=timezone.utc)


class RecordingProgress:
    """Collect progress events without affecting application behavior."""

    def __init__(self) -> None:
        self.events: list[ProgressEvent] = []

    def report(self, event: ProgressEvent) -> None:
        """Record one event."""
        self.events.append(event)


class FixtureLoader:
    """Expose a real immutable fixture repository through the loader API."""

    def __init__(self, repository, failure: Exception | None = None) -> None:
        self.repository = repository
        self.failure = failure

    def locate(self, location: str | Path) -> tuple[Path, ...]:
        """Return a deterministic discovery result."""
        return (Path(location).resolve() / "fixture.json",)

    def load(self, location: str | Path):
        """Return the fixture or raise the configured engine failure."""
        if self.failure is not None:
            raise self.failure
        return self.repository


def application(
    tmp_path: Path,
    *,
    failure: Exception | None = None,
) -> tuple[CliApplication, RecordingProgress, io.StringIO, io.StringIO]:
    """Build a CLI application around existing real engine components."""
    compiled, _, _ = compiled_fixture()
    services = PipelineServices(
        repository_loader=FixtureLoader(compiled.source, failure),  # type: ignore[arg-type]
    )
    stdout = io.StringIO()
    stderr = io.StringIO()
    progress = RecordingProgress()
    context = CliContext(
        configuration=CliConfiguration(
            repository=tmp_path,
            output_directory=tmp_path / "output",
            progress=False,
        ),
        logger=StructuredLogger(stderr, LogLevel.INFO),
        progress=progress,
        output=OutputWriter(stdout, stderr),
        services=services,
        clock=lambda: GENERATED_AT,
    )
    return CliApplication(context), progress, stdout, stderr


def test_parser_exposes_every_command_and_options() -> None:
    """Arguments become an immutable command request and explicit overrides."""
    invocation = parse_arguments(
        [
            "--repository",
            "example",
            "--renderer",
            "html",
            "--timing",
            "render",
        ]
    )

    assert invocation.request == CommandRequest(CommandName.RENDER)
    assert dict(invocation.overrides) == {
        "repository": Path("example"),
        "renderer": "html",
        "timing": True,
    }
    assert set(create_parser()._subparsers._group_actions[0].choices) == {
        command.value for command in CommandName
    }


def test_configuration_precedence_extensions_and_immutability(
    tmp_path: Path,
) -> None:
    """CLI values override environment and files while extensions survive."""
    source = tmp_path / "teos.json"
    source.write_text(
        json.dumps(
            {
                "repository": "from-file",
                "renderer": "html",
                "timing": False,
                "future_option": {"enabled": True},
            }
        ),
        encoding="utf-8",
    )

    configuration = load_configuration(
        source,
        overrides={"renderer": "markdown"},
        environ={"TEOS_REPOSITORY": "from-environment", "TEOS_TIMING": "yes"},
    )

    assert configuration.repository == Path("from-environment")
    assert configuration.renderer == "markdown"
    assert configuration.timing is True
    assert configuration.extensions == (
        ("future_option", (("enabled", True),)),
    )
    with pytest.raises(FrozenInstanceError):
        configuration.renderer = "html"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("command", "last_stage", "result"),
    (
        (CommandName.VALIDATE, "validation", "repository valid"),
        (CommandName.COMPILE, "compilation", "repository compiled"),
        (CommandName.SCHEDULE, "scheduling", "repository scheduled"),
        (CommandName.RENDER, "rendering", "schedule rendered"),
        (CommandName.GENERATE, "generation", "document generated"),
        (CommandName.BUILD, "generation", "document generated"),
    ),
)
def test_pipeline_commands_execute_only_the_required_prefix(
    tmp_path: Path,
    command: CommandName,
    last_stage: str,
    result: str,
) -> None:
    """Each pipeline command stops after its declared engine stage."""
    cli, progress, stdout, _ = application(tmp_path)

    cli.execute(CommandRequest(command))

    completed = [
        event.stage
        for event in progress.events
        if event.state is ProgressState.COMPLETED
    ]
    assert completed[-2:] == [last_stage, "completion"]
    assert result in stdout.getvalue()
    if command in {CommandName.GENERATE, CommandName.BUILD}:
        assert (tmp_path / "output" / "course-schedule.md").is_file()


def test_pipeline_failure_names_stage_and_preserves_cause(
    tmp_path: Path,
) -> None:
    """Engine exceptions remain chained beneath a stage-specific CLI error."""
    cause = RepositoryError("broken repository")
    cli, progress, _, _ = application(tmp_path, failure=cause)

    with pytest.raises(PipelineError) as captured:
        cli.execute(CommandRequest(CommandName.VALIDATE))

    assert captured.value.stage == "validation"
    assert captured.value.cause is cause
    assert progress.events[-1].state is ProgressState.FAILED


def test_progress_and_structured_logging_output() -> None:
    """Progress and logs remain distinct and honor thresholds."""
    progress_stream = io.StringIO()
    reporter = TextProgressReporter(progress_stream)
    reporter.report(ProgressEvent("validation", ProgressState.STARTED))
    reporter.report(
        ProgressEvent("validation", ProgressState.FAILED, "invalid schema")
    )
    assert progress_stream.getvalue().splitlines() == [
        "[started] validation",
        "[failed] validation: invalid schema",
    ]

    log_stream = io.StringIO()
    logger = StructuredLogger(log_stream, LogLevel.INFO)
    logger.debug("hidden", "not shown")
    logger.warning("repository.warning", "attention", count=2)
    assert log_stream.getvalue() == (
        "level=warning event=repository.warning "
        "message='attention' count=2\n"
    )


def test_invalid_command_help_and_version_output(capsys) -> None:
    """Syntax, generated help, and the version command are stable."""
    with pytest.raises(UserInputError):
        parse_arguments(["unknown"])
    with pytest.raises(SystemExit) as help_exit:
        create_parser().parse_args(["--help"])
    assert help_exit.value.code == 0
    assert "validate" in capsys.readouterr().out

    stdout = io.StringIO()
    stderr = io.StringIO()
    assert main(["version"], stdout=stdout, stderr=stderr, environ={}) == 0
    assert stdout.getvalue() == "teos 1.1.0\n"
    assert stderr.getvalue() == ""


def test_main_reports_invalid_command_without_traceback() -> None:
    """Process-level input failures receive a concise stable exit status."""
    stdout = io.StringIO()
    stderr = io.StringIO()

    status = main(["unknown"], stdout=stdout, stderr=stderr, environ={})

    assert status == 2
    assert stdout.getvalue() == ""
    assert "invalid choice" in stderr.getvalue()
    assert "Traceback" not in stderr.getvalue()
