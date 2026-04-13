# VPS Workflow

This folder gives your VPS a repeatable conversion workflow so the same PDFs render the same way every run.

## Files

- `vps.env.example`
  Environment template for your VPS paths.
- `run_pdf_html_workflow.sh`
  Main workflow script. It creates a venv, installs the wheel or source package, runs the converter, and writes logs.
- `pdf-html-toolkit.service.example`
  Example `systemd` service unit.
- `pdf-html-toolkit.timer.example`
  Example `systemd` timer unit.

## Recommended server layout

```bash
/srv/pdf-html-toolkit
/srv/pdfs
/srv/html-output
```

## Setup

1. Upload the `Toolkit PDF` folder to `/srv/pdf-html-toolkit`.
2. Copy `workflow/vps.env.example` to `workflow/vps.env`.
3. Edit `workflow/vps.env` with your real paths.
4. Make the runner executable:

```bash
chmod +x /srv/pdf-html-toolkit/workflow/run_pdf_html_workflow.sh
```

5. Run once manually:

```bash
/srv/pdf-html-toolkit/workflow/run_pdf_html_workflow.sh /srv/pdf-html-toolkit/workflow/vps.env
```

## What the workflow does

- creates a Python virtual environment if missing
- installs or updates the wheel if present
- runs `pdf-html-toolkit` with fixed input, output, and rules paths
- writes logs to `/srv/pdf-html-toolkit/logs`
- writes `latest.log` for quick inspection
- uses a lock file when `flock` exists so two runs do not overlap

## Make it automatic with systemd

1. Copy the examples:

```bash
sudo cp /srv/pdf-html-toolkit/workflow/pdf-html-toolkit.service.example /etc/systemd/system/pdf-html-toolkit.service
sudo cp /srv/pdf-html-toolkit/workflow/pdf-html-toolkit.timer.example /etc/systemd/system/pdf-html-toolkit.timer
```

2. Reload and enable:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now pdf-html-toolkit.timer
```

3. Check status:

```bash
systemctl status pdf-html-toolkit.timer
systemctl status pdf-html-toolkit.service
tail -f /srv/pdf-html-toolkit/logs/latest.log
```

## Deterministic rendering rules

- Keep `render_rules.json` in the app directory and reuse it across runs.
- Add problem PDFs to `force_hybrid_relative_paths` or `force_image_relative_paths` instead of changing the renderer ad hoc.
- Run the same workflow script each time instead of different manual commands.
- Review `pdf_html_review.csv` after each run and only adjust rules for the files that need overrides.
