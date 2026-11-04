from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import cv2
import numpy as np

from .config import Settings
from .db import Database
from .ingestion import insert_records


PRODUCTS = [
    ("A", "000000000001", "Rapid-selling snacks", 12, 1.8, 2),
    ("B", "000000000002", "Slow-selling accessories", 18, .12, 3),
    ("C", "000000000003", "Misplaced merchandise", 24, .22, 2),
    ("D", "000000000004", "Unexplained negative variance", 28, .20, 4),
    ("E", "000000000005", "Unrecorded receipt / overage", 24, .18, 3),
    ("F", "000000000006", "Damaged / occluded merchandise", 20, .15, 2),
]


def _write_jsonl(path: Path, rows):
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")


def make_demo(settings: Settings, days: int = 56, seed: int = 71, source_profile: dict | None = None) -> dict:
    """Controlled fixtures. Observations are replayed labels, NOT model-derived detections."""
    if days < 28 or days % 7:
        raise ValueError("Demo days must be a multiple of 7 and at least 28")
    db = Database(settings)
    if db.objects("products"):
        raise ValueError("Demo requires an empty runtime; use a new RETAIL_PULSE_HOME")
    rng = np.random.default_rng(seed)
    source_profile = source_profile or {}
    products_config = source_profile.get("products", PRODUCTS)
    daily_factors = source_profile.get("daily_factors", [1.0])
    tz = ZoneInfo(settings.timezone)
    end = datetime(2026, 10, 26, 7, tzinfo=tz)
    start = (end - timedelta(days=days)).replace(hour=settings.open_hour)
    products, tx, observations, rfid, scans, truth = [], [], [], [], [], []
    frames_state = []
    uid = 0

    def event(sku, at, kind, quantity, ref=""):
        nonlocal uid
        uid += 1
        tx.append(dict(event_id=f"TX{uid:06}", store_id="DEMO_01", sku=sku, at=at.isoformat(),
                       kind=kind, quantity=int(quantity), source="synthetic", business_ref=ref))

    def observe(sku, at, end_at, kind="shelf_state", avail="unknown", count=None,
                conf=.97, visibility=.98, note="", verified=False):
        eid = "demo-video" if at >= end - timedelta(days=7) and not verified else "demo-fixture"
        observations.append(dict(observation_id=f"OBS{len(observations):06}", store_id="DEMO_01", sku=sku,
                                 zone_id=f"Z{sku}", at=at.isoformat(), end_at=end_at.isoformat(), kind=kind,
                                 availability=avail, count_min=count, count_max=count,
                                 count_scope="whole_store_verified" if verified else "visible",
                                 confidence=conf, visibility=visibility, evidence_id=eid,
                                 origin="demo_replay", note=note))

    states = {}
    for j, (sku, upc, title, capacity, rate, pack) in enumerate(products_config):
        col, row = j % 3, j // 3
        products.append(dict(store_id="DEMO_01", sku=sku, upc=upc, title=title, zone_id=f"Z{sku}",
                             camera_id="CAM_DEMO", shelf_capacity=capacity, case_pack=pack, lead_days=1,
                             roi=[col / 3 + .015, row / 2 + .08, (col + 1) / 3 - .015, (row + 1) / 2 - .03]))
        states[sku] = dict(shelf=capacity, misplaced=0, damaged=0, rate=rate, capacity=capacity)
        event(sku, start - timedelta(hours=1), "opening", capacity)
    for day in range(days):
        day_start = start + timedelta(days=day)
        for sku, _, _, capacity, _, _ in products_config:
            s = states[sku]
            if day % 7 == 0 and day > 0:
                count = s["shelf"] + s["misplaced"] + s["damaged"]
                scan_id = f"RF{day:02}{sku}"
                for k in range(count):
                    if rng.random() < .93:
                        rfid.append(dict(read_id=f"{scan_id}-{k}", scan_id=scan_id,
                                         epc=f"TAG-{sku}-{k:04}", store_id="DEMO_01", sku=sku,
                                         zone_id="store", at=(day_start-timedelta(minutes=30)).isoformat()))
                addition = max(0, capacity - s["shelf"])
                if addition:
                    s["shelf"] += addition
                    event(sku, day_start, "receipt", addition, f"PO-{day}-{sku}")
                    observe(sku, day_start, day_start+timedelta(seconds=1), "restock", count=addition)
                    scans.append(dict(scan_id=f"BAR{day}{sku}", store_id="DEMO_01", sku=sku,
                                      upc=next(p["upc"] for p in products if p["sku"] == sku),
                                      zone_id=f"Z{sku}", at=day_start.isoformat(), action="receipt_scan"))
        for hour in range(settings.open_hour, settings.close_hour):
            at = day_start.replace(hour=hour)
            snapshot = {}
            for sku, _, _, _, _, _ in products_config:
                s = states[sku]
                last = day >= days - 7
                if last and day == days-7 and hour == 10 and sku == "D":
                    s["shelf"] -= min(2, s["shelf"])
                    observe(sku, at, at+timedelta(seconds=5), "removal", count=2,
                            note="Unexplained removal; intent and payment status are not established.")
                if last and day == days-6 and hour == 9 and sku == "E":
                    s["shelf"] += 3
                    observe(sku, at, at+timedelta(seconds=5), "restock", count=3,
                            note="Visible replenishment; no matching receipt in this synthetic ledger.")
                if last and day == days-5 and hour == 10 and sku == "C":
                    s["misplaced"] += s["shelf"]
                    s["shelf"] = 0
                    observe(sku, at, at+timedelta(seconds=5), "misplacement",
                            note="Merchandise moved from its assigned zone to an adjacent zone.")
                if last and day == days-4 and hour == 11 and sku == "C":
                    s["shelf"] += s["misplaced"]
                    s["misplaced"] = 0
                    observe(sku, at, at+timedelta(seconds=5), "restock", note="Misplaced units returned; no new receipt.")
                if last and day == days-3 and hour == 10 and sku == "F":
                    moved = min(2, s["shelf"])
                    s["shelf"] -= moved
                    s["damaged"] += moved
                    observe(sku, at, at+timedelta(seconds=5), "damage", count=moved,
                            note="Visible damage; units remain on hand but are not sellable.")
                if last and day == days-2 and hour == 9 and sku == "F" and s["damaged"]:
                    event(sku, at, "disposal", s["damaged"])
                    s["damaged"] = 0
                weekday_factor = 1.22 if at.weekday() >= 5 else 1.0
                demand = int(rng.poisson(s["rate"] * weekday_factor * daily_factors[day % len(daily_factors)]))
                before = s["shelf"]
                sold = min(before, demand)
                s["shelf"] -= sold
                full = before > 0 and s["shelf"] > 0
                fraction = 1.0 if full else (float(rng.uniform(.25, .85)) if before > 0 else 0.0)
                cut = at + timedelta(hours=fraction)
                if sold:
                    event(sku, at+timedelta(hours=fraction/2), "sale", sold)
                occluded = sku == "F" and hour in {12, 13}
                if fraction:
                    observe(sku, at, cut, avail="unknown" if occluded else "available",
                            count=None if occluded else before,
                            visibility=.25 if occluded else .98,
                            note="Fixture availability interval; not machine perception output.")
                if fraction < 1:
                    observe(sku, cut, at+timedelta(hours=1), avail="unknown" if occluded else "unavailable",
                            count=None if occluded else 0, visibility=.25 if occluded else .98)
                truth.append(dict(store_id="DEMO_01", sku=sku, at=at.isoformat(),
                                  demand=demand, sales=sold, lost=demand-sold,
                                  available_hours=fraction, occluded=occluded))
                snapshot[sku] = before
            if day >= days - 7:
                frames_state.append((at, snapshot))
    for sku, s in states.items():
        count = s["shelf"] + s["misplaced"] + s["damaged"]
        observe(sku, end-timedelta(seconds=1), end, kind="count", count=count, verified=True,
                note="Synthetic verified whole-store audit; not an RFID census or a vision count.")
        for k in range(count):
            if rng.random() < .93:
                rfid.append(dict(read_id=f"FINAL-{sku}-{k}", scan_id=f"FINAL-{sku}", epc=f"TAG-{sku}-{k:04}",
                                 store_id="DEMO_01", sku=sku, zone_id="store", at=(end-timedelta(minutes=2)).isoformat()))
    # One synthetic week represented by 28 seconds. Explicit time mapping is retained.
    media_path = settings.home / "media" / "retail_demo.mp4"
    duration = 28.0
    world_start = end-timedelta(days=7)
    fps, size = 8, (960, 540)
    writer = cv2.VideoWriter(str(media_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise RuntimeError("OpenCV cannot create demo MP4 with this build")
    colors = [(110,180,240), (150,210,100), (220,140,100), (140,140,240), (190,160,220), (210,200,120)]
    try:
        for frame in range(int(duration*fps)):
            world_at = world_start + timedelta(seconds=frame/fps * 7*86400/duration)
            eligible = [v for v in frames_state if v[0] <= world_at]
            values = eligible[-1][1] if eligible else {p[0]: p[3] for p in products_config}
            img = np.full((size[1], size[0], 3), 25, dtype=np.uint8)
            cv2.putText(img, "RETAIL PULSE | SYNTHETIC TIME-LAPSE", (22,28), 0, .65, (235,235,235), 1, cv2.LINE_AA)
            cv2.putText(img, world_at.strftime("%Y-%m-%d %H:%M %Z"), (640,28), 0, .5, (200,200,200), 1)
            for j, (sku, _, _, _, _, _) in enumerate(products_config):
                x, y = 15+(j%3)*320, 58+(j//3)*235
                cv2.rectangle(img, (x,y), (x+300,y+200), (90,90,90), 1)
                cv2.putText(img, f"SKU {sku} / zone Z{sku}", (x+10,y+23), 0, .55, (225,225,225), 1)
                n = min(values[sku], 28)
                for k in range(n):
                    px, py = x+12+(k%7)*40, y+42+(k//7)*36
                    cv2.rectangle(img, (px,py), (px+27,py+28), colors[j], -1)
                if n == 0:
                    cv2.putText(img, "EMPTY", (x+105,y+110), 0, .7, (180,180,180), 1)
            writer.write(img)
            if frame == 24:
                cv2.imwrite(str(settings.home/"media"/"shelf_snapshot.png"), img)
    finally:
        writer.release()
    # Browser-compatible H.264; imageio-ffmpeg supplies a binary on Windows too.
    ffmpeg=shutil.which("ffmpeg")
    if not ffmpeg:
        import imageio_ffmpeg
        ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    encoded=media_path.with_name("retail_demo_h264.mp4")
    subprocess.run([ffmpeg,"-y","-loglevel","error","-i",str(media_path),"-an","-c:v","libx264",
                    "-pix_fmt","yuv420p","-movflags","+faststart",str(encoded)],check=True,timeout=60,capture_output=True)
    encoded.replace(media_path)
    evidence = [dict(evidence_id="demo-video", path="media/retail_demo.mp4", media_type="video",
                     store_id="DEMO_01", camera_id="CAM_DEMO", start_at=world_start.isoformat(),
                     duration_seconds=duration, seconds_to_world=7*86400/duration,
                     sha256=hashlib.sha256(media_path.read_bytes()).hexdigest(), synthetic=True),
                dict(evidence_id="demo-fixture", path="", media_type="fixture", store_id="DEMO_01",
                     camera_id="CAM_DEMO", start_at=start.isoformat(), duration_seconds=days*86400,
                     seconds_to_world=1, sha256="synthetic-ground-truth", synthetic=True)]
    source_dir = settings.home/"demo_inputs"
    source_dir.mkdir(exist_ok=True)
    summaries = {}
    for table, rows in [("products",products), ("evidence",evidence), ("transactions",tx),
                        ("rfid_reads",rfid), ("barcode_scans",scans), ("observations",observations)]:
        _write_jsonl(source_dir/f"{table}.jsonl", rows)
        summaries[table] = insert_records(db, table, rows, "synthetic_demo", strict=True)
    # Evaluation-only labels are not loaded into any operational table or agent tool.
    (settings.home/"ground_truth.json").write_text(json.dumps(truth), encoding="utf-8")
    db.metadata("demo", {"seed":seed,"days":days,"as_of":end.isoformat(),"start":start.isoformat(),
                         "notice":"Synthetic replay. Does not benchmark Muse/SAM perception."})
    if source_profile:
        db.metadata("source_profile", source_profile)
    return {"inputs":summaries, "as_of":end.isoformat(), "media":str(media_path)}
