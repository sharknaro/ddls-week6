#!/usr/bin/env python3
"""Read-only FastAPI dashboard for local Ralph image archives."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "images"
THUMBS_DIR = ROOT / "thumbs"
PROGRESS_PATH = ROOT / "RALPH_PROGRESS.md"
QUESTIONS_PATH = ROOT / "OPEN_QUESTIONS.md"

app = FastAPI(title="Ralph dashboard")

TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ralph · Pond community dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script>tailwind.config={theme:{extend:{colors:{forest:'#174b32',leaf:'#3f9860',moss:'#dff2df',water:'#dff1ed',cream:'#f5f7ed'}}}}</script>
</head><body class="min-h-screen bg-gradient-to-br from-cream via-moss to-water text-slate-800">
<header class="bg-gradient-to-r from-forest to-emerald-800 text-white shadow-lg"><div class="mx-auto max-w-7xl px-5 py-8">
<p class="text-xs font-bold uppercase tracking-[.22em] text-emerald-200">DDLS · living sample observation</p><div class="mt-2 flex flex-wrap items-end justify-between gap-4"><div><h1 class="text-3xl font-bold tracking-tight md:text-4xl">Pond community dashboard</h1><p class="mt-2 max-w-2xl text-emerald-100">A read-only view of the image archive, sampling progress, and working hypotheses.</p></div><span class="rounded-full border border-white/30 bg-white/10 px-4 py-2 text-sm">● Auto-refresh · 5 s</span></div>
</div></header>
<main class="mx-auto max-w-7xl space-y-6 px-5 py-6">
<section class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div class="rounded-2xl border border-emerald-100 bg-white/80 p-5 shadow"><p class="text-sm text-slate-500">Frame count</p><p id="frames" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">./images PNGs</p></div><div class="rounded-2xl border border-emerald-100 bg-white/80 p-5 shadow"><p class="text-sm text-slate-500">Thumbnail count</p><p id="thumb-count" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">./thumbs PNGs</p></div><div class="rounded-2xl border border-emerald-100 bg-white/80 p-5 shadow"><p class="text-sm text-slate-500">Iterations</p><p id="iterations" class="mt-2 text-3xl font-bold text-forest">—</p><p class="text-xs text-slate-500">detected from records</p></div><div class="rounded-2xl border border-emerald-100 bg-white/80 p-5 shadow"><p class="text-sm text-slate-500">Latest update</p><p id="updated" class="mt-2 text-lg font-semibold text-forest">—</p></div></section>
<section class="grid gap-6 lg:grid-cols-[1.2fr_.8fr]"><article class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow"><div class="mb-4 flex items-center justify-between"><h2 class="text-xl font-semibold text-forest">Newest thumbnail</h2><span id="latest-name" class="max-w-[55%] truncate text-xs text-slate-500"></span></div><div class="grid min-h-[300px] place-items-center overflow-hidden rounded-xl bg-gradient-to-br from-water to-moss p-3"><img id="thumbnail" class="max-h-[520px] max-w-full rounded-lg object-contain shadow" alt="Newest microscopy thumbnail" hidden><p id="no-thumbnail" class="text-slate-500">No thumbnail available.</p></div></article><article class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow"><h2 class="mb-4 text-xl font-semibold text-forest">Sampling status</h2><dl class="divide-y divide-emerald-100"><div class="flex justify-between py-3"><dt class="text-slate-500">Current iteration</dt><dd id="iteration" class="font-bold text-forest">—</dd></div><div class="flex justify-between py-3"><dt class="text-slate-500">Cycle</dt><dd id="cycle" class="font-bold text-forest">—</dd></div><div class="flex justify-between py-3"><dt class="text-slate-500">Last completed slot</dt><dd id="last-slot" class="font-bold text-forest">—</dd></div><div class="flex justify-between py-3"><dt class="text-slate-500">Next slot</dt><dd id="next-slot" class="font-bold text-forest">—</dd></div></dl></article></section>
<section class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow"><h2 class="mb-4 text-xl font-semibold text-forest">Ranked hypotheses</h2><div class="overflow-x-auto"><table class="w-full text-left text-sm"><thead class="border-b border-emerald-200 text-xs uppercase tracking-wide text-slate-500"><tr><th class="px-3 py-3">Rank</th><th class="px-3 py-3">Hypothesis / update</th></tr></thead><tbody id="hypotheses" class="divide-y divide-emerald-50"><tr><td colspan="2" class="px-3 py-4 text-slate-500">No ranked hypotheses yet.</td></tr></tbody></table></div></section>
<section class="rounded-2xl border border-emerald-100 bg-white/85 p-5 shadow"><div class="mb-4 flex items-center justify-between"><h2 class="text-xl font-semibold text-forest">Latest progress entries</h2><span class="text-xs text-slate-500">RALPH_PROGRESS.md</span></div><div id="progress" class="space-y-3"></div></section>
</main><footer class="mx-auto max-w-7xl px-5 pb-8 text-xs text-slate-500">Read-only dashboard. It does not control the microscope.</footer>
<script>
function esc(s){const d=document.createElement('div');d.textContent=s;return d.innerHTML}
async function load(){try{const r=await fetch('/api/dashboard?ts='+Date.now(),{cache:'no-store'}),d=await r.json();for(const [id,key] of [['frames','frame_count'],['thumb-count','thumbnail_count'],['iterations','iteration_count'],['updated','latest_update'],['iteration','campaign_iteration'],['cycle','cycle'],['last-slot','last_completed_slot'],['next-slot','next_slot']])document.getElementById(id).textContent=d[key]??'—';const img=document.getElementById('thumbnail'),empty=document.getElementById('no-thumbnail');if(d.latest_thumbnail){img.src='/latest-thumbnail?ts='+d.latest_thumbnail_mtime;img.hidden=false;empty.hidden=true;document.getElementById('latest-name').textContent=d.latest_thumbnail}else{img.hidden=true;empty.hidden=false}const h=document.getElementById('hypotheses');h.innerHTML=d.hypotheses.length?d.hypotheses.map(x=>`<tr><td class="px-3 py-3 font-bold text-leaf">${esc(x.rank)}</td><td class="px-3 py-3">${esc(x.text)}</td></tr>`).join(''):'<tr><td colspan="2" class="px-3 py-4 text-slate-500">No ranked hypotheses yet.</td></tr>';const p=document.getElementById('progress');p.innerHTML=d.progress_entries.length?d.progress_entries.map(x=>`<article class="rounded-xl border-l-4 border-leaf bg-moss/50 p-4"><p class="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-500">${esc(x.label)}</p><pre class="whitespace-pre-wrap font-sans text-sm">${esc(x.text)}</pre></article>`).join(''):'<p class="text-slate-500">No progress entries yet.</p>'}catch(e){console.error(e)}}load();setInterval(load,5000);
</script></body></html>"""


def pngs(directory: Path) -> list[Path]:
    return [p for p in directory.rglob("*.png") if p.is_file()] if directory.exists() else []


def latest(files: list[Path]) -> Path | None:
    return max(files, key=lambda p: p.stat().st_mtime_ns, default=None)


def blocks(path: Path) -> list[str]:
    if not path.exists(): return []
    return [x.strip() for x in path.read_text(encoding="utf-8").split("\n\n") if x.strip()]


def hypotheses() -> list[dict[str, str]]:
    result=[]
    for line in QUESTIONS_PATH.read_text(encoding="utf-8").splitlines() if QUESTIONS_PATH.exists() else []:
        stripped=line.strip()
        if stripped.startswith("Rank ") or stripped.startswith("- Rank "):
            clean=stripped.removeprefix("- "); rank,_,text=clean.partition(":")
            result.append({"rank":rank,"text":text.strip() or clean})
    return result[:10]


def data() -> dict[str, Any]:
    frames=pngs(IMAGES_DIR); thumbs=pngs(THUMBS_DIR); newest=latest(thumbs); progress=blocks(PROGRESS_PATH)
    return {"frame_count":len(frames),"thumbnail_count":len(thumbs),"iteration_count":sum(1 for x in progress if "iteration" in x.lower()),"latest_update":progress[-1][:80] if progress else "—","latest_thumbnail":str(newest.relative_to(ROOT)) if newest else None,"latest_thumbnail_mtime":newest.stat().st_mtime_ns if newest else None,"hypotheses":hypotheses(),"progress_entries":[{"label":f"Entry {i}","text":x} for i,x in enumerate(progress[-5:],1)],"campaign_iteration":None,"cycle":None,"last_completed_slot":None,"next_slot":None}


@app.get("/", response_class=HTMLResponse)
def index(): return TEMPLATE

@app.get("/api/dashboard")
def api_dashboard(): return JSONResponse(data(),headers={"Cache-Control":"no-store"})

@app.get("/latest-thumbnail")
def latest_thumbnail():
    path=latest(pngs(THUMBS_DIR))
    return FileResponse(path,media_type="image/png",headers={"Cache-Control":"no-store"}) if path else PlainTextResponse("No thumbnail available",status_code=404)
