#!/usr/bin/env python3
"""Copy the existing static site into the publish directory."""
from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT / "public"
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "public",
}
SKIP_FILES = {
    ".gitignore",
    "README.md",
    "build_reports.py",
    "build_site.py",
    "netlify.toml",
}


def build_static_site() -> None:
    if PUBLIC.exists():
        shutil.rmtree(PUBLIC)
    PUBLIC.mkdir()

    for source in ROOT.iterdir():
        if source.is_dir():
            if source.name in SKIP_DIRS:
                continue
            shutil.copytree(source, PUBLIC / source.name)
        elif source.name not in SKIP_FILES:
            shutil.copy2(source, PUBLIC / source.name)


def main() -> None:
    build_static_site()


if __name__ == "__main__":
    main()