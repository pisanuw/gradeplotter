from __future__ import annotations

import json
from pathlib import Path


def load_manifests(output_root: Path) -> list[dict]:
    manifests: list[dict] = []
    runs = output_root / "runs"
    if not runs.exists():
        return manifests

    for manifest_path in runs.glob("*/manifest.json"):
        try:
            with manifest_path.open("r", encoding="utf-8") as handle:
                manifest = json.load(handle)
            manifests.append(manifest)
        except (OSError, json.JSONDecodeError):
            continue

    manifests.sort(key=lambda item: item.get("run_id", ""), reverse=True)
    return manifests


def collect_artifacts(output_root: Path) -> list[dict]:
    manifests = load_manifests(output_root)
    artifacts: list[dict] = []
    for manifest in manifests:
        run_id = manifest.get("run_id", "")
        for artifact in manifest.get("artifacts", []):
            item = dict(artifact)
            item["run_id"] = run_id
            artifacts.append(item)
    return artifacts
