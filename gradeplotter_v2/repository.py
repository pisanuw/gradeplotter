from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from statistics import median
from typing import Iterable, Optional

from .models import GradeRecord


_QUARTER_ORDER = {
    "WIN": 1,
    "SPR": 2,
    "SUM": 3,
    "AUT": 4,
}


def _term_code_sort_key(term_code: str) -> int:
    year = int(term_code[0:4])
    quarter = term_code[4:7]
    return year * 10 + _QUARTER_ORDER[quarter]


@dataclass(frozen=True)
class Query:
    curriculum_pattern: str = ".*"
    instructor_pattern: str = ".*"
    section_pattern: str = ".*"
    after_term_code: Optional[str] = None
    before_term_code: Optional[str] = None


class GradeRepository:
    def __init__(self, records: Iterable[GradeRecord]):
        self.records = list(records)

    def filter_records(self, query: Query) -> list[GradeRecord]:
        curriculum_re = re.compile(query.curriculum_pattern)
        instructor_re = re.compile(query.instructor_pattern)
        section_re = re.compile(query.section_pattern)
        after_key = _term_code_sort_key(query.after_term_code) if query.after_term_code else None
        before_key = _term_code_sort_key(query.before_term_code) if query.before_term_code else None
        filtered: list[GradeRecord] = []
        for record in self.records:
            sec = record.section
            if not curriculum_re.search(sec.curriculum):
                continue
            if not instructor_re.search(sec.instructor):
                continue
            # Legacy behavior applies --sections patterns to compact names.
            if not section_re.search(sec.compact_name):
                continue
            code_key = _term_code_sort_key(sec.term.code)
            if after_key and code_key < after_key:
                continue
            if before_key and code_key >= before_key:
                continue
            filtered.append(record)
        return filtered

    @staticmethod
    def group_numeric_grades_by_section(records: Iterable[GradeRecord]) -> dict[str, list[float]]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for record in records:
            numeric = record.numeric_grade
            if numeric is None:
                continue
            grouped[record.section.compact_name].append(numeric)
        return dict(grouped)

    @staticmethod
    def group_numeric_grades_by_course_term(
        records: Iterable[GradeRecord],
        course_code: str,
        instructor: Optional[str] = None,
    ) -> dict[str, list[float]]:
        grouped: dict[str, list[float]] = defaultdict(list)
        for record in records:
            sec = record.section
            if sec.course_code != course_code:
                continue
            if instructor and sec.instructor != instructor:
                continue
            numeric = record.numeric_grade
            if numeric is None:
                continue
            grouped[sec.term.code].append(numeric)
        return dict(grouped)

    @staticmethod
    def course_medians_by_term(
        records: Iterable[GradeRecord],
        course_code: str,
        instructor: Optional[str] = None,
    ) -> list[tuple[str, float]]:
        grouped = GradeRepository.group_numeric_grades_by_course_term(
            records=records,
            course_code=course_code,
            instructor=instructor,
        )
        points = [(term, median(values)) for term, values in grouped.items()]
        return sorted(points, key=lambda item: _term_code_sort_key(item[0]))

    @staticmethod
    def distinct_courses(records: Iterable[GradeRecord]) -> list[str]:
        return sorted({record.section.course_code for record in records})

    @staticmethod
    def distinct_instructors(records: Iterable[GradeRecord], course_code: str) -> list[str]:
        return sorted(
            {
                record.section.instructor
                for record in records
                if record.section.course_code == course_code
            }
        )
