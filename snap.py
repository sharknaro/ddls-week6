#!/usr/bin/env python3
"""Take one DDLS brightfield or fluorescence frame using atomic snap coordinates."""
from __future__ import annotations

import argparse
import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://ddls-gateway-b69bb891.svc.hypha.aicell.io/v1"
TOKEN = "bvLyc_eTjHCe92a4IYFiSNVPt4dPtZHtnFXoPVfM2Kk"
ALLOWED_PLATES = {"A", "B"}
ALLOWED_WELLS = {"B11", "B12"}
RETRY_CODES = {429, 503}
MAX_RETRIES = 7


def request_json(method: str, endpoint: str, payload: dict | None = None, timeout: float = 30.0) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    request = Request(BASE_URL + endpoint, data=body, method=method, headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try: detail = json.loads(raw)
            except json.JSONDecodeError: detail = {}
            if exc.code not in RETRY_CODES or attempt == MAX_RETRIES - 1: raise RuntimeError(f"HTTP {exc.code}: {raw}") from exc
            delay = max(float(detail.get("retry_after_s", 0) or 0), min(30.0, 2**attempt))
            time.sleep(delay)
        except (TimeoutError, URLError) as exc:
            if attempt == MAX_RETRIES - 1: raise RuntimeError(str(exc)) from exc
            time.sleep(min(30.0, 2**attempt))
    raise RuntimeError("request retries exhausted")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plate", required=True, choices=sorted(ALLOWED_PLATES))
    parser.add_argument("--well", required=True, choices=sorted(ALLOWED_WELLS))
    parser.add_argument("--channel", default="BF_LED_matrix_full", choices=["BF_LED_matrix_full", "Fluorescence_488_nm_Ex"])
    parser.add_argument("--dx", type=float, default=0.0)
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path("frames"))
    parser.add_argument("--exposure-ms", type=float, default=None)
    parser.add_argument("--intensity", type=float, default=None)
    args = parser.parse_args()
    if args.dx * args.dx + args.dy * args.dy > 1: parser.error("dx² + dy² must be <= 1")
    status = request_json("GET", f"/status?plate={args.plate}")
    scale = status.get("result", {}).get("scale", {})
    if scale.get("pixel_size_um") is None: raise RuntimeError("status did not return result.scale.pixel_size_um")
    autofocus = request_json("POST", "/focus", {"plate": args.plate, "well": args.well})
    settings = {"well": args.well, "plate": args.plate, "channel": args.channel, "dx": args.dx, "dy": args.dy}
    if args.exposure_ms is not None: settings["exposure_ms"] = args.exposure_ms
    if args.intensity is not None: settings["intensity"] = args.intensity
    response = request_json("POST", "/snap", settings, timeout=30.0 if args.channel.startswith("Fluorescence") else 30.0)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    directory = args.output / f"plate_{args.plate}" / f"well_{args.well}"
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"{timestamp}_{args.channel}"
    full = directory / f"{stem}.png"; thumb = directory / f"{stem}_thumb.png"; metadata = directory / f"{stem}.json"
    full.write_bytes(base64.b64decode(response["image_png_b64"]))
    from PIL import Image
    with Image.open(full) as image:
        image.thumbnail((768, 768), Image.Resampling.LANCZOS)
        image.save(thumb, format="PNG")
    metadata.write_text(json.dumps({"plate": args.plate, "well": args.well, "dx": args.dx, "dy": args.dy, "requested": settings, "returned_position_mm": response.get("position_mm"), "autofocus": autofocus, "pixel_size_um": scale["pixel_size_um"], "fov_um": scale.get("fov_um"), "utc_timestamp": timestamp, "full_resolution": str(full), "thumbnail": str(thumb)}, indent=2) + "\n")
    print(json.dumps({"full_resolution": str(full), "thumbnail": str(thumb), "metadata": str(metadata), "pixel_size_um": scale["pixel_size_um"], "fov_um": scale.get("fov_um"), "position_mm": response.get("position_mm")}, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())
