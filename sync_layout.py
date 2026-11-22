#!/usr/bin/env python3
"""Make every page share the home page's layout.

The home page (`index.html`) is the single source of truth for the shared
page chrome:

  * the marquee banner           <!-- MARQUEE BANNER --> .. <!-- MAIN LAYOUT TABLE -->
  * the left sidebar (menu/GIFs) <!-- LEFT SIDEBAR -->   .. <!-- MAIN CONTENT AREA -->
  * the right sidebar (GIFs)     <!-- RIGHT SIDEBAR -->  .. </tr>
  * banner, footer, ads, age gate and scripts
                                 <!-- PAGE BOTTOM -->    .. </body>

Every other HTML page keeps its own <head>, optional breadcrumb and main
content cell; everything else is replaced with the home page's chrome, with
relative links rewritten for the page's folder depth.

Usage:  python sync_layout.py
(`build_reports.py` also runs this automatically.)
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATE = ROOT / "index.html"
SKIP_DIRS = {".git", ".venv", "__pycache__", "public", "node_modules"}

# Pages that must not show the age gate (the gate's "Leave" button goes here).
NO_AGE_GATE = {"access-denied.html"}
# Pages served from arbitrary URLs need root-absolute links.
ABSOLUTE_LINKS = {"404.html"}

RIGHT_TD_RE = re.compile(
    r'<td width="160" valign="top" bgcolor="#ffffcc" style="border-left'
)
SCRIPT_RE = re.compile(r"<script\b[^>]*>.*?</script>", re.S | re.I)
LINK_ATTR_RE = re.compile(r'\b(src|href)="([^"]*)"')
SHARED_SCRIPTS = ("counter.js", "age-gate.js", "gif-barrage.js")


def _between(text: str, start: str, end: str) -> str:
    i = text.index(start)
    j = text.index(end, i)
    return text[i:j].rstrip()


def load_chrome() -> dict:
    text = TEMPLATE.read_text(encoding="utf-8")
    right_start = text.index("<!-- RIGHT SIDEBAR -->")
    return {
        "top": _between(text, "<!-- MARQUEE BANNER -->", "<!-- MAIN LAYOUT TABLE -->"),
        "left": _between(text, "<!-- LEFT SIDEBAR -->", "<!-- MAIN CONTENT AREA -->"),
        "right": text[right_start:text.index("</tr>", right_start)].rstrip(),
        "bottom": _between(text, "<!-- PAGE BOTTOM -->", "</body>"),
    }


def prefix_for(rel_path: str) -> str:
    if rel_path in ABSOLUTE_LINKS:
        return "/"
    depth = len(Path(rel_path).parent.parts)
    return "../" * depth


def rebase(fragment: str, prefix: str) -> str:
    """Rewrite home-relative links in a chrome fragment for another folder."""
    if not prefix:
        return fragment

    def fix(match: re.Match) -> str:
        attr, value = match.groups()
        if not value or value.startswith(
            ("http:", "https:", "/", "#", "mailto:", "data:", "../", "tel:")
        ):
            return match.group(0)
        return f'{attr}="{prefix}{value}"'

    return LINK_ATTR_RE.sub(fix, fragment)


def fix_head(head: str, prefix: str, age_gate: bool) -> str:
    head = head.strip("\n")
    if 'name="viewport"' not in head:
        head = re.sub(
            r'(<meta charset="[^"]*">)',
            r'\1\n  <meta name="viewport" content="width=device-width, initial-scale=1">',
            head, count=1, flags=re.I,
        )
    if age_gate and "age-gate.css" not in head:
        head = re.sub(
            r'(<link rel="stylesheet" href="[^"]*style\.css">)',
            r'\1\n  <link rel="stylesheet" href="' + prefix + 'age-gate.css">',
            head, count=1,
        )
    return head


def render_page(head: str, content: str, rel_path: str,
                breadcrumb: str = "", extra_scripts: list | None = None,
                chrome: dict | None = None) -> str:
    """Wrap a page's own head/breadcrumb/content in the shared chrome."""
    chrome = chrome or load_chrome()
    prefix = prefix_for(rel_path)
    age_gate = rel_path not in NO_AGE_GATE

    bottom = chrome["bottom"]
    if not age_gate:
        bottom = re.sub(r"\n*<!-- AGE GATE -->.*?<!-- AGE GATE:END -->\n*",
                        "\n\n", bottom, flags=re.S)
    scripts = "".join("\n" + s for s in (extra_scripts or []))

    parts = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        fix_head(head, prefix, age_gate),
        "</head>",
        "",
        "<body>",
        "",
        rebase(chrome["top"], prefix),
        "",
    ]
    if breadcrumb.strip():
        parts += [breadcrumb.strip(), ""]
    parts += [
        "<!-- MAIN LAYOUT TABLE -->",
        '<table width="100%" border="0" cellpadding="0" cellspacing="0">',
        "  <tr>",
        "    " + rebase(chrome["left"], prefix),
        "",
        "    <!-- MAIN CONTENT AREA -->",
        '    <td valign="top" bgcolor="#ffffff" style="padding: 16px;">',
        "",
        content.strip("\n"),
        "",
        "    </td>",
        "    " + rebase(chrome["right"], prefix),
        "  </tr>",
        "</table>",
        "",
        rebase(bottom, prefix) + scripts,
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(parts)


def parse_page(text: str) -> dict | None:
    """Pull the page-specific pieces out of an existing page."""
    if "<!-- MAIN CONTENT AREA -->" not in text or "<head>" not in text:
        return None

    head = text[text.index("<head>") + len("<head>"):text.index("</head>")]

    breadcrumb = ""
    if "<!-- BREADCRUMB -->" in text:
        breadcrumb = _between(text, "<!-- BREADCRUMB -->", "<!-- MAIN LAYOUT TABLE -->")

    start = text.index("<!-- MAIN CONTENT AREA -->")
    td_open_end = text.index(">", text.index("<td", start)) + 1
    candidates = []
    marker = text.find("<!-- RIGHT SIDEBAR -->", td_open_end)
    if marker != -1:
        candidates.append(marker)
    m = RIGHT_TD_RE.search(text, td_open_end)
    if m:
        candidates.append(m.start())
    if not candidates:
        return None
    right_start = min(candidates)
    content_end = text.rindex("</td>", td_open_end, right_start)
    content = text[td_open_end:content_end].rstrip()

    tail = text[right_start:]
    extra_scripts = [
        s for s in SCRIPT_RE.findall(tail)
        if not any(name in s for name in SHARED_SCRIPTS)
    ]
    return {
        "head": head,
        "breadcrumb": breadcrumb,
        "content": content,
        "extra_scripts": extra_scripts,
    }


def html_pages():
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or path == TEMPLATE:
            continue
        yield path, rel.as_posix()


def sync_all() -> None:
    chrome = load_chrome()
    for path, rel in html_pages():
        text = path.read_text(encoding="utf-8")
        parts = parse_page(text)
        if parts is None:
            print(f"skipped   {rel}  (no layout markers)")
            continue
        page = render_page(chrome=chrome, rel_path=rel, **parts)
        if page != text:
            path.write_text(page, encoding="utf-8")
            print(f"synced    {rel}")


if __name__ == "__main__":
    sync_all()
