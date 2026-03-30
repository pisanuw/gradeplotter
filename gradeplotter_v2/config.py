from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    secret_key: str
    output_root: Path
    admin_user: str
    admin_password: str
    viewer_user: str
    viewer_password: str


def load_config() -> AppConfig:
    return AppConfig(
        secret_key=os.getenv("GRADEPLOTTER_SECRET_KEY", "gradeplotter-dev-key"),
        output_root=Path(os.getenv("GRADEPLOTTER_OUTPUT_ROOT", "gradeplotter_output")),
        admin_user=os.getenv("GRADEPLOTTER_ADMIN_USER", "admin"),
        admin_password=os.getenv("GRADEPLOTTER_ADMIN_PASSWORD", "admin"),
        viewer_user=os.getenv("GRADEPLOTTER_VIEWER_USER", "viewer"),
        viewer_password=os.getenv("GRADEPLOTTER_VIEWER_PASSWORD", "viewer"),
    )
