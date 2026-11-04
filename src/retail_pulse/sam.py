from __future__ import annotations

import re
from pathlib import Path

import cv2

from .meta_client import MetaClient, output_text

FRAME=re.compile(r"<([0-9]+)f>")
RECORD=re.compile(r"([0-9]+)<\|box;([^|]+)\|><\|mask;(.*?)\|>")


def parse_sam_output(text:str) -> list[dict]:
    """Parse documented boxes, frame/track IDs and preserve encoded masks verbatim.

    No fabricated pixel-mask decoder: the mask codec is retained for an official
    decoder. Bounding-box coverage must NOT be described as exact mask occupancy.
    """
    if not text.strip():
        return []
    records=[]
    for line in text.splitlines():
        if not line.strip():
            continue
        frame=FRAME.match(line.strip())
        if not frame:
            raise ValueError("Unrecognized SAM frame marker")
        matches=list(RECORD.finditer(line))
        if not matches:
            raise ValueError("Unrecognized SAM record grammar; raw response retained")
        for match in matches:
            values=dict(pair.split("=",1) for pair in match.group(2).split(";"))
            box={k:int(values[k]) for k in ["x1","y1","x2","y2","w","h"]}
            if not 0<=box["x1"]<=box["x2"]<box["w"] or not 0<=box["y1"]<=box["y2"]<box["h"]:
                raise ValueError("SAM box outside source image")
            records.append(dict(frame_index=int(frame.group(1)),object_id=int(match.group(1)),box=box,
                                confidence=float(values["c"]) if "c" in values else None,
                                mask_encoded=match.group(3)))
    return records


def segment(client:MetaClient,media_part:dict,prompt:str,video_frames:int=0) -> dict:
    if not prompt.strip() or len(prompt)>120 or any(x in prompt for x in [",","\n",";"]):
        raise ValueError("SAM prompt must be one short object noun phrase")
    cost=video_frames*client.settings.sam_frame_price if video_frames else client.settings.sam_image_price
    response=client.create_response({"model":client.settings.sam_model,"input":[{"type":"message","role":"user",
                                    "content":[{"type":"input_text","text":prompt},media_part]}],
                                    "metadata":{"include_confidence":"true","mask_encoding":"one_bit"}},
                                   "sam_segmentation",unit_cost=cost)
    text=output_text(response)
    return {"raw_text":text,"records":parse_sam_output(text),"model":client.settings.sam_model,
            "note":"IDs valid within this response, not guaranteed across full occlusions or separate clips."}


def render_box_overlay(image:Path,records:list[dict],destination:Path) -> None:
    frame=cv2.imread(str(image))
    if frame is None:
        raise ValueError("Cannot decode image")
    height,width=frame.shape[:2]
    for r in records:
        b=r["box"]
        p1=(int(b["x1"]*width/b["w"]),int(b["y1"]*height/b["h"]))
        p2=(int(b["x2"]*width/b["w"]),int(b["y2"]*height/b["h"]))
        cv2.rectangle(frame,p1,p2,(60,220,180),2)
        cv2.putText(frame,f"track {r['object_id']}",(p1[0],max(15,p1[1]-6)),0,.5,(60,220,180),1)
    if not cv2.imwrite(str(destination),frame):
        raise RuntimeError("Could not save overlay")
