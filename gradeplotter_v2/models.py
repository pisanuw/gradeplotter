from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Quarter(Enum):
    AUT = "AUT"
    WIN = "WIN"
    SPR = "SPR"
    SUM = "SUM"


_QUARTER_LOOKUP = {
    "autumn": Quarter.AUT,
    "winter": Quarter.WIN,
    "spring": Quarter.SPR,
    "summer": Quarter.SUM,
}


@dataclass(frozen=True)
class Term:
    year: int
    quarter: Quarter

    @property
    def code(self) -> str:
        return f"{self.year}{self.quarter.value}"

    @property
    def sort_key(self) -> int:
        order = {
            Quarter.WIN: 1,
            Quarter.SPR: 2,
            Quarter.SUM: 3,
            Quarter.AUT: 4,
        }
        return self.year * 10 + order[self.quarter]

    @staticmethod
    def from_csv_value(value: str) -> "Term":
        parts = value.strip().split()
        if len(parts) != 2:
            raise ValueError(f"Invalid Quarter value: {value}")
        quarter = _QUARTER_LOOKUP.get(parts[0].lower())
        if quarter is None:
            raise ValueError(f"Unsupported quarter value: {value}")
        year = int(parts[1])
        return Term(year=year, quarter=quarter)


@dataclass(frozen=True)
class CourseSection:
    term: Term
    curriculum: str
    course_no: str
    section: str
    instructor: str

    @property
    def course_code(self) -> str:
        return f"{self.curriculum}{self.course_no}"

    @property
    def compact_name(self) -> str:
        return (
            f"{self.term.code}-{self.curriculum}{self.course_no}{self.section}-"
            f"{self.instructor}"
        )


@dataclass(frozen=True)
class GradeRecord:
    student_number: str
    section: CourseSection
    grade_raw: str
    major_dept_1: str

    @property
    def numeric_grade(self) -> Optional[float]:
        try:
            return float(self.grade_raw)
        except ValueError:
            return None
