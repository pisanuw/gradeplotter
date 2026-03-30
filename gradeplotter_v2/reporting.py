from typing import List
from .models import GradeRecord

def generate_dfw_report(records: List[GradeRecord], course_code: str) -> str:
    """
    Generate a drop/fail/withdraw/repeat report for a course.
    This is a simplified parity version: counts D, F, W, and R grades for the given course_code.
    """
    dfw_grades = {"D", "F", "W", "R"}
    filtered = [r for r in records if r.section.course_code == course_code]
    total = len(filtered)
    dfw = [r for r in filtered if r.grade_raw in dfw_grades]
    report = [
        f"DFW Report for {course_code}",
        f"Total records: {total}",
        f"DFW count: {len(dfw)}",
        f"DFW percent: {100.0 * len(dfw) / total:.2f}%" if total else "DFW percent: N/A",
        "",
        "Breakdown:",
    ]
    for grade in sorted(dfw_grades):
        count = sum(1 for r in dfw if r.grade_raw == grade)
        report.append(f"  {grade}: {count}")
    return "\n".join(report)