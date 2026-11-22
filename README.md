# Website
Horses Are Foes website guts

# Horses Are Foes

A static website for horsesarefoes.com.

This site presents a structured investigation archive about horses, secretive hay
logistics, the CIA, demons, Bigfoot, and related anomalies. It is intended as
a documented creative dossier rather than a factual claim about real people,
organizations, agencies, animals, or cryptids.

## Publishing

The existing hand-authored HTML pages are copied through unchanged. New reports
are written as Markdown in `content/reports/`, rendered by Zola, and listed at
`/reports/`. Report metadata and images can be edited through Pages CMS at
https://app.pagescms.org after signing in with GitHub and granting it access to
this repository.

For local development, install Zola 0.23.6 and Python 3.13, then run:

```powershell
$env:DEPLOY_PRIME_URL = "http://127.0.0.1:1112"
python build_reports.py
python build_site.py
python -m http.server 1112 --directory public
```

Pages CMS stores uploaded images in `assets/`. New reports use the `title`,
`date`, `description`, `author`, `cover image`, and report body fields.
