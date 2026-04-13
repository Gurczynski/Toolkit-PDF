# Lovable Prompt

Use the `pdf-html-toolkit` package on the connected VPS to convert PDFs into HTML that visually matches the source PDF page-for-page.

Requirements:

- Keep every PDF page at the original page size.
- Preserve page count, reading order, vectors, and embedded images.
- Use semantic positioned text only when stable.
- If text extraction causes overlap or clipping, keep the page visually accurate by using the toolkit's preview fallback for that page.
- Keep inline CSS, inline JS, transcript markup, and accessibility attributes intact.
- Do not redesign the document into a generic webpage.
- Do not remove page navigation, transcript support, or WCAG-oriented labels.
- Use `render_rules.json` so problem PDFs render the same way every time.

VPS execution:

1. Upload the wheel or source package to the VPS.
2. Set up `workflow/vps.env` on the VPS.
3. Run the packaged workflow script:

```bash
/srv/pdf-html-toolkit/workflow/run_pdf_html_workflow.sh /srv/pdf-html-toolkit/workflow/vps.env
```

4. If a PDF still has layout problems, add an override to `render_rules.json` and rerun the workflow.

Success condition:

- Generated HTML looks like the PDF.
- Transcript text exists per page when extractable.
- Accessibility tools can identify each page as a labeled region with transcript support.
- Output is stable and repeatable across runs.
