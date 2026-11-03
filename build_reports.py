#!/usr/bin/env python3
"""Build renderer for Horses Are Foes.

Turns markdown posts into HTML and rebuilds the home-page card regions so the
site always reflects every report in `reports/`.

What it does:
  * Renders `reports/<slug>/index.md`  ->  `reports/<slug>/index.html`
    (markdown posts created via the CMS).
  * Leaves hand-authored `index.html` posts untouched, but reads them for
    card metadata so old and new posts render consistently.
  * Regenerates the LATEST REPORTS (newest 3) + ARCHIVE SUMMARIES sections in
    `index.html` between the `<!-- LATEST REPORTS:BEGIN -->` /
    `<!-- ARCHIVE SUMMARIES:END -->` markers.

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
    blocks = re.split(r"\n\n+", md)
    out = []
    for block in blocks:
        lines = [ln for ln in block.split("\n")]
        if not lines or all(l.strip() == "" for l in lines):
            continue
        first = lines[0].strip()
        if first.startswith("#"):
            level = len(first) - len(first.lstrip("#"))
            level = min(max(level, 1), 3)
            out.append("<h%d>%s</h%d>" % (level, _inline(first.lstrip("#")), level))
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

    The CMS image picker can store a cover as the media path
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
    dt = parse_date(fm.get("published", ""))
    published = fm.get("published") or human_date(dt)
    body = md_to_html(body_md)

    # Cover front matter wins; fall back to the first image in the body.
    first_img = fm.get("cover", "")
    if not first_img:
        for m in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", body_md):
            first_img = m.group(1).strip()
            break
    cover_src = _normalize_asset(first_img, slug)
    # Absolute URLs are served verbatim; everything else is repo-relative.
    if not cover_src:
        og_image = LOGO
    elif re.match(r"^\s*https?://", cover_src):
        og_image = cover_src
    elif "/" in cover_src:
        og_image = DOMAIN + "/" + cover_src
    else:
        og_image = DOMAIN + "/reports/" + slug + "/" + cover_src

    warning = fm.get("warning") or ("NEW REPORT — " + title)
    subtitle = fm.get("subtitle", "")
    desc = (title + " — investigation report by " + author + ".")

    return """<html>
<head>
<title>{title} | Horses Are Foes</title>
<meta name="description" content="{desc}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="stylesheet" href="../../style.css">
<link rel="icon" href="../../assets/HAF_LOGO.png">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{og_image}">
<meta property="og:url" content="{site}/reports/{slug}/">
<meta property="og:type" content="article">
<meta property="og:site_name" content="Horses Are Foes">
<link rel="canonical" href="{site}/reports/{slug}/">
</head>

<body bgcolor="#FFFFFF" text="#000000" link="#0000CC" vlink="#663399">

<table align="center" width="100%" border="0" cellpadding="10" cellspacing="0" bgcolor="#F5F5F0">
<tr>
  <td>

    <table align="center" width="100%" border="0" cellpadding="0" cellspacing="0" bgcolor="#333300" style="border-style: inset;">
      <tr>
        <td align="center">
          <marquee behavior="scroll" scrollamount="5"
                   style="color: #FFFF66; font-family: Comic Sans MS, cursive;">
            <font face="Comic Sans MS, cursive" size="3" color="#FFFF66"><b>&#9733; {warning} &#9733;
            SUBMIT YOUR OWN REPORT &#9733; HORSES ARE FOES &#9733;</b></font>
          </marquee>
        </td>
      </tr>
    </table>

    <br>

    <center>
      <font face="Courier New, monospace" size="1" color="#333333">
        <a href="../../index.html" class="hl"><font color="#0000CC"><u>HOME</u></font></a>
        &nbsp;>&nbsp;
        <font color="#333333">REPORT</font>
        &nbsp;>&nbsp;
        <font color="#333333">{title}</font>
      </font>
    </center>

    <br>

    <table align="center" width="100%" border="0" cellpadding="5" cellspacing="0">
      <tr>
        <td width="150" valign="top" bgcolor="#F5F5F0">

          <table align="center" width="130" border="0" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center">
                <font face="Times New Roman, Times, serif" size="2" color="#333300">
                  <b>&#9733; HORSES ARE FOES &#9733;</b>
                </font>
                <br>
                <img src="../../assets/HAF_LOGO.png" alt="Horses Are Foes" width="130" height="130" border="2"
                     style="border-radius: 0px;">
              </td>
            </tr>
          </table>

          <hr size="2" noshade style="border-style: outset;">

          <center>
            <font face="Times New Roman, Times, serif" size="2" color="#333300">
              <b>&#9733; REPORTS &#9733;</b>
            </font>
          </center>
          <br>

          <ul>
            <li><font face="Times New Roman, Times, serif" size="2"><a href="../top-5-underground-horse-cities/index.html" class="hl"><u>Underground Horse Cities</u></a></font></li>
            <li><font face="Times New Roman, Times, serif" size="2"><a href="../faerie-lights-swamp-gas/index.html" class="hl"><u>Faerie Lights &amp; Swamp Gas</u></a></font></li>
            <li><font face="Times New Roman, Times, serif" size="2"><a href="../the-dust/index.html" class="hl"><u>The Dust</u></a></font></li>
          </ul>

          <hr size="2" noshade style="border-style: outset;">

          <center>
            <font face="Times New Roman, Times, serif" size="2" color="#333300">
              <b>&#9733; ARCHIVE &#9733;</b>
            </font>
          </center>
          <br>
          <center>
            <table border="0" cellpadding="4" cellspacing="0" style="border-style: outset;">
              <tr><td align="center"><img src="../../assets/HAF_LOGO.png" alt="Horses Are Foes" width="100" height="100" border="1"></td></tr>
              <tr><td align="center"><font face="Times New Roman, Times, serif" size="1">EST. 1998</font></td></tr>
            </table>
          </center>

        </td>

        <td valign="top" bgcolor="#FFFFFF">

          <center>
            <font face="Comic Sans MS, cursive" size="4" color="#0000ff"><b>&#9733; REPORT BY &#9733;</b></font>
          </center>
          <center>
            <font face="Times New Roman, Times, serif" size="3" color="#333300"><b>{author}</b></font><br>
            <font face="Courier New, monospace" size="1" color="#808080">Investigator, Horses Are Foes</font><br>
            <font face="Courier New, monospace" size="1" color="#808080">Published: {published}</font>
            <br>
          </center>

          <hr class="separator">

          <center>
            <table width="100%" align="center" border="0" cellpadding="5" cellspacing="0"
                   style="border-collapse: collapse;">
              <tr>
                <td align="center">
                  <font face="Comic Sans MS, cursive" size="5" color="#333300"><b>&#9733;</b></font>
                  <br>
                  <font face="Comic Sans MS, cursive" size="5" color="#333300"><b>{title}</b></font>
                  {subtitle_line}
                  <br>
                  <font face="Comic Sans MS, cursive" size="5" color="#333300"><b>&#9733;</b></font>
                </td>
              </tr>
            </table>
          </center>

          <hr class="separator">

          <br>

          <center>
            <table align="center" width="90%" border="0" cellpadding="5" cellspacing="0" bgcolor="#FFFFFF">
              <tr>
                <td>
                  {body}
                </td>
              </tr>
            </table>
          </center>

          <br>

          <hr class="separator">

          <br>
          <center>
            <font face="Comic Sans MS, cursive" size="4" color="#0000ff"><b>&#9733; REPORT BY &#9733;</b></font>
          </center>
          <br>

          <br>

        </td>

        <td width="150" valign="top" bgcolor="#F5F5F0"
             style="border-left: 2px dashed #999999;">
        </td>
      </tr>
    </table>

    <br>

    <center>
      <table align="center" width="80%" border="0" cellpadding="0" cellspacing="0"
             bgcolor="#FFFF00" style="border-style: inset;">
        <tr>
          <td>
            <table align="center" width="100%" border="0" cellpadding="8" cellspacing="0" bgcolor="#FFFF00"
                   style="border-style: inset;">
              <tr>
                <td align="center">
                  <font face="Comic Sans MS, cursive" size="3" color="#333300"><b>&#9733; REPORT &#9733;</b></font>
                  <br>
                  <table align="center" width="300" border="0" cellpadding="4" cellspacing="0">
                    <tr>
                      <td align="right" width="60"><font face="Times New Roman, Times, serif" size="2">Report by:</font></td>
                      <td align="left"><font face="Times New Roman, Times, serif" size="2" color="#333300"><b>{author}</b></font></td>
                    </tr>
                    <tr>
                      <td align="right"><font face="Courier New, monospace" size="1" color="#808080">Published:</font></td>
                      <td align="left"><font face="Courier New, monospace" size="1" color="#808080">{published}</font></td>
                    </tr>
                  </table>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </center>

    <br>

    <table align="center" width="100%" border="1" cellpadding="5" cellspacing="0"
           bgcolor="#FFFF99" style="border-style: inset;">
      <tr>
        <td align="center">
          <table align="center" width="90%" border="0" cellpadding="6" cellspacing="0">
            <tr>
              <td width="100" align="center" valign="middle">
                <font face="Comic Sans MS, cursive" size="3" color="#0000ff"><b>&#9733;</b></font>
              </td>
              <td valign="middle">
                <font face="Comic Sans MS, cursive" size="3" color="#0000ff"><b>&#9733;
                REPORT &#9733; &#9733; &#9733;</b></font>
              </td>
              <td width="100" align="center" valign="middle">
                <font face="Comic Sans MS, cursive" size="3" color="#0000ff"><b>&#9733;</b></font>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>

    <br>

    <hr class="separator">

    <br>

    <center>
      <table align="center" width="90%" border="0" cellpadding="5" cellspacing="0"
           style="border-collapse: collapse;">
        <tr>
          <td width="50%" align="left" valign="middle">
            <table align="center" border="0" cellpadding="6" cellspacing="0" bgcolor="#FFFF00"
                   style="border-style: outset;">
              <tr>
                <td>
                  <font face="Comic Sans MS, cursive" size="3" color="#0000ff">
                    <a href="../" class="hl"><font color="#0000ff"><b>&#9733; RETURN TO REPORTS &#9733;</b></font></a>
                  </font>
                </td>
              </tr>
            </table>
          </td>
          <td width="50%" align="right" valign="middle">
            <font face="Courier New, monospace" size="1" color="#808080">
              A Horses Are Foes Production &copy; 1998-2026. All horses reserved.
            </font>
          </td>
        </tr>
      </table>
    </center>

    <br>

    <hr class="separator">

    <br>

    <table align="center" width="100%" border="0" cellpadding="8" cellspacing="0" bgcolor="#FFFF99" style="border-style: inset;">
      <tr>
        <td align="center">
          <table align="center" width="100%" border="0" cellpadding="5" cellspacing="0">
            <tr>
              <td align="left" width="100" valign="top">
                <table align="center" border="0" cellpadding="3" cellspacing="0" style="border-style: inset;">
                  <tr>
                    <td><a href="../../index.html" class="hl"><font face="Comic Sans MS, cursive" size="2" color="#333300"><b>&#9733; &#9733; HORSERS ARE FOES &#9733; &#9733;</b></font></a></td>
                  </tr>
                </table>
              </td>
              <td align="center" width="100" valign="top">
                <table align="center" border="0" cellpadding="3" cellspacing="0" style="border-style: inset;">
                  <tr>
                    <td align="center"><font face="Comic Sans MS, cursive" size="2" color="#333300"><b>&#9733; &#9733; ABOUT &#9733; &#9733;</b></font></td>
                  </tr>
                  <tr>
                    <td align="center"><img src="../../assets/HAF_LOGO.png" alt="Horses Are Foes" width="80" height="80" border="1"></td>
                  </tr>
                </table>
              </td>
              <td align="right" width="100" valign="top">
                <table align="center" border="0" cellpadding="3" cellspacing="0" style="border-style: inset;">
                  <tr>
                    <td align="right"><font face="Comic Sans MS, cursive" size="2" color="#333300"><b>&#9733; &#9733; &#9733; &#9733; &#9733;</b></font></td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </td>
      </tr>
      <tr>
        <td align="center">
          <hr size="2" noshade style="border-style: outset;">
        </td>
      </tr>
      <tr>
        <td align="center">
          <font face="Courier New, monospace" size="1" color="#808080">
            This page is part of the Horses Are Foes network. &copy; 1998-2026 All horses reserved.
          </font>
        </td>
      </tr>
    </table>

    <br>

    <table align="center" width="80%" border="0" cellpadding="0" cellspacing="0">
      <tr>
        <td align="center">
          <center>
            <font face="Times New Roman, Times, serif" size="2">
              <br>
              <a href="../../index.html" class="hl"><font color="#0000CC"><b>&#9733; HOME</b></font></a>
              &nbsp;|&nbsp;
              <font color="#333333">Report archive</font>
              <br>
              <br>
            </font>
          </center>
        </td>
      </tr>
    </table>

    <br>

    <div id="counter" align="center">
      <table border="0" cellpadding="0" cellspacing="0" align="center">
        <tr>
          <td align="center">
            <font face="Courier New, monospace" size="1" color="#808080">VISITORS:</font><br>
            <table border="2" cellpadding="3" cellspacing="0" bgcolor="#333333" align="center"
                   style="border-style: inset;">
              <tr>
                <td align="center"><font face="Courier New, monospace" size="4" color="#00FF00">00004206</font></td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </div>

    <br>

    <center>
      <font face="Times New Roman, Times, serif" size="1" color="#333333">
        This page is part of the Horses Are Foes network.
      </font>
    </center>

    <br>

    <center>
      <font face="Courier New, monospace" size="1" color="#333333">
        <br>
        This site is optimised to be viewed at 800 x 600 resolution.
        <br>
        Best viewed with any 256-colour browser.
        <br>
        &copy; 1998-2026 Horses Are Foes. All horses reserved.
        <br>
        <br>
        You are visitor number
        <font color="#FF0000"><b>00004206</b></font>
        to this page.
        <br>
        <br>
      </font>
    </center>

  </td>
</tr>
</table>

<script>
  try {{
    var ref = document.referrer;
    var img = new Image();
    img.src = "../../cgi-bin/counter.gif?ref=" + encodeURIComponent(ref);
  }} catch (e) {{}}
</script>

</body>
</html>""".format(
        title=html.escape(title),
        author=html.escape(author),
        published=html.escape(published),
        warning=html.escape(warning),
        subtitle_line=("<br>" + html.escape(subtitle) if subtitle else ""),
        body=body,
        site=DOMAIN,
        slug=slug,
        og_image=html.escape(og_image),
        desc=html.escape(desc),
    )


# ---------------------------------------------------------------------------
# front matter parsing (simple YAML subset)
# ---------------------------------------------------------------------------
def split_front_matter(text: str):
    """Return (front_matter_dict, body_md) from a markdown file."""
    fm, body = {}, text
    if text.startswith("---"):
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", text, re.S)
        if m:
            raw_body = m.group(2)
            for line in m.group(1).split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip().strip('"').strip("'")
            body = raw_body
    return fm, body


# ---------------------------------------------------------------------------
# home-page cards
# ---------------------------------------------------------------------------
def card_html(p: dict, label: str) -> str:
    """One report card: the HTML comment marker, the two-cell table, trailing <br>.

    The marker is rendered verbatim (e.g. ``<!-- REPORT 1 -->``) so the rebuilt
    home matches the original source exactly.
    """
    title = p["title"] or p["slug"]
    _cover = _normalize_asset(p["cover"], p["slug"])
    if not _cover:
        img = ""
    elif re.match(r"^\s*https?://", _cover) or "/" in _cover:
        img = _cover
    else:
        img = "reports/" + p["slug"] + "/" + _cover
    author = html.escape(p["author"])
    published = html.escape(p["published_raw"] or human_date(p["published_key"]))
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
            <a href="reports/{slug}/index.html"><font face="Times New Roman, Times, serif" size="2" color="#0000ff"><u>[ READ REPORT ]</u></font></a>
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
    )


def header_section(title: str, size: int) -> str:
    """Faithful rendering of a card-section header."""
    return """      <center>
        <font face="Comic Sans MS, cursive" size="{size}" color="#0000ff"><b>&#9733; {hdr} &#9733;</b></font>
      </center>
      <br>""".format(hdr=html.escape(title), size=size)


def separator() -> str:
    """A <hr class="separator"> + <br> block, no trailing newline."""
    return '      <hr class="separator">\n      <br>'


def build_home_cards(posts: list) -> str:
    """Newest 3 -> LATEST REPORTS; the rest -> ARCHIVE SUMMARIES.

    Returns the card region: LATEST header, three cards, a separator, the
    ARCHIVE header, two cards, and a trailing separator. Each element is joined
    by a single blank line, mirroring the committed home page. The region ends
    with a blank line so main() can splice it just before the closing </td>.
    """
    blocks: list = [header_section("LATEST REPORTS", 4)]
    for i, p in enumerate(posts):
        if i == 3:
            blocks.append(separator())
            blocks.append(header_section("ARCHIVE SUMMARIES", 3))
        blocks.append(card_html(p, "<!-- REPORT {} -->".format(i + 1)))
    blocks.append(separator())
    return "\n\n".join(blocks) + "\n\n"


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
            posts.append({
                "slug": slug,
                "title": fm.get("title", slug),
                "subtitle": fm.get("subtitle", ""),
                "author": fm.get("author", "Gideon Vale"),
                "published_raw": fm.get("published", ""),
                "published_key": parse_date(fm.get("published", "")),
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

    if not os.path.exists(HOME):
        print("home index.html not found; wrote cards to stdout instead")
        print(cards)
        return

    home = open(HOME, encoding="utf-8").read()
    # Splice between the LATEST REPORTS <center> header and the main body's
    # closing </td> so no BEGIN/END markers are needed. home[:start] keeps the
    # brand header above; home[end:] keeps the sidebar below.
    star_idx = home.find("&#9733; LATEST REPORTS")
    if star_idx == -1:
        print("home index.html missing the LATEST REPORTS header; wrote cards to stdout")
        print(cards)
    else:
        # Splice with exact line anchors (no BEGIN/END markers). Build the
        # committed page as lines: the "      <center>" opening the LATEST
        # banner sits just above the banner, and the main content column closes
        # at the first exact 4-space "    </td>" after it. This avoids the old
        # substring matches that hit nested card </td> or the wrong <center>.
        lines = home.split("\n")
        banner = next(i for i, l in enumerate(lines) if "LATEST REPORTS" in l)
        start = next(i for i in range(banner, -1, -1) if lines[i] == "      <center>")
        end = next(i for i in range(banner, len(lines)) if lines[i] == "    </td>")
        cards_lines = cards.split("\n")
        while cards_lines and cards_lines[-1] == "":
            cards_lines.pop()
        cards_lines.append("")
        home = "\n".join(lines[:start] + cards_lines + lines[end:])
        open(HOME, "w", encoding="utf-8").write(home)
        print(f"rebuilt   index.html ({len(posts)} posts)")

    print("\nOrder (newest first):")
    for i, p in enumerate(posts, 1):
        print(f"  {i}. {p['title']}  [{human_date(p['published_key'])}]")


if __name__ == "__main__":
    main()
