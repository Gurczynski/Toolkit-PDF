# GitHub Setup

This folder is the clean GitHub-ready repo for the PDF HTML Toolkit.

If another AI or automation system needs to understand the repo structure, give it [ai_sitemap.json](C:/Users/AV/daytona-page-bundles/pdf-html-toolkit-github/ai_sitemap.json).

## Push to GitHub

```bash
cd /path/to/pdf-html-toolkit-github
git init
git add .
git commit -m "Initial PDF HTML toolkit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

## Install on your server from GitHub

Clone the repo:

```bash
git clone <your-github-repo-url> /srv/pdf-html-toolkit
cd /srv/pdf-html-toolkit
```

Create the workflow env file:

```bash
cp workflow/vps.env.example workflow/vps.env
```

Edit `workflow/vps.env` with your real paths, then run:

```bash
chmod +x workflow/run_pdf_html_workflow.sh
./workflow/run_pdf_html_workflow.sh ./workflow/vps.env
```

## Install directly with pip from the repo

You can also install the package directly from the checked-out repo:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install .
pdf-html-toolkit /srv/pdfs --output-root /srv/html-output --rules /srv/pdf-html-toolkit/render_rules.json
```

## Notes

- Commit `render_rules.json` so your problem-PDF overrides stay stable across deployments.
- Do not commit `workflow/vps.env`; it is ignored by `.gitignore`.
- Use the workflow script for repeatable server runs instead of ad hoc commands.
