#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from gradeplotter_v2.generator import GenerationOptions, generate_artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate GradePlotter v2 artifacts")
    parser.add_argument("-i", "--input", nargs="+", required=True, help="Input CSV files")
    parser.add_argument("--dest", default="gradeplotter_output", help="Output root directory")
    parser.add_argument("--curriculum", default="CSS", help="Regex for curriculum filter")
    parser.add_argument("--instructor", default=".*", help="Regex for instructor filter")
    parser.add_argument("--sections", default=".*", help="Regex for section filter")
    parser.add_argument("--after", default=None, help="Inclusive lower term code, ex: 2024AUT")
    parser.add_argument("--before", default=None, help="Exclusive upper term code, ex: 2025AUT")
    parser.add_argument("--no-histograms", action="store_true", help="Skip histogram generation")
    parser.add_argument("--no-multiyear", action="store_true", help="Skip multiyear generation")
    parser.add_argument(
        "--multiyear-instructor",
        action="store_true",
        help="Create per-instructor multiyear trends",
    )
    parser.add_argument(
        "--combosections",
        action="store_true",
        help="Single histogram using data from multiple sections per course (legacy parity)",
    )
    parser.add_argument(
        "--comboinstructor",
        action="store_true",
        help="Single histogram using data from multiple sections per course per instructor (legacy parity)",
    )
    parser.add_argument(
        "--dfwreport",
        type=str,
        default=None,
        help="Generate drop/fail/withdraw/repeat report for a course (legacy parity)",
    )
    parser.add_argument(
        "--skip-unchanged",
        action="store_true",
        help="Skip files whose input data is identical to the previous run",
    )
    parser.add_argument(
        "--instructor-config",
        default=None,
        help="Path to instructors.json mapping canonical names, netids, and full/part-time status",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    options = GenerationOptions(
        input_files=[Path(p) for p in args.input],
        output_root=Path(args.dest),
        curriculum_pattern=args.curriculum,
        instructor_pattern=args.instructor,
        section_pattern=args.sections,
        after_term_code=args.after,
        before_term_code=args.before,
        include_histograms=not args.no_histograms,
        include_multiyear=not args.no_multiyear,
        include_instructor_multiyear=args.multiyear_instructor,
        combine_sections=args.combosections,
        combo_instructor=args.comboinstructor,
        dfw_report=args.dfwreport,
        skip_unchanged=args.skip_unchanged,
        instructor_config_path=Path(args.instructor_config) if args.instructor_config else None,
    )
    manifest = generate_artifacts(options)
    skipped = manifest.get("skipped_count", 0)
    generated = manifest["artifact_count"] - skipped
    msg = f"Run {manifest['run_id']}: {generated} generated, {skipped} skipped"
    print(msg)


if __name__ == "__main__":
    main()
