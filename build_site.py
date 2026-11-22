#!/usr/bin/env python3
"""Stage the existing static site and build Zola-authored content."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "admin",
    "cms-proxy",
    "content",
    "public",
    "static",
    "templates",
    "themes",
}
SKIP_FILES = {
    ".gitignore",
    ".pages.yml",
    "README.md",
    "build_reports.py",
    "build_site.py",
    "netlify.toml",
    "zola.toml",
}


def stage_legacy_site() -> None:
    if STATIC.exists():
        shutil.rmtree(STATIC)
    STATIC.mkdir()

    for source in ROOT.iterdir():
        if source.is_dir():
            if source.name in SKIP_DIRS:
                continue
            shutil.copytree(source, STATIC / source.name)
        elif source.name not in SKIP_FILES:
            shutil.copy2(source, STATIC / source.name)


def main() -> None:
    stage_legacy_site()
    zola = os.environ.get("ZOLA_BIN", "zola")
    command = [zola, "build"]
    deploy_url = os.environ.get("DEPLOY_PRIME_URL")
    if deploy_url:
        command.extend(["--base-url", deploy_url])
    subprocess.run(command, cwd=ROOT, check=True)


if __name__ == "__main__":
    main()