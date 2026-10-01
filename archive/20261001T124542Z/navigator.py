#!/usr/bin/env python3
"""Tiny local microscope navigator. Start with: python navigator.py"""
from __future__ import annotations

import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parent
OUT = Path(__file__).resolve().parent / "survey_frames"
OUT.mkdir(exist_ok=True)
BASE_URL = "https://ddls-gateway-b69bb891.svc.hypha.aicell.io/v1"
RETRY = {429, 503}

app = FastAPI(title="DDLS Microscope Navigator")
app.mount("/frames", StaticFiles(directory=OUT), name="frames")


def token() -> str:
    value = os.getenv("DDLS_TOKEN")
    if not value:
        raise HTTPException(500, "DDLS_TOKEN is not set in the navigator process")
    return value


def api(method: str, path: str, payload: dict | None = None, timeout: float = 30) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(BASE_URL + path, method=method, data=body, headers={
        "Authorization": f"Bearer {token()}", "Content-Type": "application/json"})
    for attempt in range(7):
        try:
            with urlopen(req, timeout=timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try: detail = json.loads(raw)
            except json.JSONDecodeError: detail = {"error": raw}
            if exc.code not in RETRY or attempt == 6:
                raise HTTPException(exc.code, detail)
            delay = max(float(detail.get("retry_after_s", 0)), min(30, 2 ** attempt))
            time.sleep(delay)
        except (TimeoutError, URLError) as exc:
            if attempt == 6: raise HTTPException(502, str(exc))
            time.sleep(min(30, 2 ** attempt))
    raise HTTPException(502, "retry loop exhausted")


class Position(BaseModel):
    well: str = "B11"
    plate: str = "A"
    dx: float = Field(0, ge=-1, le=1)
    dy: float = Field(0, ge=-1, le=1)

    @model_validator(mode="after")
    def inside_circle(self):
        if self.dx * self.dx + self.dy * self.dy > 1:
            raise ValueError("dx² + dy² must be <= 1")
        return self


class Snap(Position):
    channel: str = "BF_LED_matrix_full"
    exposure_ms: float = Field(20, gt=0, le=200)
    intensity: float = Field(20, gt=0, le=30)


class Nudge(Position):
    dz: float = Field(0, ge=-1, le=1)


class SweepRequest(Position):
    points: list[tuple[float, float]] = Field(default_factory=lambda: [(0, 0), (-.5, 0), (.5, 0), (0, -.5), (0, .5)])
    channel: str = "BF_LED_matrix_full"
    exposure_ms: float = Field(20, gt=0, le=200)
    intensity: float = Field(20, gt=0, le=30)

    @model_validator(mode="after")
    def validate_points(self):
        if not self.points or len(self.points) > 25:
            raise ValueError("sweep must contain 1-25 points")
        if any(x*x + y*y > 1 for x, y in self.points):
            raise ValueError("every sweep point must be inside the round well")
        return self


def save_frame(response: dict, label: str, well: str, plate: str) -> dict:
    raw = response.get("image_png_b64")
    if not raw: raise HTTPException(502, "snap returned no image")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    stem = f"{stamp}_{label}"
    destination = OUT / f"plate_{plate}" / f"well_{well}"
    destination.mkdir(parents=True, exist_ok=True)
    full = destination / f"{stem}.png"
    thumb = destination / f"{stem}_thumb.png"
    full.write_bytes(base64.b64decode(raw))
    try:
        from PIL import Image
        with Image.open(full) as image:
            image.thumbnail((768, 768), Image.Resampling.LANCZOS)
            image.save(thumb, "PNG")
    except ImportError as exc:
        raise HTTPException(500, "Pillow is required") from exc
    return {"image": f"/frames/plate_{plate}/well_{well}/{full.name}", "thumbnail": f"/frames/plate_{plate}/well_{well}/{thumb.name}", "position_mm": response.get("position_mm"), "image_url": response.get("image_url")}


@app.get("/api/status")
def status(plate: str = "A"):
    return api("GET", "/status?" + urlencode({"plate": plate}))


@app.post("/api/autofocus")
def autofocus(position: Position):
    return api("POST", "/focus", position.model_dump())


@app.post("/api/nudge-z")
def nudge_z(request: Nudge):
    return api("POST", "/z", request.model_dump())


@app.post("/api/reset")
def reset(position: Position):
    # Reset means re-establish autofocus at the requested well; it does not move-then-snap.
    return api("POST", "/focus", position.model_dump())


@app.post("/api/snap")
def snap(request: Snap):
    response = api("POST", "/snap", request.model_dump())
    return {**save_frame(response, f"{request.plate}_{request.well}_{request.channel}", request.well, request.plate), "raw": {k: v for k, v in response.items() if k != "image_png_b64"}}


@app.post("/api/sweep")
def sweep(request: SweepRequest):
    focus = api("POST", "/focus", request.model_dump(exclude={"points", "channel", "exposure_ms", "intensity"}))
    frames = []
    for dx, dy in request.points:
        payload = {"well": request.well, "plate": request.plate, "dx": dx, "dy": dy, "channel": request.channel, "exposure_ms": request.exposure_ms, "intensity": request.intensity}
        frames.append({"dx": dx, "dy": dy, **save_frame(api("POST", "/snap", payload), f"{request.plate}_{request.well}_{request.channel}_{dx}_{dy}", request.well, request.plate)})
    return {"focus": focus, "frames": frames}


@app.get("/", response_class=HTMLResponse)
def home():
    return PAGE


PAGE = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Microscope Navigator</title><script src="https://cdn.tailwindcss.com"></script></head><body class="min-h-screen bg-slate-950 text-slate-100"><main class="mx-auto max-w-6xl px-5 py-8"><header class="mb-6"><p class="text-xs font-bold uppercase tracking-[.25em] text-cyan-400">DDLS Lab 6</p><h1 class="mt-2 text-3xl font-bold">Microscope navigator</h1><p class="mt-2 text-slate-400">Manual controls use atomic snap coordinates. No move-then-snap path is exposed.</p></header><div id="message" class="mb-4 hidden rounded-xl border p-3 text-sm"></div><section class="grid gap-5 lg:grid-cols-[300px_1fr]"><aside class="space-y-4 rounded-2xl border border-slate-800 bg-slate-900 p-5"><div class="grid grid-cols-2 gap-3"><label class="text-sm">Well<input id="well" value="B11" class="field"></label><label class="text-sm">Plate<input id="plate" value="A" class="field"></label></div><label class="text-sm">Channel<select id="channel" class="field"><option>BF_LED_matrix_full</option><option>Fluorescence_488_nm_Ex</option></select></label><div class="grid grid-cols-2 gap-3"><label class="text-sm">dx<input id="dx" type="number" step=".1" value="0" class="field"></label><label class="text-sm">dy<input id="dy" type="number" step=".1" value="0" class="field"></label></div><div class="grid grid-cols-2 gap-2"><button onclick="call('autofocus')" class="button">Autofocus</button><button onclick="call('status')" class="button">Status</button><button onclick="call('reset')" class="button">Reset focus</button><button onclick="nudge()" class="button">Nudge Z</button></div><input id="dz" type="number" step=".1" value="0" placeholder="dz" class="field"><button onclick="snap()" class="button w-full bg-cyan-600 hover:bg-cyan-500">Snap current position</button><button onclick="sweep()" class="button w-full bg-emerald-700 hover:bg-emerald-600">Sweep 5 positions</button><p class="text-xs leading-5 text-slate-500">Fluorescence starts at 30 ms × 20. First fluorescence request may take up to 30 s.</p></aside><section><div class="mb-4 rounded-2xl border border-slate-800 bg-slate-900 p-4"><h2 class="mb-3 font-semibold">Latest result</h2><pre id="result" class="max-h-64 overflow-auto whitespace-pre-wrap text-xs text-slate-300">Ready.</pre></div><div id="gallery" class="grid grid-cols-2 gap-3 md:grid-cols-3"></div></section></section></main><style>.field{display:block;margin-top:.35rem;width:100%;border-radius:.6rem;border:1px solid #334155;background:#020617;padding:.55rem;color:#f8fafc}.button{border-radius:.6rem;background:#1e293b;padding:.6rem;font-size:.85rem}.button:hover{background:#334155}</style><script>
const $=id=>document.getElementById(id);const base=()=>({well:$('well').value,plate:$('plate').value,dx:+$('dx').value,dy:+$('dy').value});function show(x){$('result').textContent=JSON.stringify(x,null,2);$('message').classList.add('hidden')}function fail(e){$('message').textContent=e.message||e;$('message').className='mb-4 rounded-xl border border-red-800 bg-red-950 p-3 text-sm text-red-200'}async function post(path,body){const r=await fetch('/api/'+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const x=await r.json();if(!r.ok)throw Error(JSON.stringify(x));return x}async function call(path){try{show(await (path==='status'?fetch('/api/status?plate='+encodeURIComponent($('plate').value)).then(r=>r.json()):post(path,base())))}catch(e){fail(e)}}async function nudge(){try{show(await post('nudge-z',{...base(),dz:+$('dz').value}))}catch(e){fail(e)}}async function snap(){try{const x=await post('snap',{...base(),channel:$('channel').value,exposure_ms:$('channel').value.includes('Fluorescence')?30:20,intensity:20});show(x);add(x)}catch(e){fail(e)}}async function sweep(){try{const x=await post('sweep',{...base(),points:[[0,0],[-.5,0],[.5,0],[0,-.5],[0,.5]],channel:$('channel').value,exposure_ms:$('channel').value.includes('Fluorescence')?30:20,intensity:20});show(x);x.frames.forEach(add)}catch(e){fail(e)}}function add(x){if(!x.thumbnail)return;const a=document.createElement('a');a.href=x.image;a.target='_blank';a.innerHTML='<img class="w-full rounded-xl border border-slate-800" src="'+x.thumbnail+'" title="dx '+x.dx+', dy '+x.dy+'">';$('gallery').prepend(a)}</script></body></html>'''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)
