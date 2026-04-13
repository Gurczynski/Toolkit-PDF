from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import html
import json
import re
from pathlib import Path

import fitz
from pypdf import PdfReader


SCRIPT_DIR = Path(__file__).resolve().parent
SCALE = 96 / 72
FALLBACK_RENDER_SCALE = 2.5
DEFAULT_RULES_PATH = SCRIPT_DIR / "render_rules.json"
PDF_VIEWER_CSS = """
html,body{margin:0;padding:0;background:#fff;color:#111827;font:16px/1.5 "Segoe UI",Tahoma,Arial,sans-serif}
body{min-height:100vh}
body.high-contrast{background:#000;color:#fff}
body.readable-font{font-family:Arial,Helvetica,sans-serif}
a{color:inherit;text-decoration:none}a:hover{text-decoration:underline}
button,input{font:inherit}
.sr-only{position:absolute!important;width:1px!important;height:1px!important;padding:0!important;margin:-1px!important;overflow:hidden!important;clip:rect(0,0,0,0)!important;white-space:nowrap!important;border:0!important}
.hidden{display:none!important}
.skip-link{position:absolute;left:12px;top:12px;transform:translateY(-180%);background:#fff;color:#111827;padding:10px 14px;border-radius:10px;z-index:1000}
.skip-link:focus{transform:translateY(0)}
.pdf-shell{width:100%;max-width:none;margin:0;padding:0}
.viewer{background:#fff;border:0;border-radius:0;box-shadow:none;overflow:hidden;min-height:100vh}
.viewer.sidebar-collapsed .viewer-body{grid-template-columns:minmax(0,1fr) 300px}
.viewer.sidebar-collapsed .sidebar{display:none}
.viewer.tools-collapsed .viewer-body{grid-template-columns:220px minmax(0,1fr)}
.viewer.tools-collapsed .tools{display:none}
.topbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 14px;background:#2b2f35;border-bottom:1px solid #1c1f24}
.brand{display:flex;align-items:center;gap:12px;min-width:0}
.brand__badge{width:28px;height:28px;border-radius:8px;background:#e53935;color:#fff;display:grid;place-items:center;font-weight:800}
.brand__title{font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:#f9fafb}
.brand__sub{font-size:12px;color:#aeb8c4}
.top-actions,.toolbar-actions,.mode-toggle,.page-nav,.zoom-controls,.tool-group{display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.topbar,.toolbar,.sidebar,.tools,.sidebar__head,.tools__head,.thumb-link,.transcript-list summary,.transcript-list pre,.tools__body,.tools__body p,.tools__body li,.tools__body label{color:#f3f4f6}
.ui-btn,.ui-link,.page-input,.zoom-select{display:inline-flex;align-items:center;justify-content:center;min-height:34px;padding:0 12px;border-radius:9px;border:1px solid #4a5058;background:#3b4149;color:#f3f4f6}
.ui-btn[aria-pressed="true"],.ui-btn.active{background:#4b5563;border-color:#6b7280;color:#fff}
.ui-btn:hover,.ui-link:hover{background:#4a5058;text-decoration:none}
.toolbar{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 14px;background:#3a3f46;border-bottom:1px solid #2a2e34}
.page-input,.zoom-select{width:72px;padding:0 8px;text-align:center}
.viewer-body{display:grid;grid-template-columns:220px minmax(0,1fr) 300px;min-height:calc(100vh - 150px);background:#fff}
.sidebar,.tools{background:#3a3f46;border-right:1px solid #2a2e34;overflow:auto}
.tools{border-right:0;border-left:1px solid #2a2e34}
.sidebar__head,.tools__head{padding:14px 16px;border-bottom:1px solid #2a2e34;font-weight:700}
.thumb-list,.tools__body,.transcript-list{padding:14px;display:grid;gap:12px}
.thumb-link{display:grid;gap:6px;padding:10px;border-radius:12px;border:1px solid #4a5058;background:#444a53;color:#e5e7eb}
.thumb-link.active{outline:2px solid #d1d5db}
.thumb-link span{font-size:12px;color:#b9c2cf}
.viewer-main{overflow:auto;background:#fff}
.mode-panels{position:relative;height:100%}
.mode-panel{height:100%}
.viewer-stage{padding:22px 24px 32px;background:#fff}
.page-stack{display:grid;gap:26px;justify-content:stretch;transform-origin:top center}
.page-card{width:100%;display:grid;justify-items:center}
.page-label{font-size:13px;color:#374151;margin:0 0 8px;justify-self:start;width:min(100%,816px)}
.pdf-page{position:relative;background:#fff;box-shadow:0 12px 28px rgba(0,0,0,.18);overflow:hidden}
.pdf-page:focus-visible{outline:3px solid #111827;outline-offset:3px}
.pdf-page img,.pdf-page svg{position:absolute;display:block}
.vector-layer,.image-layer,.text-layer{position:absolute;inset:0}
.text-layer{z-index:3}
.text-layer--assistive{opacity:.015}
.text-span{position:absolute;display:block;white-space:pre;transform-origin:top left;color:#111;line-height:1;overflow:visible;text-rendering:geometricPrecision;box-sizing:border-box;padding:0 6px 2px 0}
.page-fallback{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
.page-outline{position:absolute;inset:0;border:1px solid rgba(0,0,0,.08);pointer-events:none}
.pdf-frame{width:100%;height:calc(100vh - 170px);border:0;background:#fff}
.tools .ui-btn{justify-content:flex-start}
.tools__body .tool-row{display:grid;gap:8px}
.tools__body ul{margin:0;padding-left:18px}
.transcript-list details{background:#444a53;border:1px solid #555c66;border-radius:12px;padding:10px 12px}
.transcript-list summary{cursor:pointer;font-weight:700}
.transcript-list pre{white-space:pre-wrap;word-break:break-word;font:13px/1.45 Consolas,"Courier New",monospace}
.back-top{position:fixed;right:18px;bottom:18px;z-index:40;border:1px solid #4a5058;background:#2b2f35;color:#fff;border-radius:999px;padding:10px 14px;box-shadow:0 12px 28px rgba(0,0,0,.22)}
.back-top:hover{background:#3b4149}
body.high-contrast .viewer{background:#111;border-color:#000}
body.high-contrast .topbar,body.high-contrast .toolbar,body.high-contrast .sidebar,body.high-contrast .tools{background:#111;color:#fff}
body.high-contrast .ui-btn,body.high-contrast .ui-link,body.high-contrast .page-input,body.high-contrast .zoom-select,body.high-contrast .thumb-link,body.high-contrast .back-top{background:#000;border-color:#fff;color:#fff}
body.high-contrast .pdf-page{box-shadow:0 0 0 2px #fff}
@media(max-width:1180px){.viewer-body{grid-template-columns:180px minmax(0,1fr)}.tools{display:none}}
@media(max-width:860px){.viewer-body,.viewer.sidebar-collapsed .viewer-body,.viewer.tools-collapsed .viewer-body{grid-template-columns:1fr}.sidebar,.tools{display:none}.toolbar{align-items:flex-start;flex-direction:column}.topbar{align-items:flex-start;flex-direction:column}.pdf-frame{height:70vh}}
"""

PDF_VIEWER_JS = """
(function(){
  const viewer = document.querySelector('.viewer');
  const pageInput = document.getElementById('page-input');
  const pageTotal = Number(document.body.dataset.totalPages || '1');
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const zoomIn = document.getElementById('zoom-in');
  const zoomOut = document.getElementById('zoom-out');
  const fitWidth = document.getElementById('fit-width');
  const fitPage = document.getElementById('fit-page');
  const actualSize = document.getElementById('actual-size');
  const zoomSelect = document.getElementById('zoom-select');
  const zoomLabel = document.getElementById('zoom-label');
  const pageStack = document.getElementById('page-stack');
  const viewerMain = document.getElementById('viewer-main');
  const pagesToggle = document.getElementById('toggle-pages');
  const toolsToggle = document.getElementById('toggle-tools');
  const toolsPanel = document.getElementById('tools-panel');
  const transcriptToggle = document.getElementById('toggle-transcript');
  const transcriptPanel = document.getElementById('transcript-panel');
  const transcriptList = document.getElementById('transcript-list');
  const contrastToggle = document.getElementById('toggle-contrast');
  const readableToggle = document.getElementById('toggle-readable');
  const resetBtn = document.getElementById('reset-view');
  const viewerStatus = document.getElementById('viewer-status');
  const backTop = document.getElementById('back-to-top');
  const thumbs = Array.from(document.querySelectorAll('.thumb-link'));
  let currentPage = 1;
  let zoom = 1;

  function clampPage(n){ return Math.max(1, Math.min(pageTotal, n || 1)); }
  function setExpanded(button, expanded){
    if (!button) return;
    button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    button.setAttribute('aria-pressed', expanded ? 'true' : 'false');
  }
  function setPressed(button, pressed){
    if (!button) return;
    button.setAttribute('aria-pressed', pressed ? 'true' : 'false');
  }
  function syncPanelButtons(){
    if (!viewer) return;
    setExpanded(pagesToggle, !viewer.classList.contains('sidebar-collapsed'));
    setExpanded(toolsToggle, !viewer.classList.contains('tools-collapsed'));
    const transcriptOpen = transcriptPanel && !transcriptPanel.classList.contains('hidden');
    setExpanded(transcriptToggle, Boolean(transcriptOpen));
  }
  function syncPreferenceButtons(){
    setPressed(contrastToggle, document.body.classList.contains('high-contrast'));
    setPressed(readableToggle, document.body.classList.contains('readable-font'));
  }
  function updateStatus(){
    if (!viewerStatus) return;
    viewerStatus.textContent = 'HTML page ' + currentPage + ', ' + Math.round(zoom * 100) + '% zoom';
  }
  function updateZoomUi(){
    if (zoomLabel) zoomLabel.textContent = Math.round(zoom * 100) + '%';
    if (zoomSelect) zoomSelect.value = String(Math.round(zoom * 100));
  }
  function syncButtons(){
    thumbs.forEach(link => link.classList.toggle('active', Number(link.dataset.page) === currentPage));
    updateStatus();
  }
  function scrollToPage(page){
    currentPage = clampPage(page);
    pageInput.value = String(currentPage);
    const el = document.getElementById('page-' + currentPage);
    if (el) el.scrollIntoView({behavior:'smooth', block:'start'});
    syncButtons();
  }
  function scrollToTop(){
    currentPage = 1;
    pageInput.value = '1';
    if (viewerMain) {
      viewerMain.scrollTo({top: 0, behavior: 'smooth'});
    }
    window.scrollTo({top: 0, behavior: 'smooth'});
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
    syncButtons();
  }
  function applyZoom(){
    if (!pageStack) return;
    pageStack.style.zoom = String(zoom);
    updateZoomUi();
    updateStatus();
  }
  function fitToWidth(){
    const page = document.querySelector('.pdf-page');
    if (!page) return;
    const width = page.getBoundingClientRect().width / zoom;
    const target = Math.max(0.5, Math.min(2.25, (viewerMain.clientWidth - 48) / width));
    zoom = target;
    applyZoom();
  }
  function fitToPage(){
    const page = document.querySelector('.pdf-page');
    if (!page) return;
    const width = page.getBoundingClientRect().width / zoom;
    const height = page.getBoundingClientRect().height / zoom;
    const widthZoom = (viewerMain.clientWidth - 48) / width;
    const heightZoom = (viewerMain.clientHeight - 72) / height;
    zoom = Math.max(0.5, Math.min(2.25, Math.min(widthZoom, heightZoom)));
    applyZoom();
  }
  prevBtn.addEventListener('click', () => scrollToPage(currentPage - 1));
  nextBtn.addEventListener('click', () => scrollToPage(currentPage + 1));
  pageInput.addEventListener('change', () => scrollToPage(Number(pageInput.value)));
  zoomIn.addEventListener('click', () => { zoom = Math.min(2.25, zoom + 0.1); applyZoom(); });
  zoomOut.addEventListener('click', () => { zoom = Math.max(0.5, zoom - 0.1); applyZoom(); });
  fitWidth.addEventListener('click', fitToWidth);
  if (fitPage) fitPage.addEventListener('click', fitToPage);
  if (actualSize) actualSize.addEventListener('click', () => { zoom = 1; applyZoom(); });
  if (zoomSelect) zoomSelect.addEventListener('change', () => {
    const nextZoom = Number(zoomSelect.value) / 100;
    if (!Number.isFinite(nextZoom)) return;
    zoom = Math.max(0.5, Math.min(2.25, nextZoom));
    applyZoom();
  });
  if (pagesToggle) pagesToggle.addEventListener('click', () => {
    viewer.classList.toggle('sidebar-collapsed');
    syncPanelButtons();
  });
  toolsToggle.addEventListener('click', () => {
    viewer.classList.toggle('tools-collapsed');
    syncPanelButtons();
  });
  transcriptToggle.addEventListener('click', () => {
    transcriptPanel.classList.toggle('hidden');
    transcriptList.classList.toggle('hidden');
    syncPanelButtons();
  });
  contrastToggle.addEventListener('click', () => {
    document.body.classList.toggle('high-contrast');
    syncPreferenceButtons();
  });
  readableToggle.addEventListener('click', () => {
    document.body.classList.toggle('readable-font');
    syncPreferenceButtons();
  });
  resetBtn.addEventListener('click', () => {
    zoom = 1;
    applyZoom();
    document.body.classList.remove('high-contrast','readable-font');
    transcriptPanel.classList.add('hidden');
    transcriptList.classList.add('hidden');
    viewer.classList.remove('sidebar-collapsed','tools-collapsed');
    syncPreferenceButtons();
    syncPanelButtons();
    scrollToTop();
  });
  if (backTop) backTop.addEventListener('click', scrollToTop);
  thumbs.forEach(link => link.addEventListener('click', (ev) => { ev.preventDefault(); scrollToPage(Number(link.dataset.page)); }));
  const observer = new IntersectionObserver((entries) => {
    const visible = entries.filter(entry => entry.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];
    if (!visible) return;
    currentPage = clampPage(Number(visible.target.dataset.page));
    pageInput.value = String(currentPage);
    syncButtons();
  }, {root: viewerMain, threshold: [0.55, 0.8]});
  document.querySelectorAll('.page-card').forEach(card => observer.observe(card));
  pageInput.value = '1';
  syncPanelButtons();
  syncPreferenceButtons();
  syncButtons();
  fitToPage();
  window.addEventListener('resize', fitToPage);
})();
"""


def sha1(path: Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def esc(value: str) -> str:
    return html.escape(value or "", quote=True)


def default_rules() -> dict[str, list[str]]:
    return {
        "force_hybrid_relative_paths": [],
        "force_image_relative_paths": [],
        "force_semantic_relative_paths": [],
    }


def load_rules(path: Path | None) -> dict[str, list[str]]:
    rules = default_rules()
    if path is None or not path.exists():
        return rules
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        return rules
    for key in rules:
        values = loaded.get(key, [])
        if isinstance(values, list):
            rules[key] = [str(item).replace("\\", "/") for item in values]
    return rules


def normalize_rule_path(value: str) -> str:
    return str(value or "").replace("\\", "/").lower().strip("/")


def relative_key(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def forced_mode_for_path(pdf_path: Path, root: Path, rules: dict[str, list[str]]) -> str | None:
    key = normalize_rule_path(relative_key(pdf_path, root))
    full_key = normalize_rule_path(pdf_path.as_posix())
    name_key = normalize_rule_path(pdf_path.name)

    def matches(rule_values: list[str]) -> bool:
        normalized_rules = {normalize_rule_path(value) for value in rule_values}
        if key in normalized_rules or full_key in normalized_rules or name_key in normalized_rules:
            return True
        return any(full_key.endswith(rule) or key.endswith(rule) for rule in normalized_rules if rule)

    if matches(rules["force_image_relative_paths"]):
        return "image"
    if matches(rules["force_hybrid_relative_paths"]):
        return "hybrid"
    if matches(rules["force_semantic_relative_paths"]):
        return "semantic"
    return None


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "pdf"


def prettify_name(name: str) -> str:
    text = re.sub(r"[-_]+", " ", name).strip()
    text = re.sub(r"\s+", " ", text)
    return text.title() if text else "PDF Document"


def color_from_int(value: int | None) -> str:
    if value is None:
        return "none"
    return f"rgb({(value >> 16) & 255}, {(value >> 8) & 255}, {value & 255})"


def color_from_tuple(value: tuple[float, float, float] | None) -> str:
    if value is None:
        return "none"
    return f"rgb({round(value[0] * 255)}, {round(value[1] * 255)}, {round(value[2] * 255)})"


def mime_for_ext(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext in {"jpg", "jpeg"}:
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    if ext == "svg":
        return "image/svg+xml"
    if ext == "gif":
        return "image/gif"
    if ext == "webp":
        return "image/webp"
    return "application/octet-stream"


def data_uri(data: bytes, ext: str) -> str:
    mime = mime_for_ext(ext)
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def css_font_family(name: str) -> str:
    lowered = (name or "").lower()
    if "arial" in lowered or "helvetica" in lowered:
        return "Arial, Helvetica, sans-serif"
    if "times" in lowered:
        return "'Times New Roman', Times, serif"
    if "courier" in lowered:
        return "'Courier New', Courier, monospace"
    if "symbol" in lowered:
        return "Symbol, sans-serif"
    return "'Segoe UI', Tahoma, Arial, sans-serif"


def font_weight(name: str, flags: int) -> str:
    lowered = (name or "").lower()
    return "700" if "bold" in lowered or (flags & 16) else "400"


def font_style(name: str, flags: int) -> str:
    lowered = (name or "").lower()
    return "italic" if "italic" in lowered or "oblique" in lowered or (flags & 2) else "normal"


def pt(x: float) -> str:
    return f"{x * SCALE:.2f}"


def extract_linear_text(page: fitz.Page) -> str:
    return normalize_plain_text(page.get_text("text"))


def normalize_plain_text(text: str) -> str:
    cleaned = (text or "").replace("\x00", "").replace("\u00ad", "")
    cleaned = re.sub(r"\r\n?", "\n", cleaned)
    cleaned = re.sub(r"[ \t\f\v]+", " ", cleaned)
    cleaned = re.sub(r" *\n *", "\n", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def text_quality_metrics(text: str) -> tuple[int, int, int]:
    printable = sum(1 for ch in text if ch.isprintable() and not ch.isspace())
    alpha_numeric = sum(1 for ch in text if ch.isalnum())
    lines = text.count("\n") + 1 if text else 0
    return printable, alpha_numeric, lines


def text_quality_score(text: str) -> int:
    printable, alpha_numeric, lines = text_quality_metrics(text)
    return (alpha_numeric * 3) + printable + min(lines, 25) * 5


def is_reliable_text(text: str) -> bool:
    printable, alpha_numeric, lines = text_quality_metrics(text)
    if not text or printable < 8:
        return False
    ratio = alpha_numeric / max(printable, 1)
    return ratio >= 0.2 or (printable >= 32 and lines >= 2)


def transcript_fallback(page_number: int) -> str:
    return (
        f"Plain-text transcript was not available for page {page_number}. "
        "The page is still exposed as an accessible HTML region with labeled navigation and page context."
    )


def choose_transcript_text(page_number: int, *candidates: str) -> str:
    normalized = [normalize_plain_text(candidate) for candidate in candidates if candidate]
    normalized = [candidate for candidate in normalized if candidate]
    if not normalized:
        return transcript_fallback(page_number)
    reliable = [candidate for candidate in normalized if is_reliable_text(candidate)]
    if reliable:
        return max(reliable, key=text_quality_score)
    best_available = max(normalized, key=text_quality_score)
    if text_quality_score(best_available) >= 24:
        return best_available
    return transcript_fallback(page_number)


def extract_reader_page_texts(pdf_path: Path, page_count: int) -> list[str]:
    texts = [""] * page_count
    try:
        reader = PdfReader(str(pdf_path))
        for index, reader_page in enumerate(reader.pages):
            if index >= page_count:
                break
            texts[index] = normalize_plain_text(reader_page.extract_text() or "")
    except Exception:
        return texts
    return texts


def sanitize_accessible_text(text: str, page_number: int) -> str:
    return choose_transcript_text(page_number, text)


def drawing_to_svg(drawing: dict) -> str:
    items = drawing.get("items") or []
    fill = color_from_tuple(drawing.get("fill"))
    stroke = color_from_tuple(drawing.get("color"))
    width = (drawing.get("width") or 1) * SCALE
    fill_opacity = drawing.get("fill_opacity", 1)
    stroke_opacity = drawing.get("stroke_opacity", 1)
    linejoin = drawing.get("lineJoin")
    linecap = drawing.get("lineCap")

    if len(items) == 1 and items[0][0] == "re":
        rect = items[0][1]
        return (
            f'<rect x="{pt(rect.x0)}" y="{pt(rect.y0)}" width="{pt(rect.width)}" height="{pt(rect.height)}" '
            f'fill="{fill}" fill-opacity="{fill_opacity}" stroke="{stroke}" stroke-opacity="{stroke_opacity}" '
            f'stroke-width="{width:.2f}" rx="0" ry="0" />'
        )

    parts: list[str] = []
    for item in items:
        kind = item[0]
        if kind == "l":
            p1, p2 = item[1], item[2]
            parts.append(f"M {pt(p1.x)} {pt(p1.y)} L {pt(p2.x)} {pt(p2.y)}")
        elif kind == "c":
            p1, p2, p3, p4 = item[1], item[2], item[3], item[4]
            parts.append(
                f"M {pt(p1.x)} {pt(p1.y)} C {pt(p2.x)} {pt(p2.y)} {pt(p3.x)} {pt(p3.y)} {pt(p4.x)} {pt(p4.y)}"
            )
        elif kind == "re":
            rect = item[1]
            parts.append(
                f"M {pt(rect.x0)} {pt(rect.y0)} H {pt(rect.x1)} V {pt(rect.y1)} H {pt(rect.x0)} Z"
            )
        elif kind == "qu":
            quad = item[1]
            parts.append(
                f"M {pt(quad.ul.x)} {pt(quad.ul.y)} L {pt(quad.ur.x)} {pt(quad.ur.y)} "
                f"L {pt(quad.lr.x)} {pt(quad.lr.y)} L {pt(quad.ll.x)} {pt(quad.ll.y)} Z"
            )
    if not parts:
        return ""
    attrs = [
        f'd="{esc(" ".join(parts))}"',
        f'fill="{fill}"',
        f'fill-opacity="{fill_opacity}"',
        f'stroke="{stroke}"',
        f'stroke-opacity="{stroke_opacity}"',
        f'stroke-width="{width:.2f}"',
    ]
    if linejoin is not None:
        attrs.append(f'stroke-linejoin="{int(linejoin)}"')
    if linecap:
        attrs.append('stroke-linecap="round"')
    return f"<path {' '.join(attrs)} />"


def image_html(block: dict, decorative: bool) -> str:
    bbox = block["bbox"]
    uri = data_uri(block["image"], block["ext"])
    alt = "" if decorative else "Rendered image extracted from the PDF page"
    aria = ' aria-hidden="true"' if decorative else ""
    return (
        f'<img{aria} alt="{esc(alt)}" src="{uri}" '
        f'style="left:{pt(bbox[0])}px;top:{pt(bbox[1])}px;width:{pt(bbox[2]-bbox[0])}px;'
        f'height:{pt(bbox[3]-bbox[1])}px;">'
    )


def span_html(span: dict) -> str:
    text = span.get("text", "")
    if not text or not text.strip():
        return ""
    bbox = span["bbox"]
    size = span.get("size", 12) * SCALE
    width = max((bbox[2] - bbox[0]) * SCALE + max(6.0, size * 0.35), 1.0)
    height = max((bbox[3] - bbox[1]) * SCALE + max(2.0, size * 0.2), size + 1.0)
    return (
        f'<span class="text-span" style="left:{pt(bbox[0])}px;top:{pt(bbox[1])}px;'
        f'width:{width:.2f}px;min-height:{height:.2f}px;'
        f'font-family:{css_font_family(span.get("font", ""))};font-size:{size:.2f}px;'
        f'font-weight:{font_weight(span.get("font", ""), span.get("flags", 0))};'
        f'font-style:{font_style(span.get("font", ""), span.get("flags", 0))};'
        f'color:{color_from_int(span.get("color", 0))};">{esc(text)}</span>'
    )


def rect_overlap_x(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return max(0.0, min(a[2], b[2]) - max(a[0], b[0]))


def rect_overlap_y(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> float:
    return max(0.0, min(a[3], b[3]) - max(a[1], b[1]))


def text_overlap_risk(text_blocks: list[dict]) -> tuple[int, list[str]]:
    span_overlaps = 0
    line_overlaps = 0

    for block in text_blocks:
        prev_line_bbox: tuple[float, float, float, float] | None = None
        for line in block.get("lines", []):
            line_bbox = tuple(line.get("bbox", (0.0, 0.0, 0.0, 0.0)))
            spans = [span for span in line.get("spans", []) if (span.get("text") or "").strip()]
            spans = sorted(spans, key=lambda item: (item["bbox"][0], item["bbox"][1]))

            prev_span_bbox: tuple[float, float, float, float] | None = None
            for span in spans:
                bbox = tuple(span["bbox"])
                if prev_span_bbox is not None:
                    overlap_x = rect_overlap_x(prev_span_bbox, bbox)
                    overlap_y = rect_overlap_y(prev_span_bbox, bbox)
                    min_height = min(prev_span_bbox[3] - prev_span_bbox[1], bbox[3] - bbox[1])
                    if overlap_x > 4 and overlap_y > max(2.0, min_height * 0.55):
                        span_overlaps += 1
                prev_span_bbox = bbox

            if prev_line_bbox is not None:
                overlap_y = rect_overlap_y(prev_line_bbox, line_bbox)
                overlap_x = rect_overlap_x(prev_line_bbox, line_bbox)
                min_height = min(prev_line_bbox[3] - prev_line_bbox[1], line_bbox[3] - line_bbox[1])
                if overlap_y > max(2.0, min_height * 0.35) and overlap_x > 24:
                    line_overlaps += 1
            prev_line_bbox = line_bbox

    reasons: list[str] = []
    if span_overlaps:
        reasons.append(f"span-overlap:{span_overlaps}")
    if line_overlaps:
        reasons.append(f"line-overlap:{line_overlaps}")
    return span_overlaps + line_overlaps, reasons


def text_fragmentation_risk(text_blocks: list[dict]) -> tuple[int, list[str]]:
    tiny_spans = 0
    short_spans = 0
    total_spans = 0
    for block in text_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text = (span.get("text") or "").strip()
                if not text:
                    continue
                total_spans += 1
                width = max(span["bbox"][2] - span["bbox"][0], 0.0)
                if width < 2:
                    tiny_spans += 1
                if len(text) <= 2:
                    short_spans += 1
    reasons: list[str] = []
    score = 0
    if tiny_spans >= 20:
        score += 1
        reasons.append(f"tiny-spans:{tiny_spans}")
    if total_spans >= 250 and short_spans / max(total_spans, 1) > 0.45:
        score += 1
        reasons.append(f"fragmented-spans:{short_spans}/{total_spans}")
    if total_spans >= 900:
        score += 1
        reasons.append(f"dense-spans:{total_spans}")
    return score, reasons


def fallback_page_image(page: fitz.Page) -> str:
    pix = page.get_pixmap(matrix=fitz.Matrix(FALLBACK_RENDER_SCALE, FALLBACK_RENDER_SCALE), alpha=False)
    return data_uri(pix.tobytes("png"), "png")


def page_payload(
    page: fitz.Page,
    page_number: int,
    total_pages: int,
    transcript_text: str = "",
    force_mode: str | None = None,
) -> dict[str, object]:
    blocks = page.get_text("dict")["blocks"]
    text_blocks = [block for block in blocks if block["type"] == 0]
    image_blocks = [block for block in blocks if block["type"] == 1]
    text_spans: list[str] = []
    text_char_count = 0
    for block in text_blocks:
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                text_char_count += len((span.get("text") or "").strip())
                rendered = span_html(span)
                if rendered:
                    text_spans.append(rendered)

    vector_parts = [drawing_to_svg(d) for d in page.get_drawings()]
    vector_parts = [part for part in vector_parts if part]
    page_width = page.rect.width * SCALE
    page_height = page.rect.height * SCALE
    linear_text = extract_linear_text(page)
    accessible_text = sanitize_accessible_text(linear_text, page_number)
    text_span_count = len(text_spans)
    image_count = len(image_blocks)
    vector_count = len(vector_parts)
    overlap_score, overlap_reasons = text_overlap_risk(text_blocks)
    fragmentation_score, fragmentation_reasons = text_fragmentation_risk(text_blocks)

    render_mode = "semantic"
    review_reasons: list[str] = []
    if not text_span_count:
        render_mode = "image"
        review_reasons.append("no-positioned-text")
    elif overlap_score >= 1:
        render_mode = "hybrid"
        review_reasons.extend(overlap_reasons)
    elif fragmentation_score >= 1:
        render_mode = "hybrid"
        review_reasons.extend(fragmentation_reasons)
    elif text_char_count < 80 and (image_count or vector_count >= 20):
        render_mode = "hybrid"
        review_reasons.append("low-text-density")
    elif text_char_count < 30 and image_count >= 1:
        render_mode = "hybrid"
        review_reasons.append("image-heavy")
    if force_mode in {"semantic", "hybrid", "image"}:
        render_mode = force_mode
        review_reasons.append(f"forced-{force_mode}")

    decorative_images = bool(text_spans)
    images = "".join(image_html(block, decorative_images) for block in image_blocks)
    vectors = (
        f'<svg class="vector-layer" width="{page_width:.2f}" height="{page_height:.2f}" '
        f'viewBox="0 0 {page_width:.2f} {page_height:.2f}" aria-hidden="true" focusable="false">'
        + "".join(vector_parts)
        + "</svg>"
        if vector_parts
        else ""
    )
    text_layer = f'<div class="text-layer">{"".join(text_spans)}</div>' if text_spans else ""
    assistive_text_layer = (
        f'<div class="text-layer text-layer--assistive" aria-hidden="true">{"".join(text_spans)}</div>'
        if text_spans
        else ""
    )

    fallback = ""
    if render_mode == "image":
        fallback = (
            f'<img class="page-fallback" alt="" aria-hidden="true" src="{fallback_page_image(page)}">'
        )
    elif render_mode == "hybrid":
        fallback = (
            f'<img class="page-fallback" alt="" aria-hidden="true" src="{fallback_page_image(page)}">'
        )

    sr_text = choose_transcript_text(page_number, transcript_text, accessible_text, linear_text)
    missing_transcript = sr_text == transcript_fallback(page_number)
    if render_mode == "semantic":
        page_surface_note = (
            f"Page {page_number} is rendered as structured HTML with selectable text, extracted images, and vector artwork."
        )
    elif missing_transcript:
        page_surface_note = (
            f"Page {page_number} is rendered as a high-resolution preview to preserve layout fidelity. "
            "A full plain-text transcript could not be extracted from the source PDF."
        )
    else:
        page_surface_note = (
            f"Page {page_number} is rendered as a high-resolution preview to preserve layout fidelity. "
            "A plain-text transcript is available for screen readers and browser accessibility tools."
        )
    title_id = f"page-{page_number}-title"
    transcript_id = f"page-{page_number}-transcript"
    surface_note_id = f"page-{page_number}-surface-note"
    page_html = f"""
    <article class="page-card" id="page-{page_number}" data-page="{page_number}">
      <p class="page-label">Page {page_number} of {total_pages}</p>
      <section class="pdf-page" role="region" tabindex="0" aria-roledescription="PDF page" aria-labelledby="{title_id}" aria-describedby="{surface_note_id} {transcript_id}" style="width:{page_width:.2f}px;height:{page_height:.2f}px;">
        <h2 class="sr-only" id="{title_id}">Page {page_number}</h2>
        <div class="sr-only" id="{surface_note_id}">{esc(page_surface_note)}</div>
        <div class="sr-only" id="{transcript_id}">{esc(sr_text)}</div>
        {vectors if render_mode == "semantic" else ""}
        <div class="image-layer">{images if render_mode == "semantic" else ""}</div>
        {fallback}
        {text_layer if render_mode == "semantic" else assistive_text_layer}
        <div class="page-outline" aria-hidden="true"></div>
      </section>
    </article>
    """
    return {
        "html": page_html,
        "transcript": sr_text,
        "render_mode": render_mode,
        "review_reasons": ",".join(review_reasons) if review_reasons else "",
        "text_chars": text_char_count,
        "text_spans": text_span_count,
        "image_count": image_count,
        "vector_count": vector_count,
        "overlap_score": overlap_score + fragmentation_score,
    }


def document_title(doc: fitz.Document, pdf_path: Path) -> str:
    title = (doc.metadata or {}).get("title") or ""
    title = title.strip()
    return title or prettify_name(pdf_path.stem)


def build_html(pdf_path: Path, scan_root: Path, rules: dict[str, list[str]]) -> tuple[str, dict[str, object]]:
    doc = fitz.open(pdf_path)
    try:
        title = document_title(doc, pdf_path)
        force_mode = forced_mode_for_path(pdf_path, scan_root, rules)
        reader_texts = extract_reader_page_texts(pdf_path, doc.page_count)
        page_data = [
            page_payload(
                doc[i],
                i + 1,
                doc.page_count,
                transcript_text=reader_texts[i] if i < len(reader_texts) else "",
                force_mode=force_mode,
            )
            for i in range(doc.page_count)
        ]
        pages = "".join(str(item["html"]) for item in page_data)
        thumbs = "".join(
            f'<a class="thumb-link{" active" if i == 0 else ""}" href="#page-{i+1}" data-page="{i+1}" '
            f'aria-label="Jump to page {i+1}"><strong>Page {i+1}</strong></a>'
            for i, item in enumerate(page_data)
        )
        transcripts = "".join(
            f'<details{" open" if i == 0 else ""}><summary id="page-{i+1}-transcript-summary">Page {i+1} transcript</summary>'
            f'<pre aria-labelledby="page-{i+1}-transcript-summary">{esc(str(item["transcript"]))}</pre></details>'
            for i, item in enumerate(page_data)
        )
        semantic_pages = sum(1 for item in page_data if item["render_mode"] == "semantic")
        hybrid_pages = sum(1 for item in page_data if item["render_mode"] == "hybrid")
        image_pages = sum(1 for item in page_data if item["render_mode"] == "image")
        overlap_pages = sum(1 for item in page_data if int(item["overlap_score"]) > 0)
        needs_review = hybrid_pages > 0 or image_pages > 0
        html_text = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} - HTML PDF Replica</title>
  <style>{PDF_VIEWER_CSS}</style>
</head>
<body data-total-pages="{doc.page_count}">
  <a class="skip-link" href="#viewer-main">Skip to PDF content</a>
  <a class="skip-link" href="#tools-panel">Skip to accessibility tools</a>
  <main class="pdf-shell" id="pdf-main" role="main" aria-label="Accessible HTML version of {esc(title)}">
    <div class="viewer">
      <header class="topbar">
        <div class="brand">
          <div class="brand__badge" aria-hidden="true">A</div>
          <div>
            <div class="brand__title">{esc(title)}</div>
            <div class="brand__sub">{esc(pdf_path.name)} - {doc.page_count} page{'s' if doc.page_count != 1 else ''}</div>
          </div>
        </div>
      </header>
        <section class="toolbar" aria-label="Document controls">
        <div class="toolbar-actions">
          <div class="tool-group" role="group" aria-label="Panel controls">
            <button class="ui-btn" id="toggle-pages" type="button" aria-controls="pages-panel" aria-expanded="true" aria-pressed="true">Pages</button>
            <button class="ui-btn" id="toggle-tools" type="button" aria-controls="tools-panel" aria-expanded="true" aria-pressed="true">Accessibility</button>
            <button class="ui-btn" id="toggle-transcript" type="button" aria-controls="transcript-list transcript-panel" aria-expanded="false" aria-pressed="false">Transcript</button>
          </div>
          <div class="page-nav" role="group" aria-label="Page navigation">
            <button class="ui-btn" id="prev-page" type="button">Previous</button>
            <label class="sr-only" for="page-input">Current page</label>
            <input class="page-input" id="page-input" type="number" min="1" max="{doc.page_count}" inputmode="numeric">
            <span>of {doc.page_count}</span>
            <button class="ui-btn" id="next-page" type="button">Next</button>
          </div>
          <div class="zoom-controls" role="group" aria-label="Zoom controls">
            <button class="ui-btn" id="zoom-out" type="button">-</button>
            <span id="zoom-label" aria-live="polite">100%</span>
            <button class="ui-btn" id="zoom-in" type="button">+</button>
            <label class="sr-only" for="zoom-select">Zoom percent</label>
            <select class="zoom-select" id="zoom-select" aria-label="Zoom percent">
              <option value="50">50%</option>
              <option value="75">75%</option>
              <option value="100" selected>100%</option>
              <option value="125">125%</option>
              <option value="150">150%</option>
              <option value="200">200%</option>
            </select>
            <button class="ui-btn" id="actual-size" type="button">Actual Size</button>
            <button class="ui-btn" id="fit-page" type="button">Fit Page</button>
            <button class="ui-btn" id="fit-width" type="button">Fit Width</button>
          </div>
        </div>
        <div class="tool-group" aria-label="Viewer tools">
          <button class="ui-btn" id="reset-view" type="button">Reset</button>
        </div>
      </section>
      <div class="viewer-body">
        <aside class="sidebar" id="pages-panel" aria-label="Pages">
          <div class="sidebar__head">Pages</div>
          <nav class="thumb-list" aria-label="Page thumbnails">{thumbs}</nav>
        </aside>
        <section class="viewer-main" id="viewer-main" tabindex="-1" role="region" aria-label="PDF pages">
          <div class="viewer-stage">
            <div class="page-stack" id="page-stack" role="document" aria-label="{esc(title)} pages">{pages}</div>
          </div>
        </section>
        <aside class="tools" id="tools-panel" aria-label="Accessibility tools">
          <div class="tools__head">Accessibility</div>
          <div class="tools__body">
            <div class="tool-row">
              <button class="ui-btn" id="toggle-contrast" type="button" aria-pressed="false">High Contrast</button>
              <button class="ui-btn" id="toggle-readable" type="button" aria-pressed="false">Readable Font</button>
            </div>
            <p>This HTML view exposes each page as a labeled region, keeps a plain-text transcript for every page when text can be extracted, and falls back to a high-resolution preview when visual fidelity is safer than positioned text.</p>
            <ul>
              <li>Semantic HTML pages: {semantic_pages}</li>
              <li>Hybrid preview pages: {hybrid_pages}</li>
              <li>Image fallback pages: {image_pages}</li>
              <li>Overlap-risk pages corrected: {overlap_pages}</li>
            </ul>
            <div class="status-chip"><strong>Status</strong> <span id="viewer-status" aria-live="polite">HTML page 1, 100% zoom</span></div>
          </div>
          <div class="tools__head hidden" id="transcript-panel">Transcript</div>
          <div class="transcript-list hidden" id="transcript-list" role="region" aria-label="Page transcripts">{transcripts}</div>
        </aside>
      </div>
    </div>
  </main>
  <button class="back-top" id="back-to-top" type="button" aria-controls="viewer-main" aria-label="Return to top">Top</button>
  <script>{PDF_VIEWER_JS}</script>
</body>
</html>
"""
        report = {
            "title": title,
            "page_count": doc.page_count,
            "semantic_pages": semantic_pages,
            "hybrid_pages": hybrid_pages,
            "image_pages": image_pages,
            "overlap_pages": overlap_pages,
            "needs_review": "yes" if needs_review else "no",
        }
        return html_text, report
    finally:
        doc.close()


def collect_pdfs(input_path: Path) -> tuple[list[Path], Path]:
    if input_path.is_file():
        return [input_path], input_path.parent
    return sorted(input_path.rglob("*.pdf")), input_path


def output_html_path(pdf_path: Path, scan_root: Path, output_root: Path | None) -> Path:
    if output_root is None:
        return pdf_path.with_suffix(".html")
    try:
        relative = pdf_path.relative_to(scan_root)
    except ValueError:
        relative = Path(pdf_path.name)
    target = output_root / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    return target.with_suffix(".html")


def write_review_csv(review_rows: list[dict[str, object]], review_path: Path) -> int:
    review_path.parent.mkdir(parents=True, exist_ok=True)
    with review_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "pdf_path",
                "html_path",
                "page_count",
                "semantic_pages",
                "hybrid_pages",
                "image_pages",
                "overlap_pages",
                "needs_review",
                "title",
            ],
        )
        writer.writeheader()
        writer.writerows(review_rows)
    return sum(1 for row in review_rows if row["needs_review"] == "yes")


def convert_all(input_path: Path, output_root: Path | None = None, rules_path: Path | None = None) -> tuple[int, int, int, Path]:
    pdfs, scan_root = collect_pdfs(input_path)
    rules = load_rules(rules_path)
    cache: dict[str, tuple[str, dict[str, object]]] = {}
    converted = 0
    review_rows: list[dict[str, object]] = []
    for pdf_path in pdfs:
        digest = sha1(pdf_path)
        cached = cache.get(digest)
        if cached is None:
            cached = build_html(pdf_path, scan_root, rules)
            cache[digest] = cached
            converted += 1
        html_text, report = cached
        html_path = output_html_path(pdf_path, scan_root, output_root)
        html_path.write_text(html_text, encoding="utf-8")
        review_rows.append(
            {
                "pdf_path": relative_key(pdf_path, scan_root),
                "html_path": relative_key(html_path, output_root or scan_root),
                "page_count": report["page_count"],
                "semantic_pages": report["semantic_pages"],
                "hybrid_pages": report["hybrid_pages"],
                "image_pages": report["image_pages"],
                "overlap_pages": report["overlap_pages"],
                "needs_review": report["needs_review"],
                "title": report["title"],
            }
        )
    review_root = output_root or scan_root
    review_path = review_root / "pdf_html_review.csv"
    review_count = write_review_csv(review_rows, review_path)
    return len(pdfs), converted, review_count, review_path


def parse_args(
    argv: list[str] | None = None,
    default_input: str | None = None,
    default_rules_path: str | None = None,
) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert PDFs to styled HTML-only pages.")
    parser.add_argument(
        "input",
        nargs="?",
        default=default_input or str(Path.cwd()),
        help="PDF file or directory to convert.",
    )
    parser.add_argument("--output-root", type=str, default=None, help="Optional output directory for generated HTML.")
    parser.add_argument(
        "--rules",
        type=str,
        default=default_rules_path or str(DEFAULT_RULES_PATH),
        help="Optional JSON rules file.",
    )
    return parser.parse_args(argv)


def main(
    argv: list[str] | None = None,
    default_input: Path | None = None,
    default_rules_path: Path | None = None,
) -> int:
    args = parse_args(
        argv=argv,
        default_input=str(default_input) if default_input else None,
        default_rules_path=str(default_rules_path) if default_rules_path else None,
    )
    input_path = Path(args.input).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else None
    rules_path = Path(args.rules).resolve() if args.rules else None
    total, unique, review_count, review_path = convert_all(input_path, output_root=output_root, rules_path=rules_path)
    print(
        f"Converted {total} PDF files ({unique} unique sources) to HTML. "
        f"Review flagged {review_count} files. Review CSV: {review_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
