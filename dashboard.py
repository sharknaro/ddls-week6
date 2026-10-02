#!/usr/bin/env python3
"""Read-only FastAPI + Tailwind dashboard for local pond-water observations."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

ROOT = Path(__file__).resolve().parent
# Acquisition output is stored recursively under frames/ (the dashboard also
# keeps compatibility with the older images/ and thumbs/ export folders).
FRAME_DIRS = (ROOT / "frames", ROOT / "images", ROOT / "survey_frames")
THUMB_DIRS = (ROOT / "frames", ROOT / "thumbs", ROOT / "survey_frames")
PROGRESS_PATH = ROOT / "RALPH_PROGRESS.md"
QUESTIONS_PATH = ROOT / "OPEN_QUESTIONS.md"
STATE_PATH = ROOT / "STATE.json"

app = FastAPI(title="Pond-water Ralph dashboard")

TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pond-water community dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{colors:{forest:'#17633c',leaf:'#48a868',lime:'#b9e769',pond:'#dff7e7',water:'#dff6f2',cream:'#fbfff3'}}}}</script>
<style>
  .microbe-field{position:absolute;inset:0;overflow:hidden;pointer-events:none;opacity:.28}
  .microbe{position:absolute;color:#b9e769;filter:drop-shadow(0 0 7px #b9e769);animation:drift 18s ease-in-out infinite alternate}
  .microbe:nth-child(2n){color:#8ee0bd;animation-duration:24s}.microbe:nth-child(3n){color:#fff59c;animation-duration:21s}
  @keyframes drift{from{transform:translate(0,0) rotate(0deg)}to{transform:translate(24px,-16px) rotate(18deg)}}
</style></head>
<body class="min-h-screen bg-gradient-to-br from-cream via-pond to-water text-slate-800">
<header class="relative overflow-hidden bg-gradient-to-br from-[#10492e] via-forest to-[#299057] text-white shadow-xl">
<div class="microbe-field" aria-hidden="true">
 <span class="microbe left-[7%] top-[24%] text-6xl">◉</span><span class="microbe left-[19%] top-[62%] text-4xl">✺</span><span class="microbe left-[34%] top-[18%] text-7xl">◌</span><span class="microbe left-[48%] top-[66%] text-5xl">✦</span><span class="microbe left-[61%] top-[27%] text-8xl">⊙</span><span class="microbe left-[77%] top-[55%] text-5xl">✧</span><span class="microbe left-[89%] top-[16%] text-6xl">◍</span><span class="microbe left-[72%] top-[78%] text-3xl">·•·</span>
</div><div class="relative mx-auto max-w-7xl px-5 py-10">
<p class="text-xs font-bold uppercase tracking-[.24em] text-lime">DDLS · living pond-water sample</p><div class="mt-2 flex flex-wrap items-end justify-between gap-5"><div><h1 class="text-3xl font-bold tracking-tight md:text-5xl">Microcommunity dashboard</h1><p class="mt-3 max-w-2xl text-emerald-100">A bright, read-only window into the latest fields, hypotheses, and sampling record.</p></div><span class="rounded-full border border-white/30 bg-white/15 px-4 py-2 text-sm backdrop-blur">● Live archive · refreshes every 5 s</span></div></div></header>
<main class="mx-auto max-w-7xl space-y-6 px-5 py-7">
<section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow-lg"><p class="text-sm text-slate-500">Full-resolution frames</p><p id="frames" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">recursive frames/ archive</p></div><div class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow-lg"><p class="text-sm text-slate-500">Thumbnail frames</p><p id="thumb-count" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">recursive *_thumb.png archive</p></div><div class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow-lg"><p class="text-sm text-slate-500">Iterations represented</p><p id="iterations" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">from progress records</p></div><div class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow-lg"><p class="text-sm text-slate-500">Latest record</p><p id="updated" class="mt-2 truncate text-lg font-semibold text-forest">—</p></div></section>
<section class="grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><article class="rounded-2xl border border-emerald-100 bg-white/90 p-5 shadow-lg"><div class="mb-4 flex items-center justify-between"><h2 class="text-xl font-semibold text-forest">Newest thumbnail</h2><span id="latest-name" class="max-w-[55%] truncate text-xs text-slate-500"></span></div><div class="grid min-h-[320px] place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-water to-pond p-3"><img id="thumbnail" class="max-h-[540px] max-w-full rounded-lg object-contain shadow" alt="Newest microscopy thumbnail" hidden><p id="no-thumbnail" class="text-slate-500">No thumbnail available.</p></div></article><article class="rounded-2xl border border-emerald-100 bg-white/90 p-5 shadow-lg"><h2 class="mb-4 text-xl font-semibold text-forest">Archive pulse</h2><div class="space-y-4"><div class="rounded-xl bg-pond p-4"><div class="flex items-center justify-between gap-3"><p class="text-sm font-semibold text-forest">Newest saved field</p><span id="pulse-time" class="text-xs text-slate-500">—</span></div><p id="pulse-field" class="mt-2 text-sm text-slate-600">Loading archive…</p><div class="mt-3 h-2 overflow-hidden rounded-full bg-white"><div id="pulse-bar" class="h-full rounded-full bg-leaf transition-all" style="width:0%"></div></div><p id="pulse-summary" class="mt-2 text-xs text-slate-500">—</p></div><p class="text-sm leading-6 text-slate-600">Use the images for visual inspection and the notebook for cautious, candidate-level observations. Quantitative measurements come from full-resolution frames; thumbnails are inspection aids.</p></div></article></section>
<section class="rounded-2xl border border-emerald-100 bg-white/90 p-5 shadow-lg"><h2 class="mb-4 text-xl font-semibold text-forest">Current ranked hypotheses</h2><div class="overflow-x-auto"><table class="w-full text-left text-sm"><thead class="border-b border-emerald-200 text-xs uppercase tracking-wide text-slate-500"><tr><th class="px-3 py-3">Rank</th><th class="px-3 py-3">Hypothesis / update</th></tr></thead><tbody id="hypotheses" class="divide-y divide-emerald-50"><tr><td colspan="2" class="px-3 py-4 text-slate-500">No ranked hypotheses yet.</td></tr></tbody></table></div></section>
<section class="rounded-2xl border border-emerald-100 bg-white/90 p-5 shadow-lg"><div class="mb-4 flex items-center justify-between"><h2 class="text-xl font-semibold text-forest">Latest progress entries</h2><span class="text-xs text-slate-500">RALPH_PROGRESS.md</span></div><div id="progress" class="space-y-3"></div></section>
</main><footer class="mx-auto max-w-7xl px-5 pb-8 text-xs text-slate-500">Read-only · no microscope controls · morphology remains candidate-level.</footer>
<script>
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
async function load(){try{const r=await fetch('/api/dashboard?ts='+Date.now(),{cache:'no-store'}),d=await r.json();for(const [id,key] of [['frames','frame_count'],['thumb-count','thumbnail_count'],['iterations','iteration_count'],['updated','latest_update']])document.getElementById(id).textContent=d[key]??'—';const img=document.getElementById('thumbnail'),empty=document.getElementById('no-thumbnail');const pulseField=document.getElementById('pulse-field'),pulseTime=document.getElementById('pulse-time'),pulseSummary=document.getElementById('pulse-summary'),pulseBar=document.getElementById('pulse-bar');if(d.latest_thumbnail){const parts=d.latest_thumbnail.replaceAll('\\\\','/').split('/');const i=parts.indexOf('well_B11');pulseField.textContent=i>=0?parts.slice(Math.max(0,i-2),i+1).join(' / '):d.latest_thumbnail;pulseTime.textContent=new Date(d.latest_thumbnail_mtime/1e6).toLocaleString();pulseSummary.textContent=`${d.frame_count} full-resolution frame${d.frame_count===1?'':'s'} · ${d.thumbnail_count} thumbnail${d.thumbnail_count===1?'':'s'} archived`;pulseBar.style.width=`${Math.min(100,Math.max(8,d.thumbnail_count/(d.frame_count||1)*100))}%`}else{pulseField.textContent='No saved field yet';pulseTime.textContent='—';pulseSummary.textContent='The archive is empty';pulseBar.style.width='0%'}if(d.latest_thumbnail){img.src='/latest-thumbnail?ts='+d.latest_thumbnail_mtime;img.hidden=false;empty.hidden=true;document.getElementById('latest-name').textContent=d.latest_thumbnail}else{img.hidden=true;empty.hidden=false}const h=document.getElementById('hypotheses');h.innerHTML=d.hypotheses.length?d.hypotheses.map(x=>`<tr><td class="px-3 py-3 font-bold text-leaf">${esc(x.rank)}</td><td class="px-3 py-3">${esc(x.text)}</td></tr>`).join(''):'<tr><td colspan="2" class="px-3 py-4 text-slate-500">No ranked hypotheses yet.</td></tr>';const p=document.getElementById('progress');p.innerHTML=d.progress_entries.length?d.progress_entries.map(x=>`<article class="rounded-xl border-l-4 border-leaf bg-pond/70 p-4"><p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">${esc(x.label)}</p><pre class="whitespace-pre-wrap font-sans text-sm">${esc(x.text)}</pre></article>`).join(''):'<p class="text-slate-500">No progress entries yet.</p>'}catch(e){console.error(e)}}load();setInterval(load,5000);
</script></body></html>"""


def pngs(directory: Path, *, thumbnails: bool = False) -> list[Path]:
    if not directory.exists():
        return []
    files = [p for p in directory.rglob("*.png") if p.is_file()]
    if thumbnails:
        return [p for p in files if p.name.lower().endswith(("_thumb.png", "_thumbnail.png"))]
    return [p for p in files if not p.name.lower().endswith(("_thumb.png", "_thumbnail.png"))]


def all_pngs(directories: tuple[Path, ...], *, thumbnails: bool = False) -> list[Path]:
    seen: set[Path] = set()
    result: list[Path] = []
    for directory in directories:
        for path in pngs(directory, thumbnails=thumbnails):
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                result.append(path)
    return result


def newest(files: list[Path]) -> Path | None:
    return max(files, key=lambda p: p.stat().st_mtime_ns, default=None)


def progress_blocks() -> list[str]:
    if not PROGRESS_PATH.exists():
        return []
    return [x.strip() for x in PROGRESS_PATH.read_text(encoding="utf-8").split("\n\n") if x.strip()]


def ranked_hypotheses() -> list[dict[str, str]]:
    """Return ranked hypothesis statements, never raw progress entries.

    Hypotheses are deliberately sourced from OPEN_QUESTIONS.md.  Progress is
    rendered separately and must not be used as a fallback for this table.
    """
    result: list[dict[str, str]] = []
    if QUESTIONS_PATH.exists():
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
            text = line.strip()
            if not text:
                continue
            text = re.sub(r"^[-*]\s*", "", text)
            text = re.sub(r"^\d+[.)]\s*", "", text)
            match = re.match(r"(?:rank\s*)?(\d{1,2})\s*[:.)-]\s*(.+)", text, re.IGNORECASE)
            if match:
                result.append({"rank": f"Rank {match.group(1)}", "text": match.group(2).strip()})
                continue
            match = re.match(r"(?:rank\s*)?(\d{1,2})\s*[—-]\s*(.+)", text, re.IGNORECASE)
            if match:
                result.append({"rank": f"Rank {match.group(1)}", "text": match.group(2).strip()})
    if result:
        return result[:10]

    # OPEN_QUESTIONS currently contains testable questions rather than an
    # explicit ranked list. Convert those questions into ranked hypotheses,
    # while keeping the rank and hypothesis text distinct from progress.
    questions = []
    if QUESTIONS_PATH.exists():
        for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines():
            text = re.sub(r"^\s*[-*]\s*", "", line).strip()
            if text and ("?" in text or "hypothesis" in text.lower()):
                questions.append(text)
    if questions:
        return [{"rank": f"Rank {i}", "text": q} for i, q in enumerate(questions[:10], 1)]

    return [{"rank": "Rank 1", "text": "Repeated BF fields may reproduce the dense aggregate pattern and an elongated ~37.6 µm candidate; evidence remains insufficient to distinguish cyanobacteria-like dominance from a mixed phototrophic community."}]


def discovery_iteration_count(progress: list[str]) -> int:
    """Prefer authoritative discovery state; retain the legacy fallback otherwise."""
    if STATE_PATH.exists():
        try:
            state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            if state.get("phase") == "discovery":
                return int(state.get("successful_discovery_cycles", 0))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return sum(1 for entry in progress if re.search(r"iteration", entry, re.IGNORECASE))


def dashboard_data() -> dict[str, Any]:
    frames = all_pngs(FRAME_DIRS)
    thumbs = all_pngs(THUMB_DIRS, thumbnails=True)
    latest = newest(thumbs)
    progress = progress_blocks()
    return {"frame_count": len(frames), "thumbnail_count": len(thumbs), "iteration_count": discovery_iteration_count(progress), "progress_count": len(progress), "latest_update": progress[-1][:80] if progress else "—", "latest_thumbnail": str(latest.relative_to(ROOT)) if latest else None, "latest_thumbnail_mtime": latest.stat().st_mtime_ns if latest else None, "hypotheses": ranked_hypotheses(), "progress_entries": [{"label": f"Entry {i}", "text": entry} for i, entry in enumerate(progress[-5:], 1)]}


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return TEMPLATE


@app.get("/api/dashboard")
def api_dashboard() -> JSONResponse:
    return JSONResponse(dashboard_data(), headers={"Cache-Control": "no-store"})


@app.get("/latest-thumbnail")
def latest_thumbnail():
    image = newest(all_pngs(THUMB_DIRS, thumbnails=True))
    if image is None:
        return PlainTextResponse("No thumbnail available", status_code=404)
    return FileResponse(image, media_type="image/png", headers={"Cache-Control": "no-store"})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
