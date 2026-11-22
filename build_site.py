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


def inject_gif_barrage() -> None:
    """Add the shared GIF barrage script to every published HTML page."""
    script_tag = '<script src="{path}js/gif-barrage.js"></script>'
    for html_path in PUBLIC.rglob("*.html"):
        text = html_path.read_text(encoding="utf-8")
        if "gif-barrage.js" in text:
            continue
        depth = len(html_path.relative_to(PUBLIC).parent.parts)
        prefix = "../" * depth
        script = script_tag.format(path=prefix)
        if "</body>" in text:
            text = text.replace("</body>", script + "\n</body>", 1)
        else:
            text += "\n" + script
        html_path.write_text(text, encoding="utf-8")


def main() -> None:
    build_static_site()
    inject_gif_barrage()


if __name__ == "__main__":
    main()