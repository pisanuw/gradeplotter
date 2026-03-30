from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .loader import load_grade_records
from .rendering import render_legacy_style_histogram, render_multiyear_trend
from .repository import GradeRepository, Query


@dataclass(frozen=True)
class GenerationOptions:
    input_files: list[Path]
    output_root: Path
    curriculum_pattern: str = "CSS"
    instructor_pattern: str = ".*"
    section_pattern: str = ".*"
    after_term_code: Optional[str] = None
    before_term_code: Optional[str] = None
    include_histograms: bool = True
    include_multiyear: bool = True
    include_instructor_multiyear: bool = False
    dept_restrictions: bool = True
    min_sections_for_multiyear: int = 10
    combine_sections: bool = False
    combo_instructor: bool = False
    dfw_report: Optional[str] = None


def _section_filename_parts(compact_name: str) -> tuple[str, str, str, str, str, str]:
    # Format: YYYYQTR-CURRICNOSECTION-INSTRUCTOR
    left, instructor = compact_name.split("-", 1)
    instructor = instructor.split("-", 1)[1]
    year = left[0:4]
    quarter = left[4:7]
    mid = compact_name.split("-")[1]
    curriculum = ""
    number = ""
    section = ""
    state = "curr"
    for ch in mid:
        if state == "curr" and ch.isalpha():
            curriculum += ch
            continue
        if ch.isdigit():
            state = "num"
            number += ch
            continue
        state = "sec"
        section += ch
    return year, quarter, curriculum, number, section, instructor


def _copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)



def generate_artifacts(options: GenerationOptions) -> dict:
    records = load_grade_records(options.input_files)
    repo = GradeRepository(records)
    filtered = repo.filter_records(
        Query(
            curriculum_pattern=options.curriculum_pattern,
            instructor_pattern=options.instructor_pattern,
            section_pattern=options.section_pattern,
            after_term_code=options.after_term_code,
            before_term_code=options.before_term_code,
        )
    )

    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_root = options.output_root / "runs" / run_id
    artifacts: list[dict] = []

    # DFW Report mode
    if options.dfw_report:
        from .reporting import generate_dfw_report
        dfw_path = run_root / "dfwreport" / f"{options.dfw_report}.txt"
        dfw_path.parent.mkdir(parents=True, exist_ok=True)
        report = generate_dfw_report(filtered, options.dfw_report)
        with open(dfw_path, "w", encoding="utf-8") as f:
            f.write(report)
        artifacts.append({
            "type": "dfw_report",
            "id": options.dfw_report,
            "path": str(dfw_path.relative_to(options.output_root)),
        })

    if options.include_histograms:
        if options.combo_instructor:
            # Group by instructor, then by course, then combine all sections for each instructor+course
            from collections import defaultdict
            instructor_course_map = defaultdict(lambda: defaultdict(list))
            for record in filtered:
                instr = record.section.instructor or "000NoInstructor"
                course = record.section.course_code
                instructor_course_map[instr][course].append(record)
            for instr, course_map in instructor_course_map.items():
                for course, records_group in course_map.items():
                    numerical = [r.numeric_grade for r in records_group if r.numeric_grade is not None]
                    non_numerical = [r.grade_raw for r in records_group if r.numeric_grade is None]
                    if not numerical and not non_numerical:
                        continue
                    filename = f"combo-{course}-{instr}.png"
                    title = f"{course} (All Sections) {instr}"
                    by_instructor_path = run_root / "byInstructor" / instr / filename
                    by_course_path = run_root / "byCourse" / course / filename
                    render_legacy_style_histogram(
                        numerical_grades=numerical,
                        non_numerical_grades=non_numerical,
                        title=title,
                        output_path=by_instructor_path,
                    )
                    _copy_file(by_instructor_path, by_course_path)
                    artifacts.append(
                        {
                            "type": "combo_instructor_histogram",
                            "id": f"{course}-{instr}",
                            "path": str(by_instructor_path.relative_to(options.output_root)),
                            "copies": [str(by_course_path.relative_to(options.output_root))],
                            "count": len(records_group),
                        }
                    )
        elif options.combine_sections:
            # Group by course, combine all sections for each course
            from collections import defaultdict
            course_map = defaultdict(list)
            for record in filtered:
                course = record.section.course_code
                course_map[course].append(record)
            for course, records_group in course_map.items():
                numerical = [r.numeric_grade for r in records_group if r.numeric_grade is not None]
                non_numerical = [r.grade_raw for r in records_group if r.numeric_grade is None]
                if not numerical and not non_numerical:
                    continue
                filename = f"combo-{course}.png"
                title = f"{course} (All Sections)"
                by_course_path = run_root / "byCourse" / course / filename
                render_legacy_style_histogram(
                    numerical_grades=numerical,
                    non_numerical_grades=non_numerical,
                    title=title,
                    output_path=by_course_path,
                )
                artifacts.append(
                    {
                        "type": "combo_histogram",
                        "id": course,
                        "path": str(by_course_path.relative_to(options.output_root)),
                        "count": len(records_group),
                    }
                )
        else:
            section_map: dict[str, list] = {}
            for record in filtered:
                section_map.setdefault(record.section.compact_name, []).append(record)

            for section_name, section_records in section_map.items():
                numerical = [r.numeric_grade for r in section_records if r.numeric_grade is not None]
                non_numerical = [r.grade_raw for r in section_records if r.numeric_grade is None]
                if not numerical and not non_numerical:
                    continue

                year, quarter, curriculum, number, section, instructor = _section_filename_parts(section_name)
                filename = f"{year}-{quarter}-{curriculum}-{number}-{section}-{instructor}.png"
                title = f"{year} {quarter} {curriculum} {number} {section} {instructor}"

                by_year_path = run_root / "byYear" / f"{year}{quarter}" / filename
                by_instructor_path = run_root / "byInstructor" / instructor / filename
                by_course_path = run_root / "byCourse" / f"{curriculum}{number}" / filename

                render_legacy_style_histogram(
                    numerical_grades=numerical,
                    non_numerical_grades=non_numerical,
                    title=title,
                    output_path=by_year_path,
                )
                _copy_file(by_year_path, by_instructor_path)
                _copy_file(by_year_path, by_course_path)

                artifacts.append(
                    {
                        "type": "section_histogram",
                        "id": section_name,
                        "path": str(by_year_path.relative_to(options.output_root)),
                        "copies": [
                            str(by_instructor_path.relative_to(options.output_root)),
                            str(by_course_path.relative_to(options.output_root)),
                        ],
                        "count": len(section_records),
                    }
                )

    if options.include_multiyear:
        courses = repo.distinct_courses(filtered)
        for course_code in courses:
            section_count = len({r.section.compact_name for r in filtered if r.section.course_code == course_code})
            if options.dept_restrictions and section_count < options.min_sections_for_multiyear:
                continue

            points = repo.course_medians_by_term(filtered, course_code=course_code)
            if len(points) < 2:
                continue
            path = run_root / "stats_per_course" / f"{course_code}.png"
            render_multiyear_trend(points, title=f"{course_code} Median Grades", output_path=path)
            artifacts.append(
                {
                    "type": "course_multiyear",
                    "id": course_code,
                    "path": str(path.relative_to(options.output_root)),
                    "points": len(points),
                    "sections": section_count,
                }
            )

            if options.include_instructor_multiyear:
                instructors = repo.distinct_instructors(filtered, course_code)
                for instructor in instructors:
                    ipoints = repo.course_medians_by_term(
                        filtered,
                        course_code=course_code,
                        instructor=instructor,
                    )
                    if len(ipoints) < 2:
                        continue
                    name = f"{course_code}-{instructor}"
                    ipath = run_root / "byCourse" / course_code / f"{name}.png"
                    instructor_copy_path = run_root / "byInstructor" / instructor / f"{name}.png"
                    render_multiyear_trend(
                        ipoints,
                        title=f"{course_code} Median Grades for {instructor}",
                        output_path=ipath,
                    )
                    _copy_file(ipath, instructor_copy_path)
                    artifacts.append(
                        {
                            "type": "instructor_multiyear",
                            "id": name,
                            "path": str(ipath.relative_to(options.output_root)),
                            "copy": str(instructor_copy_path.relative_to(options.output_root)),
                            "points": len(ipoints),
                        }
                    )

    run_root.mkdir(parents=True, exist_ok=True)
    manifest = {
        "run_id": run_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": [str(p) for p in options.input_files],
        "options": {
            "curriculum_pattern": options.curriculum_pattern,
            "instructor_pattern": options.instructor_pattern,
            "section_pattern": options.section_pattern,
            "after_term_code": options.after_term_code,
            "before_term_code": options.before_term_code,
            "include_histograms": options.include_histograms,
            "include_multiyear": options.include_multiyear,
            "include_instructor_multiyear": options.include_instructor_multiyear,
        },
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
    }
    manifest_path = run_root / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    latest_link = options.output_root / "latest-manifest.json"
    latest_link.parent.mkdir(parents=True, exist_ok=True)
    with latest_link.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    return manifest
