# Website
Horses Are Foes website guts

# Horses Are Foes

A static website for horsesarefoes.com.

This site presents a structured investigation archive about horses, secretive hay
logistics, the CIA, demons, Bigfoot, and related anomalies. It is intended as
a documented creative dossier rather than a factual claim about real people,
organizations, agencies, animals, or cryptids.

## Publishing

The existing hand-authored HTML pages are copied through unchanged. Reports can
be authored as Markdown bundles in `reports/<slug>/index.md`; the build renders
their HTML pages and regenerates the homepage list and `/reports/` archive.

For local development, install Python 3, then run:

```powershell
python build_reports.py
python build_site.py
python -m http.server 1112 --directory public
```

Report metadata is stored in each Markdown file's YAML front matter. Put report
images in the report's folder and reference them from its Markdown body. Run
`python build_reports.py` to regenerate the report pages and archive listings.

## Shared layout

The home page (`index.html`) is the template for every page: the marquee, the
left menu/GIF sidebar, the right GIF sidebar, the banner, footer, ad banners
and age gate. To change any of these, edit `index.html`, then run
`python sync_layout.py` (or `python build_reports.py`, which runs it too).
Each page keeps its own `<head>`, breadcrumb and main content cell; everything
else is copied from the home page with links adjusted for the page's folder.

## Fonts

Pages keep the classic font names in `<font face="...">` (Times New Roman,
Courier New, Comic Sans MS), and `style.css` draws them with look-alike copies
bundled in `assets/fonts/`, so phones show the same text as desktops. In CSS,
use the `--font-serif`, `--font-mono`, `--font-comic` and `--font-sans`
variables. Any other font will look different on phones, which don't have the
desktop fonts installed.
