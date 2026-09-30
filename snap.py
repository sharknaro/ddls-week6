#!/usr/bin/env python3
"""Capture a DDLS microscope frame, autofocus first, and save full-size + thumbnail PNGs."""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://ddls-gateway-b69bb891.svc.hypha.aicell.io/v1"
RETRY_STATUSES = {429, 503}
MAX_RETRIES = 7


def request_json(method: str, endpoint: str, token: str, payload: dict | None = None) -> dict:
    body = None if payload is None else json.dumps(payload).encode()
    req = Request(
        BASE_URL + endpoint,
        data=body,
        method=method,
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    for attempt in range(MAX_RETRIES):
        try:
            with urlopen(req, timeout=30) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                detail = {"error": raw}
            if exc.code not in RETRY_STATUSES or attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"{method} {endpoint} failed ({exc.code}): {detail}") from exc
            delay = float(detail.get("retry_after_s", 0)) if isinstance(detail, dict) else 0
            delay = max(delay, min(30.0, 2**attempt))
            print(f"Shared scope busy ({exc.code}); retrying in {delay:g}s...", file=sys.stderr)
            time.sleep(delay)
        except (TimeoutError, URLError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"{method} {endpoint} failed: {exc}") from exc
            delay = min(30.0, 2**attempt)
            print(f"Request failed; retrying in {delay:g}s...", file=sys.stderr)
            time.sleep(delay)
    raise AssertionError("unreachable")


def save_images(response: dict, output: Path, stem: str) -> tuple[Path, Path]:
    encoded = response.get("image_png_b64")
    if not encoded:
        raise RuntimeError("snap response did not contain image_png_b64")
    full_path = output / f"{stem}.png"
    thumb_path = output / f"{stem}_thumb.png"
    full_path.write_bytes(base64.b64decode(encoded))

    try:
        from PIL import Image
        with Image.open(full_path) as image:
            image.thumbnail((768, 768), Image.Resampling.LANCZOS)
            image.save(thumb_path, format="PNG")
    except ImportError as exc:
        raise RuntimeError("Pillow is required for thumbnail generation: python -m pip install Pillow") from exc
    return full_path, thumb_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--well", required=True, help="Your well, e.g. B11")
    parser.add_argument("--plate", required=True, help="A, B, or the printed plate barcode")
    parser.add_argument("--channel", default="BF_LED_matrix_full", choices=["BF_LED_matrix_full", "Fluorescence_488_nm_Ex"])
    parser.add_argument("--dx", type=float, default=0.0)
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--exposure-ms", type=float, default=20.0)
    parser.add_argument("--intensity", type=float, default=20.0)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "survey_frames")
    args = parser.parse_args()
    token = os.environ.get("DDLS_TOKEN")
    if not token:
        parser.error("DDLS_TOKEN environment variable is required")
    if args.dx * args.dx + args.dy * args.dy > 1:
        parser.error("dx² + dy² must be <= 1")

    args.output = args.output / f"plate_{args.plate}" / f"well_{args.well}"
    args.output.mkdir(parents=True, exist_ok=True)
    common = {"well": args.well, "plate": args.plate}
    # Autofocus is deliberately a separate operation before the atomic snap.
    autofocus = request_json("POST", "/focus", token, common)
    status = request_json("GET", f"/status?plate={args.plate}", token)
    scale = status.get("result", {}).get("scale", {}).get("pixel_size_um")
    if scale is None:
        raise RuntimeError("status response did not contain result.scale.pixel_size_um")
    snap_payload = {**common, "channel": args.channel, "exposure_ms": args.exposure_ms, "intensity": args.intensity, "dx": args.dx, "dy": args.dy}
    response = request_json("POST", "/snap", token, snap_payload)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    stem = f"{timestamp}_{args.plate}_{args.well}_{args.channel}"
    full_path, thumb_path = save_images(response, args.output, stem)
    result = {"full": str(full_path), "thumbnail": str(thumb_path), "pixel_size_um": scale, "position_mm": response.get("position_mm"), "autofocus": autofocus}
    print(json.dumps(result, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
