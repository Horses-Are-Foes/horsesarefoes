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

For local development, install Python 3.13, then run:

```powershell
$env:DEPLOY_PRIME_URL = "http://127.0.0.1:1112"
python build_reports.py
python build_site.py
python -m http.server 1112 --directory public
```

Report metadata is stored in each Markdown file's YAML front matter. Put report
images in the report's folder and reference them from its Markdown body. Run
`python build_reports.py` to regenerate the report pages and archive listings.
