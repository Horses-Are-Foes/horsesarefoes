#!/usr/bin/env python3
"""Build renderer for Horses Are Foes.

Turns markdown posts into HTML and rebuilds the home-page card regions so the
site always reflects every report in `reports/`.

What it does:
  * Renders `reports/<slug>/index.md`  ->  `reports/<slug>/index.html`
    (markdown-authored posts).
  * Leaves hand-authored `index.html` posts untouched, but reads them for
    card metadata so old and new posts render consistently.
  * Regenerates the report lists in `index.html` and `reports/index.html`.

No third-party dependencies (tiny built-in markdown converter) so it runs on
GitHub Pages previews and Netlify's build step with just Python 3.

Usage:  python3 build_reports.py
"""
from __future__ import annotations

import html
import os
import re
from datetime import date, datetime

REPO = os.path.dirname(os.path.abspath(__file__))
REPORTS = os.path.join(REPO, "reports")
HOME = os.path.join(REPO, "index.html")
DOMAIN = "https://horsesarefoes.com"
LOGO = DOMAIN + "/assets/HAF_LOGO.png"

MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11,
    "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8,
    "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

CONTENT_IMG_PREFIXES = ("assets/", "../../", "https://", "../")


# ---------------------------------------------------------------------------
# date helpers
# ---------------------------------------------------------------------------
def parse_date(raw: str) -> datetime:
    """Accept ISO (YYYY-MM-DD) or 'Month D, YYYY' and return a datetime."""
    raw = (raw or "").strip()
    m = re.match(r"(\d{4})-(\d{1,2})-(\d{1,2})", raw)
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3]))
    for name, num in MONTHS.items():
        m = re.search(rf"{name}\.?\s+(\d{{1,2}}),?\s+(\d{{4}})", raw, re.I)
        if m:
            return datetime(int(m[2]), num, int(m[1]))
    return datetime(1900, 1, 1)


def human_date(dt: datetime) -> str:
    return dt.strftime("%B ") + str(dt.day) + ", " + str(dt.year)


def display_date(raw: str, dt: datetime) -> str:
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw.strip()):
        return human_date(dt)
    return raw or human_date(dt)


# ---------------------------------------------------------------------------
# metadata extraction from an existing HTML post
# ---------------------------------------------------------------------------
def extract_metadata(slug: str, text: str) -> dict:
    og = lambda prop: (re.search(
        rf'<meta[^>]*property="?og:{prop}"\s+content="([^"]*)"', text, re.I) or
        re.search(rf'<meta[^>]*content="([^"]*)"[^>]*property="?og:{prop}"', text, re.I))

    m = og("title")
    title = (m.group(1) if m else slug)
    # Normalise titles to match the committed cards:
    #   * drop a subtitle after an em dash ("Title - subtitle")
    #   * convert an ellipsis … to ...
    #   * turn "Title: Subtitle" into "Title Subtitle"
    title = re.split("—", title, maxsplit=1)[0]
    title = title.replace("…", "...")
    title = re.sub(r"\s*:\s*", " ", title).strip()

    desc = og("description")
    description = desc.group(1).strip() if desc else ""

    # Cover = og:image (matches the committed cards, repo-root relative as
    # "reports/<slug>/file"), stripped so card_img() can re-attach it, with a
    # body-image fallback before the logo.
    ogc = og("image")
    cover = (ogc.group(1).strip() if ogc else "").split("?")[0]
    prefix = "reports/" + slug + "/"
    if cover.startswith(prefix):
        cover = cover[len(prefix):]
    cover = cover.lstrip("./")
    if not cover or any(cover.startswith(p) for p in ("assets/", "../../", "../", "https://", "http://")):
        for src in re.findall(r'<img[^>]+src="([^"]+)"', text):
            src = src.split("?")[0].lstrip("./")
            if not src.startswith(("assets/", "../../", "../", "https://", "http://")):
                cover = src
                break
    if not cover:
        cover = "assets/HAF_LOGO.png"

    # Author + published from the report header line.
    m = re.search(r"Report by\s+(.+?)<", text)
    author = m.group(1).strip() if m else "Gideon Vale"

    m = re.search(r"Published:\s*([^<]+?)</font>", text)
    published_raw = m.group(1).strip() if m else ""

    return {
        "slug": slug,
        "title": title,
        "subtitle": description,
        "author": author,
        "published_raw": published_raw,
        "published_key": parse_date(published_raw),
        "cover": cover,
    }


# ---------------------------------------------------------------------------
# tiny markdown -> HTML converter
# ---------------------------------------------------------------------------
def _img_tag(src: str, alt: str) -> str:
    """Render a markdown image inside the site's retro bordered table."""
    src = src.strip()
    return (
        '<br><center><table border="3" cellpadding="5" cellspacing="0" '
        'bgcolor="#fffff0" style="border-style: outset;">'
        '<tr><td align="center"><img src="' + html.escape(src) +
        '" alt="' + html.escape(alt) + '" width="320" border="2" '
        'style="border-radius: 0px;" /><br><font face="Courier New, monospace" '
        'size="1" color="#333333">' + html.escape(alt) + '</font></td></tr>'
        '</table></center><br>'
    )


def _inline(s: str) -> str:
    s = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)",
               lambda m: _img_tag(m.group(2), m.group(1)), s)
    s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)",
               lambda m: '<a href="' + html.escape(m.group(2)) +
               '" class="hl"><u>' + html.escape(m.group(1)) + '</u></a>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s, flags=re.S)
    s = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", s, flags=re.S)
    s = re.sub(r"`([^`]+)`",
               r'<font face="Courier New, monospace" size="1">\1</font>', s)
    return s


def md_to_html(md: str) -> str:
    md = md.replace("\r\n", "\n").strip()
    if re.search(r"<(?:p|div|h[1-6]|table|blockquote|ul|ol)\b", md, re.I):
        return md
    blocks = re.split(r"\n\n+", md)
    out = []
    for block in blocks:
        lines = [ln for ln in block.split("\n")]
        if not lines or all(l.strip() == "" for l in lines):
            continue
        first = lines[0].strip()
        if re.fullmatch(r"<img\b[^>]*>", first, re.I):
            width_match = re.search(r'\bwidth=["\'](\d+(?:\.\d+)?)%["\']', first, re.I)
            if width_match:
                width = round(float(width_match.group(1)) * 9)
                first = re.sub(
                    r'\bwidth=["\']\d+(?:\.\d+)?%["\']',
                    f'width="{width}" style="max-width: 90%; height: auto;"',
                    first,
                    count=1,
                    flags=re.I,
                )
            out.append(
                '<br><center><table border="3" cellpadding="5" cellspacing="0" '
                'bgcolor="#fffff0" style="border-style: outset;"><tr><td align="center">'
                + first + '</td></tr></table></center><br>'
            )
        elif first.startswith("#"):
            level = len(first) - len(first.lstrip("#"))
            level = min(max(level, 1), 3)
            size = max(2, 5 - level)
            heading = _inline(first.lstrip("#").strip())
            out.append('<center><font size="%d"><b>%s</b></font></center><br>' % (size, heading))
        elif first.startswith(">"):
            inner = " ".join(l.lstrip("> ").strip() for l in lines)
            out.append('<blockquote>' + _inline(inner) + "</blockquote>")
        elif re.match(r"^(\d*\.?)\s", first) or first[:1] in ("-", "*"):
            items = [re.sub(r"^\s*(\d*\.?)\s*", "", ln).strip() for ln in lines]
            ordered = first[0].isdigit()
            tag = "ol" if ordered else "ul"
            inner = "".join("<li>" + _inline(i) + "</li>" for i in items)
            out.append("<%" + tag + ">" + inner + "</%s>" % tag)
        else:
            para = " ".join(l.strip() for l in lines if l.strip())
            out.append("<p>" + _inline(para) + "</p>")
    return "<br>".join(out)


def _normalize_asset(src: str, slug: str) -> str:
    """Return a media path relative to the post directory.

    A cover can be stored as the media path
    (``assets/x.png``), the public path (``/reports/<slug>/assets/x.png``),
    or an absolute URL. Normalise all three to something the site serves at
    ``reports/<slug>/``. Returns "" when there is no usable source.
    """
    src = (src or "").strip()
    if not src:
        return ""
    if src.startswith("http://") or src.startswith("https://"):
        return src
    clean = re.sub(r"^(\.\./)+", "", src).lstrip("./")
    clean = re.sub(r"^reports/" + re.escape(slug) + r"/", "", clean).lstrip("/")
    return clean


# ---------------------------------------------------------------------------
# markdown post front matter -> rendered HTML
# ---------------------------------------------------------------------------
def render_markdown_post(fm: dict, body_md: str, slug: str) -> str:
    title = fm.get("title") or slug
    author = fm.get("author") or "Gideon Vale"
    published_raw = fm.get("published") or fm.get("date", "")
    published = display_date(published_raw, parse_date(published_raw))
    body = md_to_html(body_md)
    warning = fm.get("warning") or "INVESTIGATION REPORT"
    subtitle = fm.get("subtitle", "")
    description = title + " - investigation report by " + author + "."
    title_text = html.escape(title, quote=False)
    title_attr = html.escape(title, quote=True)
    author_text = html.escape(author, quote=False)
    description_attr = html.escape(description, quote=True)

    cover_src = _normalize_asset(fm.get("cover", ""), slug)
    if not cover_src:
        og_image = LOGO
    elif re.match(r"^\s*https?://", cover_src):
        og_image = cover_src
    elif "/" in cover_src:
        og_image = DOMAIN + "/" + cover_src
    else:
        og_image = DOMAIN + "/reports/" + slug + "/" + cover_src

    template_path = os.path.join(REPORTS, "faerie-lights-swamp-gas", "index.html")
    with open(template_path, encoding="utf-8") as template_file:
        page = template_file.read()

    head_start = page.index("<head>")
    head_end = page.index("</head>", head_start) + len("</head>")
    head = f'''<head>
  <meta charset="UTF-8">
  <title>{title_text} | Horses Are Foes</title>
  <meta name="description" content="{description_attr}">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="../../style.css">
  <link rel="icon" href="/assets/HAF_LOGO.png">
  <meta property="og:title" content="{title_attr}">
  <meta property="og:description" content="{description_attr}">
  <meta property="og:image" content="{html.escape(og_image, quote=True)}">
  <meta property="og:url" content="{DOMAIN}/reports/{slug}/">
  <meta property="og:type" content="article">
  <meta name="twitter:card" content="summary_large_image">
  <link rel="canonical" href="{DOMAIN}/reports/{slug}/">
</head>'''
    page = page[:head_start] + head + page[head_end:]

    banner_start = page.index("<!-- MARQUEE BANNER -->")
    breadcrumb_start = page.index("<!-- BREADCRUMB -->", banner_start)
    banner = f'''<!-- MARQUEE BANNER -->
<table width="100%" bgcolor="#000080" cellpadding="3" cellspacing="0">
  <tr>
    <td align="center">
      <marquee scrollamount="3" behavior="scroll" direction="left">
        <font face="Courier New, monospace" size="2" color="#ffffff">
          &#9733; {html.escape(warning, quote=False)} &#9733; HORSES ARE FOES &#9733;
        </font>
      </marquee>
    </td>
  </tr>
</table>

'''
    page = page[:banner_start] + banner + page[breadcrumb_start:]

    breadcrumb_start = page.index("<!-- BREADCRUMB -->")
    layout_start = page.index("<!-- MAIN LAYOUT TABLE -->", breadcrumb_start)
    breadcrumb = f'''<!-- BREADCRUMB -->
<table width="100%" cellpadding="4" cellspacing="0">
  <tr>
    <td>
      <font face="Courier New, monospace" size="1" color="#808080">
        <a href="../../index.html"><font color="#0000ff"><u>[ Home ]</u></font></a> &gt; <b>Reports</b> &gt; <b>{title_text}</b>
      </font>
    </td>
  </tr>
</table>

'''
    page = page[:breadcrumb_start] + breadcrumb + page[layout_start:]

    content_start = page.index("<!-- MAIN CONTENT AREA -->")
    right_sidebar_start = page.index(
        '    <td width="160" valign="top" bgcolor="#ffffcc" style="border-left: 2px ridge #cccccc; padding: 8px;">',
        content_start,
    )
    subtitle_html = (
        '<br><font face="Times New Roman, Times, serif" size="3" color="#333333"><i>'
        + html.escape(subtitle, quote=False)
        + "</i></font>"
        if subtitle else ""
    )
    article = f'''<!-- MAIN CONTENT AREA -->
    <td valign="top" bgcolor="#ffffff" style="padding: 16px;">

      <!-- REPORT HEADER -->
      <center>
        <font face="Comic Sans MS, cursive" size="2" color="#0000ff"><b>Report by {author_text}</b></font>
      </center>
      <center>
        <font face="Courier New, monospace" size="1" color="#808080">Published: {html.escape(published, quote=False)}</font>
      </center>

      <br>
      <hr class="separator">
      <br>

      <!-- REPORT TITLE -->
      <center>
        <font face="Comic Sans MS, cursive" size="5" color="#0000ff"><b>&#9733; {title_text} &#9733;</b></font>{subtitle_html}
      </center>

      <br>
      <hr class="separator">
      <br>

      <!-- REPORT CONTENT -->
      <div class="report-content">
      {body}
      </div>

      <br>
      <hr class="separator">
      <br>

      <center>
        <table border="2" cellpadding="10" cellspacing="0" bgcolor="#000080" style="border-style: outset;">
          <tr>
            <td align="center">
              <font face="Times New Roman, Times, serif" size="2" color="#ffffff">
                <b>Return to Reports List</b><br>
                <a href="../../index.html"><font color="#ffff00"><u>[ Return to Homepage ]</u></font></a>
              </font>
            </td>
          </tr>
        </table>
      </center>

    </td>
'''
    return page[:content_start] + article + page[right_sidebar_start:]


# ---------------------------------------------------------------------------
# front matter parsing (simple YAML subset)
# ---------------------------------------------------------------------------
def split_front_matter(text: str):
    """Return (front_matter_dict, body_md) from a markdown file."""
    fm, body = {}, text
    if not text.startswith("---"):
        return fm, body

    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.S)
    if not m:
        return fm, body

    raw = m.group(1)
    body = m.group(2)
    block_key = None
    block_lines = []
    extra = None

    def finish_description():
        if block_key:
            fm[block_key] = " ".join(block_lines).strip()

    sections = []
    section = None
    content_key = None
    content_lines = []

    def finish_content():
        nonlocal content_key, content_lines
        if section is not None and content_key:
            section[content_key] = "\n".join(content_lines).strip()
        content_key = None
        content_lines = []

    in_sections = False
    for line in raw.split("\n"):
        stripped = line.strip()

        if in_sections:
            if line.startswith("  - type:"):
                finish_content()
                section = {"type": stripped.split(":", 1)[1].strip().strip('"').strip("'")}
                sections.append(section)
                continue
            if section is not None and line.startswith("    "):
                field = line.strip()
                if ":" in field:
                    key, value = field.split(":", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if value in ("|", ">", "|-", ">-"):
                        finish_content()
                        content_key = key
                        content_lines = []
                    else:
                        finish_content()
                        section[key] = value
                    continue
                if content_key:
                    content_lines.append(line[6:].rstrip())
                    continue
            if line and not line.startswith(" "):
                finish_content()
                in_sections = False

        if not in_sections:
            if line == "sections:":
                in_sections = True
                continue

            if block_key:
                if line.startswith("  "):
                    block_lines.append(stripped)
                    continue
                finish_description()
                block_key = None
                block_lines = []

            if not stripped or ":" not in stripped:
                continue

            key, value = stripped.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")

            if key == "extra" and not value:
                extra = {}
                fm["extra"] = extra
                continue
            if extra is not None and line.startswith("  "):
                extra[key] = value
                continue
            if value in ("|", ">", "|-", ">-"):
                block_key = key
                block_lines = []
                continue
            fm[key] = value

    finish_content()
    finish_description()
    if sections:
        fm["sections"] = sections

    nested = fm.get("extra", {})
    if isinstance(nested, dict):
        fm.setdefault("author", nested.get("author", ""))
        fm.setdefault("cover", nested.get("cover", ""))

    return fm, body


# ---------------------------------------------------------------------------
# home-page cards
# ---------------------------------------------------------------------------
def card_html(p: dict, label: str, path_prefix: str = "reports/") -> str:
    """One report card: the HTML comment marker, the two-cell table, trailing <br>.

    The marker is rendered verbatim (e.g. ``<!-- REPORT 1 -->``) so the rebuilt
    home matches the original source exactly.
    """
    title = p["title"] or p["slug"]
    _cover = _normalize_asset(p["cover"], p["slug"])
    if not _cover:
        img = ""
    elif re.match(r"^\s*https?://", _cover):
        img = _cover
    elif _cover.startswith("assets/"):
        img = _cover if path_prefix else "../" + _cover
    elif "/" in _cover:
        img = _cover
    else:
        img = path_prefix + p["slug"] + "/" + _cover
    href = path_prefix + p["slug"] + "/index.html"
    author = html.escape(p["author"])
    published = html.escape(display_date(p["published_raw"], p["published_key"]))
    return """      {label}
      <table width="100%" border="1" cellpadding="8" cellspacing="0" bgcolor="#f5f5f5" style="border-style: outset;">
        <tr>
          <td width="100" valign="top" align="center">
            <img src="{img}" width="80" height="80" border="2" alt="">
          </td>
          <td valign="middle">
            <font face="Times New Roman, Times, serif" size="3" color="#0000ff"><b>{title}</b></font><br>
            <font face="Times New Roman, Times, serif" size="2" color="#000000">by <font color="#ff0000"><b>{author}</b></font></font><br>
            <font face="Courier New, monospace" size="1" color="#808080">Published: {published}</font><br>
            <a href="{href}"><font face="Times New Roman, Times, serif" size="2" color="#0000ff"><u>[ READ REPORT ]</u></font></a>
          </td>
        </tr>
      </table>
      <br>""".format(
        label=label,
        img=img,
        title=html.escape(title, quote=False),
        author=author,
        published=published,
        slug=p["slug"],
        href=href,
    )


def separator() -> str:
    """A <hr class="separator"> + <br> block, no trailing newline."""
    return '      <hr class="separator">\n      <br>'


def build_home_cards(posts: list) -> str:
    """Return every report card in one date-sorted list."""
    blocks = [
        card_html(post, "<!-- REPORT {} -->".format(index + 1))
        for index, post in enumerate(posts)
    ]
    blocks.append(separator())
    return "\n\n".join(blocks) + "\n\n"


def build_archive_page(posts: list) -> str:
    cards = "\n\n".join(
        card_html(post, "<!-- REPORT {} -->".format(index + 1), path_prefix="")
        for index, post in enumerate(posts)
    )
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Reports | Horses Are Foes</title>
  <link rel="stylesheet" href="../style.css">
  <link rel="icon" href="../assets/HAF_LOGO.png">
</head>
<body>
  <div class="marquee-bar"><font face="Courier New, monospace" size="2" color="#00ff00">+++ REPORT ARCHIVE +++</font></div>
  <p><a href="../index.html">[ Home ]</a></p>
  <center><font face="Comic Sans MS, cursive" size="5" color="#0000ff"><b>REPORT ARCHIVE</b></font></center>
  <hr class="separator">
  {cards}
</body>
</html>
""".format(cards=cards)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main() -> None:
    posts: list[dict] = []

    for entry in sorted(os.listdir(REPORTS)):
        slug = entry
        path = os.path.join(REPORTS, slug)
        if not os.path.isdir(path):
            continue
        md_path = os.path.join(path, "index.md")
        html_path = os.path.join(path, "index.html")

        if os.path.exists(md_path):
            fm, body = split_front_matter(open(md_path, encoding="utf-8").read())
            html_doc = render_markdown_post(fm, body, slug)
            open(html_path, "w", encoding="utf-8").write(html_doc)
            published_raw = fm.get("published") or fm.get("date", "")
            posts.append({
                "slug": slug,
                "title": fm.get("title", slug),
                "subtitle": fm.get("subtitle") or fm.get("description", ""),
                "author": fm.get("author", "Gideon Vale"),
                "published_raw": published_raw,
                "published_key": parse_date(published_raw),
                "cover": fm.get("cover", ""),
            })
            print(f"rendered  {slug}  (markdown)")
        else:
            if not os.path.exists(html_path):
                continue
            text = open(html_path, encoding="utf-8").read()
            p = extract_metadata(slug, text)
            print(f"scanned   {slug}  ({p['title']})")
            posts.append(p)

    posts.sort(key=lambda p: p["published_key"], reverse=True)
    cards = build_home_cards(posts)
    archive_path = os.path.join(REPORTS, "index.html")
    with open(archive_path, "w", encoding="utf-8") as archive_file:
        archive_file.write(build_archive_page(posts))
    print(f"rebuilt   reports/index.html ({len(posts)} posts)")

    if not os.path.exists(HOME):
        print("home index.html not found; wrote cards to stdout instead")
        print(cards)
        return

    home = open(HOME, encoding="utf-8").read()
    # Replace only the generated card region, leaving the rest of the homepage intact.
    begin_marker = "<!-- REPORT LIST:BEGIN -->"
    end_marker = "<!-- REPORT LIST:END -->"
    start = home.find(begin_marker)
    end = home.find(end_marker)
    if start == -1 or end == -1 or end < start:
        print("home index.html missing report-list markers; wrote cards to stdout")
        print(cards)
    else:
        start += len(begin_marker)
        home = home[:start] + "\n" + cards + home[end:]
        open(HOME, "w", encoding="utf-8").write(home)
        print(f"rebuilt   index.html ({len(posts)} posts)")

    print("\nOrder (newest first):")
    for i, p in enumerate(posts, 1):
        print(f"  {i}. {p['title']}  [{human_date(p['published_key'])}]")


if __name__ == "__main__":
    main()
