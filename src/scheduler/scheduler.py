"""Deterministic orchestration from compiled curriculum to execution plans."""

from __future__ import annotations

import heapq
from dataclasses import dataclass

from src.compiler import (
    CompiledCourse,
    CompiledInstructionalUnit,
    CompiledRepository,
    CompiledSession,
)
from src.models import AcademicCalendar, InstitutionProfile, Session

from .calendar import SchedulingCalendar
from .exceptions import SchedulingInputError
from .placement import Placement
from .schedule import InstitutionSchedule
from .scheduled_course import ScheduledCourse
from .scheduled_instructional_unit import ScheduledInstructionalUnit
from .scheduled_repository import ScheduledRepository
from .scheduled_session import ScheduledSession


SessionKey = tuple[str, str]


def _session_key(session: Session) -> SessionKey:
    return (str(session.teos_id), session.teos_version)


@dataclass(frozen=True, slots=True)
class SchedulingContext:
    """Select one institution profile and calendar from a compilation."""

    institution_profile: InstitutionProfile
    academic_calendar: AcademicCalendar


class Scheduler:
    """Place compiled Sessions in deterministic eligible calendar slots."""

    def schedule(
        self,
        compiled: CompiledRepository,
        institution_profile: InstitutionProfile,
        academic_calendar: AcademicCalendar,
    ) -> InstitutionSchedule:
        """Produce one immutable institution schedule."""
        self._require_compiled_inputs(
            compiled, institution_profile, academic_calendar
        )
        calendar = SchedulingCalendar(
            institution_profile, academic_calendar
        )
        ordered, predecessors = self._ordered_sessions(compiled)
        placements: dict[SessionKey, ScheduledSession] = {}
        occupied: set[tuple[object, ...]] = set()
        unscheduled: list[CompiledSession] = []
        next_slot = 0
        for compiled_session in ordered:
            key = _session_key(compiled_session.source)
            if any(parent not in placements for parent in predecessors[key]):
                unscheduled.append(compiled_session)
                continue
            selected_index = next(
                (
                    index
                    for index in range(next_slot, len(calendar.slots))
                    if calendar.slots[index].accepts(compiled_session.source)
                    and self._time_key(
                        calendar.slots[index].placement
                    )
                    not in occupied
                ),
                None,
            )
            if selected_index is None:
                unscheduled.append(compiled_session)
                continue
            scheduled = ScheduledSession(
                source=compiled_session,
                placement=calendar.slots[selected_index].placement,
            )
            placements[key] = scheduled
            occupied.add(self._time_key(scheduled.placement))
            next_slot = selected_index + 1

        sessions = tuple(
            placements[key]
            for key in (_session_key(item.source) for item in ordered)
            if key in placements
        )
        courses = self._scheduled_courses(compiled, placements)
        return InstitutionSchedule(
            source=compiled,
            institution_profile=institution_profile,
            academic_calendar=academic_calendar,
            courses=courses,
            sessions=sessions,
            unscheduled_sessions=tuple(unscheduled),
        )

    def schedule_repository(
        self,
        compiled: CompiledRepository,
        contexts: tuple[SchedulingContext, ...],
    ) -> ScheduledRepository:
        """Produce independent schedules for every declared context."""
        if not contexts:
            raise SchedulingInputError(
                "at least one scheduling context is required"
            )
        schedules = tuple(
            self.schedule(
                compiled,
                context.institution_profile,
                context.academic_calendar,
            )
            for context in contexts
        )
        return ScheduledRepository(compiled, schedules)

    @staticmethod
    def _time_key(placement: Placement) -> tuple[object, ...]:
        calendar_date = placement.calendar_date
        period = placement.instructional_period
        if period is not None:
            return (calendar_date, period.instructional_period_id)
        pattern = placement.meeting_pattern
        return (calendar_date, pattern.start_time, pattern.end_time)

    @staticmethod
    def _require_compiled_inputs(
        compiled: CompiledRepository,
        profile: InstitutionProfile,
        calendar: AcademicCalendar,
    ) -> None:
        objects = tuple(compiled.source.registry)
        if not any(item is profile for item in objects):
            raise SchedulingInputError(
                "institution profile must come from compiled repository"
            )
        if not any(item is calendar for item in objects):
            raise SchedulingInputError(
                "academic calendar must come from compiled repository"
            )

    def _ordered_sessions(
        self, compiled: CompiledRepository
    ) -> tuple[
        tuple[CompiledSession, ...],
        dict[SessionKey, set[SessionKey]],
    ]:
        by_key = {
            _session_key(item.source): item for item in compiled.sessions
        }
        rank: dict[SessionKey, int] = {}
        declarations: list[SessionKey] = []
        for course in self._courses_in_dependency_order(compiled):
            for unit in course.instructional_units:
                compiled_unit = self._compiled_unit(compiled, unit.teos_id, unit.teos_version)
                declarations.extend(
                    _session_key(session)
                    for session in compiled_unit.sessions
                )
        declarations.extend(
            _session_key(session) for session in compiled.session_order
        )
        for key in declarations:
            if key not in rank:
                rank[key] = len(rank)

        predecessors: dict[SessionKey, set[SessionKey]] = {
            key: set() for key in by_key
        }
        successors: dict[SessionKey, set[SessionKey]] = {
            key: set() for key in by_key
        }

        def precedes(first: SessionKey, second: SessionKey) -> None:
            if first == second:
                return
            predecessors[second].add(first)
            successors[first].add(second)

        for session in compiled.sessions:
            current = _session_key(session.source)
            for prerequisite in session.prerequisite_sessions:
                precedes(_session_key(prerequisite), current)
            for dependent in session.dependent_sessions:
                precedes(current, _session_key(dependent))
        for unit in compiled.instructional_units:
            keys = tuple(_session_key(item) for item in unit.sessions)
            for first, second in zip(keys, keys[1:]):
                precedes(first, second)
            if keys:
                for prerequisite_unit in (
                    unit.prerequisite_instructional_units
                ):
                    prerequisite = self._compiled_unit(
                        compiled,
                        prerequisite_unit.teos_id,
                        prerequisite_unit.teos_version,
                    )
                    prerequisite_keys = tuple(
                        _session_key(item)
                        for item in prerequisite.sessions
                    )
                    if prerequisite_keys:
                        precedes(prerequisite_keys[-1], keys[0])
        for course in self._courses_in_dependency_order(compiled):
            unit_session_keys = tuple(
                tuple(
                    _session_key(session)
                    for session in self._compiled_unit(
                        compiled, unit.teos_id, unit.teos_version
                    ).sessions
                )
                for unit in course.instructional_units
            )
            nonempty = tuple(keys for keys in unit_session_keys if keys)
            for first, second in zip(nonempty, nonempty[1:]):
                precedes(first[-1], second[0])
            current_keys = tuple(key for keys in nonempty for key in keys)
            if current_keys:
                for prerequisite_course in course.prerequisite_courses:
                    prerequisite = self._compiled_course(
                        compiled,
                        prerequisite_course.teos_id,
                        prerequisite_course.teos_version,
                    )
                    prerequisite_keys = self._course_session_keys(
                        compiled, prerequisite
                    )
                    if prerequisite_keys:
                        precedes(prerequisite_keys[-1], current_keys[0])

        indegree = {
            key: len(parents) for key, parents in predecessors.items()
        }
        ready = [
            (rank[key], key)
            for key, degree in indegree.items()
            if degree == 0
        ]
        heapq.heapify(ready)
        ordered_keys: list[SessionKey] = []
        while ready:
            _, key = heapq.heappop(ready)
            ordered_keys.append(key)
            for child in sorted(
                successors[key], key=lambda item: (rank[item], item)
            ):
                indegree[child] -= 1
                if indegree[child] == 0:
                    heapq.heappush(ready, (rank[child], child))
        if len(ordered_keys) != len(by_key):
            raise SchedulingInputError(
                "declared curriculum sequence contradicts dependency ordering"
            )
        return tuple(by_key[key] for key in ordered_keys), predecessors

    def _scheduled_courses(
        self,
        compiled: CompiledRepository,
        placements: dict[SessionKey, ScheduledSession],
    ) -> tuple[ScheduledCourse, ...]:
        result: list[ScheduledCourse] = []
        for course in self._courses_in_dependency_order(compiled):
            units: list[ScheduledInstructionalUnit] = []
            for unit_source in course.instructional_units:
                unit = self._compiled_unit(
                    compiled,
                    unit_source.teos_id,
                    unit_source.teos_version,
                )
                units.append(
                    ScheduledInstructionalUnit(
                        source=unit,
                        sessions=tuple(
                            placements[_session_key(session)]
                            for session in unit.sessions
                            if _session_key(session) in placements
                        ),
                    )
                )
            result.append(
                ScheduledCourse(
                    source=course,
                    instructional_units=tuple(units),
                )
            )
        return tuple(result)

    def _courses_in_dependency_order(
        self, compiled: CompiledRepository
    ) -> tuple[CompiledCourse, ...]:
        return tuple(
            self._compiled_course(
                compiled, course.teos_id, course.teos_version
            )
            for course in compiled.course_order
        )

    def _course_session_keys(
        self,
        compiled: CompiledRepository,
        course: CompiledCourse,
    ) -> tuple[SessionKey, ...]:
        return tuple(
            _session_key(session)
            for unit in course.instructional_units
            for session in self._compiled_unit(
                compiled, unit.teos_id, unit.teos_version
            ).sessions
        )

    @staticmethod
    def _compiled_unit(
        compiled: CompiledRepository,
        identifier: object,
        version: str,
    ) -> CompiledInstructionalUnit:
        return next(
            item
            for item in compiled.instructional_units
            if item.source.teos_id == identifier
            and item.source.teos_version == version
        )

    @staticmethod
    def _compiled_course(
        compiled: CompiledRepository,
        identifier: object,
        version: str,
    ) -> CompiledCourse:
        return next(
            item
            for item in compiled.courses
            if item.source.teos_id == identifier
            and item.source.teos_version == version
        )


def schedule_repository(
    compiled: CompiledRepository,
    contexts: tuple[SchedulingContext, ...],
) -> ScheduledRepository:
    """Schedule a compilation for one or more institution contexts."""
    return Scheduler().schedule_repository(compiled, contexts)
