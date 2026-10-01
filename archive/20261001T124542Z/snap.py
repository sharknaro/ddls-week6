#!/usr/bin/env python3
"""Validated DDLS microscope acquisition helper.

This module performs acquisition only. It does not interpret biology.
"""
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
ALLOWED_PLATES = {"A", "B"}
ALLOWED_WELLS = {"B11", "B12"}
BF_CHANNEL = "BF_LED_matrix_full"
FL_CHANNEL = "Fluorescence_488_nm_Ex"
DEFAULT_BF_EXPOSURE_MS = 20.0
DEFAULT_BF_INTENSITY = 20.0
DEFAULT_FL_EXPOSURE_MS = 30.0
DEFAULT_FL_INTENSITY = 20.0
RETRY_STATUSES = {429, 503}
MAX_RETRIES = 7
REQUEST_TIMEOUT_SECONDS = 30.0
FL_TIMEOUT_SECONDS = 30.0


def request_json(method: str, endpoint: str, token: str, payload: dict | None = None, *, timeout: float = REQUEST_TIMEOUT_SECONDS) -> dict:
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    for attempt in range(MAX_RETRIES):
        request = Request(BASE_URL + endpoint, data=body, method=method, headers=headers)
        try:
            with urlopen(request, timeout=timeout) as response:
                return json.loads(response.read())
        except HTTPError as exc:
            raw = exc.read().decode(errors="replace")
            try:
                detail = json.loads(raw)
            except json.JSONDecodeError:
                detail = {"error": raw}
            if exc.code not in RETRY_STATUSES or attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"{method} {endpoint} failed ({exc.code}): {detail}") from exc
            retry_after = detail.get("retry_after_s", 0) if isinstance(detail, dict) else 0
            delay = max(float(retry_after or 0), min(30.0, 2**attempt))
            print(f"{method} {endpoint}: HTTP {exc.code}; retrying in {delay:g}s", file=sys.stderr)
            time.sleep(delay)
        except (TimeoutError, URLError) as exc:
            if attempt == MAX_RETRIES - 1:
                raise RuntimeError(f"{method} {endpoint} failed: {exc}") from exc
            delay = min(30.0, 2**attempt)
            print(f"{method} {endpoint}: {exc}; retrying in {delay:g}s", file=sys.stderr)
            time.sleep(delay)
    raise RuntimeError(f"{method} {endpoint} exhausted retries")


def validate_location(plate: str, well: str, dx: float, dy: float) -> None:
    if plate not in ALLOWED_PLATES:
        raise ValueError(f"plate must be A or B, got {plate!r}")
    if well not in ALLOWED_WELLS:
        raise ValueError(f"well must be B11 or B12, got {well!r}")
    if not (-1.0 <= dx <= 1.0 and -1.0 <= dy <= 1.0):
        raise ValueError("dx and dy must each be between -1 and 1")
    if dx * dx + dy * dy > 1.0:
        raise ValueError("dx² + dy² must be <= 1 for the round well")


def output_directory(root: Path, plate: str, well: str) -> Path:
    """Append exactly one plate/well pair to the caller's output root."""
    output = root / f"plate_{plate}" / f"well_{well}"
    output.mkdir(parents=True, exist_ok=True)
    return output


def decode_png(response: dict) -> bytes:
    encoded = response.get("image_png_b64")
    if not encoded:
        raise RuntimeError("snap response did not contain image_png_b64")
    return base64.b64decode(encoded)


def save_acquisition(response: dict, directory: Path, stem: str, metadata: dict) -> dict[str, str]:
    full_path = directory / f"{stem}.png"
    thumb_path = directory / f"{stem}_thumb.png"
    metadata_path = directory / f"{stem}.json"
    if full_path.exists() or thumb_path.exists() or metadata_path.exists():
        raise FileExistsError(f"refusing to overwrite acquisition files for {stem}")
    full_path.write_bytes(decode_png(response))
    try:
        from PIL import Image
        with Image.open(full_path) as image:
            image.thumbnail((768, 768), Image.Resampling.LANCZOS)
            image.save(thumb_path, format="PNG")
    except ImportError as exc:
        raise RuntimeError("Pillow is required for thumbnail generation") from exc
    metadata = {**metadata, "file_paths": {"full_resolution": str(full_path), "thumbnail": str(thumb_path), "metadata": str(metadata_path)}}
    metadata_path.write_text(json.dumps(metadata, indent=2, default=str) + "\n", encoding="utf-8")
    return {"full_resolution": str(full_path), "thumbnail": str(thumb_path), "metadata": str(metadata_path)}


def acquire_one(*, token: str, plate: str, well: str, dx: float, dy: float, channel: str, exposure_ms: float, intensity: float, directory: Path, status: dict, autofocus: dict, timestamp: str) -> dict:
    payload = {"well": well, "plate": plate, "channel": channel, "exposure_ms": exposure_ms, "intensity": intensity, "dx": dx, "dy": dy}
    timeout = FL_TIMEOUT_SECONDS if channel == FL_CHANNEL else REQUEST_TIMEOUT_SECONDS
    response = request_json("POST", "/snap", token, payload, timeout=timeout)
    metadata = {
        "plate": plate,
        "well": well,
        "dx": dx,
        "dy": dy,
        "requested": {"channel": channel, "exposure_ms": exposure_ms, "intensity": intensity},
        "returned": {"position_mm": response.get("position_mm")},
        "autofocus": autofocus,
        "pixel_size_um": status["pixel_size_um"],
        "fov_um": status["fov_um"],
        "utc_timestamp": timestamp,
    }
    stem = f"{timestamp}_{plate}_{well}_{channel}"
    paths = save_acquisition(response, directory, stem, metadata)
    return {"channel": channel, "paths": paths, "metadata": metadata, "response": response}


def prepare_field(token: str, plate: str, well: str) -> tuple[dict, dict]:
    status_response = request_json("GET", f"/status?plate={plate}", token)
    scale = status_response.get("result", {}).get("scale", {})
    pixel_size_um = scale.get("pixel_size_um")
    fov_um = scale.get("fov_um")
    if pixel_size_um is None or fov_um is None:
        raise RuntimeError("status response did not contain result.scale.pixel_size_um and result.scale.fov_um")
    autofocus = request_json("POST", "/focus", token, {"well": well, "plate": plate})
    status = {"response": status_response, "pixel_size_um": pixel_size_um, "fov_um": fov_um}
    return status, autofocus


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--plate", required=True, choices=sorted(ALLOWED_PLATES))
    parser.add_argument("--well", required=True, choices=sorted(ALLOWED_WELLS))
    parser.add_argument("--dx", type=float, default=0.0)
    parser.add_argument("--dy", type=float, default=0.0)
    parser.add_argument("--output", type=Path, default=Path("survey_frames"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    pair = subparsers.add_parser("pair", help="status -> autofocus once -> BF -> FL at one atomic field")
    add_common_arguments(pair)
    bf_only = subparsers.add_parser("bf-only", help="status -> autofocus once -> BF at one atomic field")
    add_common_arguments(bf_only)
    bf_only.add_argument("--exposure-ms", type=float, default=DEFAULT_BF_EXPOSURE_MS)
    bf_only.add_argument("--intensity", type=float, default=DEFAULT_BF_INTENSITY)
    args = parser.parse_args()
    token = os.environ.get("DDLS_TOKEN")
    if not token:
        parser.error("DDLS_TOKEN environment variable is required")
    try:
        validate_location(args.plate, args.well, args.dx, args.dy)
        directory = output_directory(args.output, args.plate, args.well)
        status, autofocus = prepare_field(token, args.plate, args.well)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        results = []
        results.append(acquire_one(token=token, plate=args.plate, well=args.well, dx=args.dx, dy=args.dy, channel=BF_CHANNEL, exposure_ms=DEFAULT_BF_EXPOSURE_MS if args.command == "pair" else args.exposure_ms, intensity=DEFAULT_BF_INTENSITY if args.command == "pair" else args.intensity, directory=directory, status=status, autofocus=autofocus, timestamp=timestamp))
        if args.command == "pair":
            fl_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            results.append(acquire_one(token=token, plate=args.plate, well=args.well, dx=args.dx, dy=args.dy, channel=FL_CHANNEL, exposure_ms=DEFAULT_FL_EXPOSURE_MS, intensity=DEFAULT_FL_INTENSITY, directory=directory, status=status, autofocus=autofocus, timestamp=fl_timestamp))
        print(json.dumps({"plate": args.plate, "well": args.well, "dx": args.dx, "dy": args.dy, "status": status, "autofocus": autofocus, "acquisitions": [{"channel": item["channel"], "paths": item["paths"]} for item in results]}, indent=2, default=str))
        return 0
    except (RuntimeError, ValueError, FileExistsError) as exc:
        print(f"snap.py: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
