from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent
IMAGE_DIRS = {"images": ROOT / "images", "thumbs": ROOT / "thumbs"}
SOURCE_DIRS = [ROOT / "survey_frames", ROOT / "fluorescence"]
PROGRESS_PATH = ROOT / "RALPH_PROGRESS.md"
QUESTIONS_PATH = ROOT / "OPEN_QUESTIONS.md"

app = FastAPI(title="DDLS Lab Dashboard")
for name, path in IMAGE_DIRS.items():
    path.mkdir(exist_ok=True)
    app.mount(f"/{name}", StaticFiles(directory=path), name=name)
for directory in SOURCE_DIRS:
    directory.mkdir(exist_ok=True)
app.mount("/source", StaticFiles(directory=ROOT), name="source")


def files_in(path: Path, recursive: bool = False) -> list[Path]:
    if not path.exists():
        return []
    candidates = path.rglob("*") if recursive else path.iterdir()
    return sorted((p for p in candidates if p.is_file()), key=lambda p: p.stat().st_mtime, reverse=True)


def source_files(thumbnails: bool | None = None) -> list[Path]:
    files = []
    for directory in SOURCE_DIRS:
        for path in files_in(directory, recursive=True):
            is_thumb = path.name.endswith("_thumb.png")
            if thumbnails is None or is_thumb == thumbnails:
                files.append(path)
    return sorted(files, key=lambda p: p.stat().st_mtime, reverse=True)


def newest_thumbnail() -> dict[str, Any] | None:
    files = source_files(thumbnails=True) or files_in(IMAGE_DIRS["thumbs"], recursive=True)
    if not files:
        return None
    item = files[0]
    if item.is_relative_to(ROOT / "thumbs"):
        url = "/thumbs/" + item.relative_to(ROOT / "thumbs").as_posix()
    else:
        url = "/source/" + item.relative_to(ROOT).as_posix()
    return {"name": item.name, "url": url, "updated": item.stat().st_mtime}


def read_markdown(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def progress_entries() -> list[dict[str, str]]:
    text = read_markdown(PROGRESS_PATH)
    entries: list[dict[str, str]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", line)
        if match:
            entries.append({"text": match.group(1), "raw": line})
    if not entries and text.strip():
        entries = [{"text": line.strip(), "raw": line.strip()} for line in text.splitlines() if line.strip()][:20]
    return entries[-20:][::-1]


def hypotheses() -> list[dict[str, str]]:
    text = read_markdown(QUESTIONS_PATH)
    rows: list[dict[str, str]] = []
    # Prefer markdown tables, but also accept the project's "Rank N: ..." entries.
    for line in text.splitlines():
        stripped = line.strip()
        if "|" in stripped and not re.match(r"^\s*\|?\s*:?-+:?", stripped):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) >= 2 and not all(re.fullmatch(r":?-+:?", c) for c in cells) and cells[0].lower() not in {"rank", "#", "priority"}:
                rows.append({"rank": cells[0], "hypothesis": cells[1], "evidence": " · ".join(cells[2:])})
            continue
        match = re.match(r"^(?:[-*]\s*)?(?:Rank\s*)?(\d+)\s*[:.)-]\s*(.+)$", stripped, re.I)
        if match:
            rows.append({"rank": match.group(1), "hypothesis": match.group(2), "evidence": ""})
    return rows[:20]


def counts() -> dict[str, int]:
    frames = len(source_files(thumbnails=False)) or len(files_in(IMAGE_DIRS["images"], recursive=True))
    thumbs = len(source_files(thumbnails=True)) or len(files_in(IMAGE_DIRS["thumbs"], recursive=True))
    progress = len(progress_entries())
    iterations = 0
    for value in (read_markdown(PROGRESS_PATH), read_markdown(QUESTIONS_PATH)):
        iterations += len(re.findall(r"\b(?:iteration|iter|cycle)\s*#?\s*\d+", value, flags=re.I))
    return {"frames": frames, "thumbnails": thumbs, "progress_entries": progress, "iterations": iterations}


@app.get("/api/dashboard")
def dashboard_data() -> JSONResponse:
    return JSONResponse({
        "newest_thumbnail": newest_thumbnail(),
        "hypotheses": hypotheses(),
        "progress": progress_entries(),
        "counts": counts(),
        "questions": read_markdown(QUESTIONS_PATH),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    })


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return HTML


HTML = r'''<!doctype html>
<html lang="en" class="bg-slate-950">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>DDLS Lab Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>
</head>
<body class="min-h-screen text-slate-100" x-data="dashboard()" x-init="load(); setInterval(load, 5000)">
  <main class="mx-auto max-w-7xl px-5 py-8">
    <header class="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div><p class="text-sm font-semibold uppercase tracking-[.25em] text-cyan-400">DDLS · Lab 6</p><h1 class="mt-2 text-3xl font-bold tracking-tight">Microscope dashboard</h1></div>
      <div class="text-right text-sm text-slate-400"><span class="mr-2 inline-block h-2 w-2 rounded-full bg-emerald-400"></span>Auto-refreshing every 5 seconds<br><span x-text="data.generated_at || 'Loading…'"></span></div>
    </header>
    <section class="mb-6 grid grid-cols-2 gap-3 md:grid-cols-4">
      <template x-for="stat in stats" :key="stat.key"><div class="rounded-2xl border border-slate-800 bg-slate-900 p-4"><div class="text-xs uppercase tracking-wider text-slate-500" x-text="stat.label"></div><div class="mt-2 text-3xl font-semibold" x-text="data.counts?.[stat.key] ?? 0"></div></div></template>
    </section>
    <section class="grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5"><div class="mb-4 flex items-center justify-between"><h2 class="text-lg font-semibold">Newest thumbnail</h2><span class="text-xs text-slate-500" x-text="data.newest_thumbnail?.name || 'No thumbnails yet'"></span></div><div class="flex min-h-80 items-center justify-center overflow-hidden rounded-xl bg-slate-950"><template x-if="data.newest_thumbnail"><img class="max-h-[32rem] max-w-full object-contain" :src="data.newest_thumbnail.url + '?t=' + Date.now()" :alt="data.newest_thumbnail.name"></template><template x-if="!data.newest_thumbnail"><p class="text-slate-500">Add thumbnails to ./thumbs</p></template></div></div>
      <div class="rounded-2xl border border-slate-800 bg-slate-900 p-5"><h2 class="mb-4 text-lg font-semibold">Ranked hypotheses</h2><div class="overflow-x-auto"><table class="w-full text-left text-sm"><thead class="border-b border-slate-800 text-xs uppercase tracking-wider text-slate-500"><tr><th class="px-2 py-3">Rank</th><th class="px-2 py-3">Hypothesis</th><th class="px-2 py-3">Evidence</th></tr></thead><tbody><template x-for="row in data.hypotheses" :key="row.rank + row.hypothesis"><tr class="border-b border-slate-800/70 align-top"><td class="px-2 py-3 font-semibold text-cyan-400" x-text="row.rank"></td><td class="px-2 py-3" x-text="row.hypothesis"></td><td class="px-2 py-3 text-slate-400" x-text="row.evidence"></td></tr></template></tbody></table><p x-show="!data.hypotheses?.length" class="py-6 text-sm text-slate-500">No markdown hypothesis table found in OPEN_QUESTIONS.md.</p></div></div>
    </section>
    <section class="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5"><h2 class="mb-4 text-lg font-semibold">Latest progress</h2><ol class="space-y-3"><template x-for="(entry, i) in data.progress" :key="i"><li class="flex gap-3 text-sm"><span class="mt-1 h-2 w-2 shrink-0 rounded-full bg-cyan-400"></span><span class="text-slate-300" x-text="entry.text"></span></li></template></ol><p x-show="!data.progress?.length" class="text-sm text-slate-500">No progress entries found in RALPH_PROGRESS.md.</p></section>
  </main>
<script>
function dashboard(){return {data:{},stats:[{key:'frames',label:'Frames'},{key:'thumbnails',label:'Thumbnails'},{key:'iterations',label:'Iterations'},{key:'progress_entries',label:'Progress entries'}],async load(){try{const r=await fetch('/api/dashboard?ts='+Date.now());this.data=await r.json()}catch(e){console.error(e)}}}}
</script></body></html>'''
