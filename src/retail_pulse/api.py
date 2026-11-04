from __future__ import annotations

import hmac
import json
import shutil
import uuid
from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .agents import run_agent
from .config import Settings
from .db import Database
from .fusion import parse_time
from .ingestion import import_file, normalize_time
from .meta_client import MetaError, usage_summary
from .monitor import monitor_once
from .perception import analyze_media, register_media
from .pipeline import run_pipeline
from .schemas import QueryRequest
from .operations import CaseAction,PosEvent,Conflict


WEB=Path(__file__).parent/"web"


def create_app(settings:Settings|None=None) -> FastAPI:
    settings=settings or Settings.from_env()
    db=Database(settings)
    app=FastAPI(title="Retail Pulse",version="0.1.0",description="Local research prototype; advisory only.")
    app.state.db=db; app.state.settings=settings

    @app.middleware("http")
    async def local_security(request:Request,call_next):
        host=request.headers.get("host","")
        hostname=host.split(":")[0]
        if not settings.api_token and hostname not in {"localhost","127.0.0.1","testserver"}:
            return JSONResponse({"detail":"Configure RETAIL_PULSE_API_TOKEN for non-local access"},status_code=403)
        origin=request.headers.get("origin")
        if origin and origin not in {f"http://{host}",f"https://{host}"}:
            return JSONResponse({"detail":"Cross-origin access is disabled"},status_code=403)
        response=await call_next(request)
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Referrer-Policy"]="no-referrer"
        if request.url.path=="/":
            response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; media-src 'self' blob:; connect-src 'self'; frame-ancestors 'none'"
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"]="no-store"
        return response

    def authorize(request:Request):
        if settings.api_token:
            auth=request.headers.get("authorization","")
            supplied=auth[7:] if auth.startswith("Bearer ") else ""
            if not hmac.compare_digest(supplied,settings.api_token):
                raise HTTPException(401,"Valid local API bearer token required")

    protected=[Depends(authorize)]

    @app.exception_handler(MetaError)
    async def meta_exception(request,exc):
        return JSONResponse({"detail":str(exc)},status_code=502)

    @app.exception_handler(ValueError)
    async def value_exception(request,exc):
        return JSONResponse({"detail":str(exc)},status_code=400)

    @app.exception_handler(Conflict)
    async def conflict_exception(request,exc):
        return JSONResponse({'detail':str(exc)},status_code=409)

    @app.get("/healthz")
    def healthz():
        return {"status":"ok","version":"0.1.0"}

    @app.get("/")
    def index():
        return FileResponse(WEB/"index.html")

    @app.get("/api/config",dependencies=protected)
    def config():
        return {"mode":settings.mode,"live_ready":settings.mode=="meta" and bool(settings.api_key),
                "default_store":db.metadata("default_store"),"external_media":settings.external_media,"timezone":settings.timezone,
                "muse_model":settings.muse_model,"sam_model":settings.sam_model,
                "stores":sorted({p["store_id"] for p in db.objects("products")}),
                "max_media_mb":settings.max_media_mb,"max_video_seconds":settings.max_video_seconds}

    @app.get("/api/overview",dependencies=protected)
    def overview(store_id:str="DEMO_01"):
        result=db.current_overview(store_id)
        if not result:
            raise HTTPException(404,"No report. Run: python -m retail_pulse demo")
        result["health"]=db.latest_report("health",store_id) or result["health"]
        result["benchmark"]=db.latest_report("benchmark",store_id)
        result["usage"]=usage_summary(db)
        return result

    @app.get("/api/catalog",dependencies=protected)
    def catalog(store_id:str="DEMO_01"):
        return db.objects("products",store_id)

    @app.get('/api/library',dependencies=protected)
    def library():
        return dict(warehouse=db.metadata('warehouse'),assets=db.metadata('source_assets') or [])

    @app.get('/api/library/browse',dependencies=protected)
    def library_browse(dataset:str='m5',store:str|None=None,query:str=Query('',max_length=100),
                       sku:str|None=Query(None,max_length=100),offset:int=Query(0,ge=0),limit:int=Query(50,ge=1,le=100)):
        from .warehouse import browse
        if not (settings.home/'warehouse.duckdb').exists():raise HTTPException(404,'Prepare the local source warehouse first')
        return browse(settings,dataset,store,query,offset,limit,sku)

    @app.get('/api/video-flow',dependencies=protected)
    def video_flow():
        return db.metadata('video_flow') or {}

    @app.get('/api/model-lab',dependencies=protected)
    def model_lab():
        return db.metadata('model_lab') or {}

    @app.get('/api/forecast-benchmark',dependencies=protected)
    def forecast_benchmark():
        return db.metadata('forecast_benchmark') or {}

    @app.get('/api/visual-grounding',dependencies=protected)
    def visual_grounding():
        return db.metadata('visual_grounding') or {}

    @app.get('/api/operations',dependencies=protected)
    def operations(minutes:int=Query(10,ge=3,le=120),delay_hours:float=Query(3,ge=.25,le=24)):
        from .operations import desk
        return desk(db,minutes,delay_hours)

    @app.post('/api/operations/cases/{case_id}',dependencies=protected)
    def operation_action(case_id:str,body:CaseAction):
        from .operations import act
        return act(db,case_id,body)

    @app.post('/api/operations/replay-sale',dependencies=protected)
    def operation_replay():
        from .operations import replay_next
        return replay_next(db)

    @app.post('/api/pos-events',dependencies=protected)
    def pos_event(body:PosEvent):
        from .operations import ingest_sale
        return ingest_sale(db,body)

    @app.post('/api/operations/brief',dependencies=protected)
    def operations_brief():
        with db.lease('operations-muse-brief',300):
            result=run_agent(db,db.metadata('default_store') or 'STOCK_STR_1010',
              'Use get_operations, get_visual_grounding and get_forecast_benchmark. Give the retail operations manager a brief: what happened, which count is disputed and why, what human action should happen next, how received sales feed supply-chain review, and what the real seven-day evaluation establishes. Distinguish historical POS replay from a live merchant feed and normalized forecasts from unit orders. Cite exact returned evidence and metrics. Do not claim a refill, sale, savings or order that has not been recorded.', 'business',settings.mode)
            db.metadata('operations_brief',result)
            return result

    @app.get('/api/operations/brief',dependencies=protected)
    def latest_operations_brief():
        return db.metadata('operations_brief')

    @app.get("/api/events",dependencies=protected)
    def events(store_id:str="DEMO_01",sku:str|None=None,kind:str|None=None,
               limit:int=Query(100,ge=1,le=1000),offset:int=Query(0,ge=0)):
        rows=db.objects("observations",store_id)
        if sku:
            rows=[o for o in rows if o["sku"]==sku]
        if kind:
            rows=[o for o in rows if o["kind"]==kind]
        rows.sort(key=lambda o:o["at"],reverse=True)
        return {"total":len(rows),"offset":offset,"items":rows[offset:offset+limit]}

    @app.post("/api/analyze-camera/{evidence_id}",dependencies=protected)
    def analyze_camera_endpoint(evidence_id:str,store_id:str):
        evidence=db.evidence(evidence_id)
        if not evidence or evidence["store_id"]!=store_id:
            raise HTTPException(404,"Unknown evidence in this store")
        from .camera_ai import analyze_camera
        with db.lease("camera:"+evidence_id):
            return analyze_camera(db,evidence_id)

    @app.get("/api/latest-agent",dependencies=protected)
    def latest_agent(store_id:str,role:str="business"):
        rows=db.rows("SELECT data FROM agent_runs WHERE store_id=? AND role=? AND json_extract(data,'$.mode')='meta' ORDER BY at DESC LIMIT 1",(store_id,role))
        return json.loads(rows[0]["data"]) if rows else None

    @app.get("/api/camera-timeline/{evidence_id}",dependencies=protected)
    def camera_timeline(evidence_id:str,store_id:str="DEMO_01"):
        result=db.metadata("camera_timeline:"+evidence_id)
        if not result or result["store_id"]!=store_id:
            raise HTTPException(404,"No recorded camera analysis for this store/clip")
        return result

    @app.get("/api/evidence",dependencies=protected)
    def evidence(store_id:str="DEMO_01"):
        return [dict({k:v for k,v in e.items() if k!="path"}, camera_analysis=bool(db.metadata("camera_timeline:"+e["evidence_id"]))) for e in db.objects("evidence",store_id)]

    @app.get("/api/media/{evidence_id}",dependencies=protected)
    def media(evidence_id:str):
        try:
            path=db.safe_media_path(evidence_id)
        except (FileNotFoundError,ValueError):
            raise HTTPException(404,"Playable evidence not available")
        return FileResponse(path,media_type="video/mp4" if path.suffix in {".mp4",".mov"} else None)

    @app.get("/api/daily",dependencies=protected)
    def daily(store_id:str="DEMO_01"):
        # Store ID must refer to a known catalog key before constructing any path.
        if store_id not in {p["store_id"] for p in db.objects("products")}:
            raise HTTPException(404,"Unknown store")
        path=settings.home/"reports"/f"daily_exposure_{store_id}.csv"
        if not path.exists():return []
        frame=pd.read_csv(path,dtype={"sku":str})
        return frame.astype(object).where(pd.notna(frame),None).to_dict("records")

    @app.post("/api/ask",dependencies=protected)
    def ask(body:QueryRequest):
        return run_agent(db,body.store_id,body.question,body.role,body.mode or settings.mode)

    @app.post("/api/health-review",dependencies=protected)
    def health_review(store_id:str="DEMO_01",agent:bool=False):
        return monitor_once(settings,store_id,agent)

    @app.post("/api/run",dependencies=protected)
    def run(store_id:str="DEMO_01"):
        try:
            return run_pipeline(settings,store_id)
        except RuntimeError as exc:
            raise HTTPException(409,str(exc))

    def save_upload(file:UploadFile) -> Path:
        suffix=Path(file.filename or "").suffix.lower()
        if suffix not in {".mp4",".mov",".png",".jpg",".jpeg",".csv",".json",".jsonl"}:
            raise HTTPException(400,"Unsupported extension")
        path=settings.home/"raw"/f"upload-{uuid.uuid4().hex}{suffix}"
        size=0
        try:
            with path.open("wb") as f:
                while chunk:=file.file.read(1024*1024):
                    size+=len(chunk)
                    if size>settings.max_media_mb*1024**2:
                        raise HTTPException(413,"Upload exceeds configured maximum")
                    f.write(chunk)
            return path
        except Exception:
            path.unlink(missing_ok=True)
            raise

    @app.post("/api/upload-media",dependencies=protected)
    def upload_media(file:UploadFile=File(...),store_id:str=Form(...),camera_id:str=Form(...),
                     start_at:str=Form(...),source_timezone:str=Form("America/Denver"),
                     clock_offset_seconds:float=Form(0),analyze:bool=Form(False),sam_prompt:str=Form("")):
        path=save_upload(file)
        try:
            start=normalize_time(start_at,source_timezone,clock_offset_seconds)
            e=register_media(db,path,store_id,camera_id,start)
            result={"evidence":e.model_dump(mode="json")}
            if analyze:
                result["analysis"]=analyze_media(db,e.evidence_id,sam_prompt or None)
                result["pipeline"]=run_pipeline(settings,store_id)
                # Requested step-4 agent runs AFTER validated numeric observations reach the DB.
                result["health_agent"]=run_agent(db,store_id,"Review health after new visual evidence ingestion.","health",settings.mode)
            return result
        finally:
            path.unlink(missing_ok=True)

    @app.post("/api/import",dependencies=protected)
    def import_data(file:UploadFile=File(...),table:str=Form(...),source_timezone:str=Form("America/Denver")):
        path=save_upload(file)
        try:
            return import_file(db,table,path,source_timezone)
        finally:
            path.unlink(missing_ok=True)

    app.mount("/static",StaticFiles(directory=WEB),name="static")
    return app
