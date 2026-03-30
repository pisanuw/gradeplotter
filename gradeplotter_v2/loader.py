from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

from .models import CourseSection, GradeRecord, Term


def _clean(value: str) -> str:
    return value.strip()


def load_grade_records(paths: Iterable[Path]) -> list[GradeRecord]:
    records: list[GradeRecord] = []
    for path in paths:
        with path.open("r", newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                curriculum = _clean(row.get("Curric", ""))
                course_no = _clean(row.get("Course_No", ""))
                section = _clean(row.get("Section", ""))
                instructor = _clean(row.get("Course_Instructor", "")).replace(" ", "")
                if not (curriculum and course_no and section and instructor):
                    continue

                term = Term.from_csv_value(row.get("Quarter", ""))
                grade_raw = _clean(row.get("Grade", ""))
                student_number = _clean(row.get("Student_Number", ""))
                major_dept_1 = _clean(row.get("MajorDept1", ""))
                records.append(
                    GradeRecord(
                        student_number=student_number,
                        section=CourseSection(
                            term=term,
                            curriculum=curriculum,
                            course_no=course_no,
                            section=section,
                            instructor=instructor,
                        ),
                        grade_raw=grade_raw,
                        major_dept_1=major_dept_1,
                    )
                )
    return records
