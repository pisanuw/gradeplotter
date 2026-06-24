from __future__ import annotations

import hashlib
import json
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .loader import load_grade_records
from .rendering import render_legacy_style_histogram, render_multiyear_trend
from .repository import GradeRepository, Query

_HASH_VERSION = "v1"


def _input_hash(*parts: object) -> str:
    h = hashlib.sha256()
    for part in parts:
        h.update(repr(part).encode())
    return f"{_HASH_VERSION}:{h.hexdigest()}"


def _cache_sidecar(out_path: Path, run_root: Path, output_root: Path) -> Path:
    """Stable sidecar location that persists across runs, keyed by path within the run."""
    rel = out_path.relative_to(run_root)
    return output_root / ".skip_cache" / rel.with_suffix(".sha256")


def _is_unchanged(out_path: Path, run_root: Path, output_root: Path, data_hash: str) -> bool:
    s = _cache_sidecar(out_path, run_root, output_root)
    return s.exists() and s.read_text(encoding="utf-8").strip() == data_hash


def _mark_written(out_path: Path, run_root: Path, output_root: Path, data_hash: str) -> None:
    s = _cache_sidecar(out_path, run_root, output_root)
    s.parent.mkdir(parents=True, exist_ok=True)
    s.write_text(data_hash + "\n", encoding="utf-8")


def _load_instructor_config(path: Optional[Path]) -> dict:
    """Load instructors.json and return a dict keyed by lower-cased CSV name."""
    if path is None:
        return {}
    with path.open(encoding="utf-8") as f:
        raw = json.load(f)
    result: dict = {}
    for canonical, netid in raw.get("full_time", {}).items():
        result[canonical.lower()] = {"canonical": canonical, "type": "full_time", "netid": netid}
    return result


def _resolve_instructor(csv_name: str, config: dict) -> tuple[str, Path]:
    """Return (canonical_name, subfolder_relative_to_run_root) for an instructor."""
    entry = config.get(csv_name.lower())
    if entry:
        canonical = entry["canonical"]
        if entry["type"] == "full_time":
            folder = Path(f"grading_stats {canonical} - {entry['netid']}") / canonical
            return canonical, folder
        return canonical, Path("stats_part_time_instructors") / canonical
    return csv_name, Path("stats_part_time_instructors") / csv_name


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
    skip_unchanged: bool = False
    instructor_config_path: Optional[Path] = None


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


def generate_artifacts(options: GenerationOptions) -> dict:
    instructor_config = _load_instructor_config(options.instructor_config_path)

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
            # Combined histogram per instructor+course → instructor folder as {course}-combined-{name}.png
            instructor_course_map: dict = defaultdict(lambda: defaultdict(list))
            for record in filtered:
                instr = record.section.instructor or "000NoInstructor"
                course = record.section.course_code
                instructor_course_map[instr][course].append(record)
            for csv_instr, course_map in instructor_course_map.items():
                canonical, instr_subdir = _resolve_instructor(csv_instr, instructor_config)
                for course, records_group in course_map.items():
                    numerical = [r.numeric_grade for r in records_group if r.numeric_grade is not None]
                    non_numerical = [r.grade_raw for r in records_group if r.numeric_grade is None]
                    if not numerical and not non_numerical:
                        continue
                    filename = f"{course}-combined-{canonical}.png"
                    title = f"{course} (All Sections) {canonical}"
                    out_path = run_root / instr_subdir / filename
                    data_hash = _input_hash(title, sorted(numerical), sorted(non_numerical))
                    if options.skip_unchanged and _is_unchanged(out_path, run_root, options.output_root, data_hash):
                        artifacts.append({
                            "type": "combo_instructor_histogram",
                            "id": f"{course}-{canonical}",
                            "path": str(out_path.relative_to(options.output_root)),
                            "count": len(records_group),
                            "skipped": True,
                        })
                    else:
                        render_legacy_style_histogram(
                            numerical_grades=numerical,
                            non_numerical_grades=non_numerical,
                            title=title,
                            output_path=out_path,
                        )
                        _mark_written(out_path, run_root, options.output_root, data_hash)
                        artifacts.append({
                            "type": "combo_instructor_histogram",
                            "id": f"{course}-{canonical}",
                            "path": str(out_path.relative_to(options.output_root)),
                            "count": len(records_group),
                        })

        elif options.combine_sections:
            # Combined histogram per course → stats_per_course/{course}-combined.png
            course_map: dict = defaultdict(list)
            for record in filtered:
                course_map[record.section.course_code].append(record)
            for course, records_group in course_map.items():
                numerical = [r.numeric_grade for r in records_group if r.numeric_grade is not None]
                non_numerical = [r.grade_raw for r in records_group if r.numeric_grade is None]
                if not numerical and not non_numerical:
                    continue
                filename = f"{course}-combined.png"
                title = f"{course} (All Sections)"
                out_path = run_root / "stats_per_course" / filename
                data_hash = _input_hash(title, sorted(numerical), sorted(non_numerical))
                if options.skip_unchanged and _is_unchanged(out_path, run_root, options.output_root, data_hash):
                    artifacts.append({
                        "type": "combo_histogram",
                        "id": course,
                        "path": str(out_path.relative_to(options.output_root)),
                        "count": len(records_group),
                        "skipped": True,
                    })
                else:
                    render_legacy_style_histogram(
                        numerical_grades=numerical,
                        non_numerical_grades=non_numerical,
                        title=title,
                        output_path=out_path,
                    )
                    _mark_written(out_path, run_root, options.output_root, data_hash)
                    artifacts.append({
                        "type": "combo_histogram",
                        "id": course,
                        "path": str(out_path.relative_to(options.output_root)),
                        "count": len(records_group),
                    })

        else:
            # Per-section histograms → instructor folder only
            section_map: dict[str, list] = {}
            for record in filtered:
                section_map.setdefault(record.section.compact_name, []).append(record)

            for section_name, section_records in section_map.items():
                numerical = [r.numeric_grade for r in section_records if r.numeric_grade is not None]
                non_numerical = [r.grade_raw for r in section_records if r.numeric_grade is None]
                if not numerical and not non_numerical:
                    continue

                year, quarter, curriculum, number, section, csv_instr = _section_filename_parts(section_name)
                canonical, instr_subdir = _resolve_instructor(csv_instr, instructor_config)
                filename = f"{year}-{quarter}-{curriculum}-{number}-{section}-{canonical}.png"
                title = f"{year} {quarter} {curriculum} {number} {section} {canonical}"
                out_path = run_root / instr_subdir / filename

                data_hash = _input_hash(title, sorted(numerical), sorted(non_numerical))
                if options.skip_unchanged and _is_unchanged(out_path, run_root, options.output_root, data_hash):
                    artifacts.append({
                        "type": "section_histogram",
                        "id": section_name,
                        "path": str(out_path.relative_to(options.output_root)),
                        "count": len(section_records),
                        "skipped": True,
                    })
                else:
                    render_legacy_style_histogram(
                        numerical_grades=numerical,
                        non_numerical_grades=non_numerical,
                        title=title,
                        output_path=out_path,
                    )
                    _mark_written(out_path, run_root, options.output_root, data_hash)
                    artifacts.append({
                        "type": "section_histogram",
                        "id": section_name,
                        "path": str(out_path.relative_to(options.output_root)),
                        "count": len(section_records),
                    })

    if options.include_multiyear:
        courses = repo.distinct_courses(filtered)
        for course_code in courses:
            section_count = len({r.section.compact_name for r in filtered if r.section.course_code == course_code})
            if options.dept_restrictions and section_count < options.min_sections_for_multiyear:
                continue

            points = repo.course_medians_by_term(filtered, course_code=course_code)
            if len(points) < 2:
                continue

            # Course multiyear → stats_per_course/{course}.png
            path = run_root / "stats_per_course" / f"{course_code}.png"
            title = f"{course_code} Median Grades"
            data_hash = _input_hash(title, points)
            if options.skip_unchanged and _is_unchanged(path, run_root, options.output_root, data_hash):
                artifacts.append({
                    "type": "course_multiyear",
                    "id": course_code,
                    "path": str(path.relative_to(options.output_root)),
                    "points": len(points),
                    "sections": section_count,
                    "skipped": True,
                })
            else:
                render_multiyear_trend(points, title=title, output_path=path)
                _mark_written(path, run_root, options.output_root, data_hash)
                artifacts.append({
                    "type": "course_multiyear",
                    "id": course_code,
                    "path": str(path.relative_to(options.output_root)),
                    "points": len(points),
                    "sections": section_count,
                })

            if options.include_instructor_multiyear:
                instructors = repo.distinct_instructors(filtered, course_code)
                for csv_instr in instructors:
                    ipoints = repo.course_medians_by_term(
                        filtered,
                        course_code=course_code,
                        instructor=csv_instr,
                    )
                    if len(ipoints) < 2:
                        continue
                    canonical, instr_subdir = _resolve_instructor(csv_instr, instructor_config)
                    ifilename = f"{course_code}-{canonical}.png"
                    ipath = run_root / instr_subdir / ifilename
                    ititle = f"{course_code} Median Grades for {canonical}"
                    data_hash = _input_hash(ititle, ipoints)
                    if options.skip_unchanged and _is_unchanged(ipath, run_root, options.output_root, data_hash):
                        artifacts.append({
                            "type": "instructor_multiyear",
                            "id": f"{course_code}-{canonical}",
                            "path": str(ipath.relative_to(options.output_root)),
                            "points": len(ipoints),
                            "skipped": True,
                        })
                    else:
                        render_multiyear_trend(ipoints, title=ititle, output_path=ipath)
                        _mark_written(ipath, run_root, options.output_root, data_hash)
                        artifacts.append({
                            "type": "instructor_multiyear",
                            "id": f"{course_code}-{canonical}",
                            "path": str(ipath.relative_to(options.output_root)),
                            "points": len(ipoints),
                        })

    run_root.mkdir(parents=True, exist_ok=True)
    skipped_count = sum(1 for a in artifacts if a.get("skipped"))
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
            "skip_unchanged": options.skip_unchanged,
            "instructor_config_path": str(options.instructor_config_path) if options.instructor_config_path else None,
        },
        "artifact_count": len(artifacts),
        "skipped_count": skipped_count,
        "artifacts": artifacts,
    }
    run_root.mkdir(parents=True, exist_ok=True)
    manifest_path = run_root / "manifest.json"
    with manifest_path.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    latest_link = options.output_root / "latest-manifest.json"
    latest_link.parent.mkdir(parents=True, exist_ok=True)
    with latest_link.open("w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)

    return manifest
