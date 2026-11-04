from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Settings


def show(value):
    print(json.dumps(value,indent=2,default=str,allow_nan=False))


def main(argv=None):
    parser=argparse.ArgumentParser(description="Retail Pulse research prototype")
    parser.add_argument("--home",type=Path,help="Override runtime directory (before subcommand)")
    sub=parser.add_subparsers(dest="command",required=True)
    demo=sub.add_parser("demo",help="Generate synthetic data, run pipeline, evaluate; no paid API calls")
    demo.add_argument("--seed",type=int,default=71); demo.add_argument("--days",type=int,default=56)
    demo.add_argument("--datasets",type=Path,help="Profile all nine collected sources for a synthetic demo")
    real=sub.add_parser("prepare-real",help="Build dashboards from source-native measured records")
    real.add_argument("--datasets",type=Path,default=Path("data/external"))
    camera=sub.add_parser("camera-demo",help="Prepare real MERL video and local observation timelines")
    camera.add_argument("--datasets",type=Path,default=Path("data/external"))
    serve=sub.add_parser("serve",help="Serve dashboard and API")
    serve.add_argument("--host",default="127.0.0.1"); serve.add_argument("--port",type=int,default=8000)
    run=sub.add_parser("run",help="Explicitly recompute analytics and evaluate/refit forecasting candidate")
    run.add_argument("--store",default="DEMO_01"); run.add_argument("--as-of")
    imp=sub.add_parser("import",help="Validate and idempotently import normalized source records")
    imp.add_argument("--table",required=True,choices=["products","transactions","observations","rfid_reads","barcode_scans","evidence"])
    imp.add_argument("--file",type=Path,required=True); imp.add_argument("--timezone")
    imp.add_argument("--clock-offset",type=float,default=0)
    media=sub.add_parser("media",help="Register image/video and optionally analyze with Muse/SAM")
    media.add_argument("--file",type=Path,required=True); media.add_argument("--store",required=True)
    media.add_argument("--camera",required=True); media.add_argument("--start",required=True)
    media.add_argument("--timezone"); media.add_argument("--clock-offset",type=float,default=0)
    media.add_argument("--time-scale",type=float,default=1)
    media.add_argument("--sam-prompt"); media.add_argument("--analyze",action="store_true")
    ask=sub.add_parser("ask",help="Read-only business/health agent; mode is explicit")
    ask.add_argument("question"); ask.add_argument("--store",default="DEMO_01")
    ask.add_argument("--role",choices=["business","health"],default="business")
    ask.add_argument("--mode",choices=["demo","meta"])
    health=sub.add_parser("health",help="Recompute diagnostics; optionally ask Muse to interpret")
    health.add_argument("--store",default="DEMO_01"); health.add_argument("--agent",action="store_true"); health.add_argument("--as-of")
    watch=sub.add_parser("watch",help="Foreground monitoring; Ctrl+C stops; no hidden background service")
    watch.add_argument("--store",default="DEMO_01"); watch.add_argument("--interval",type=int,default=300)
    watch.add_argument("--agent",action="store_true")
    ev=sub.add_parser("evaluate",help="Held-out synthetic-demand evaluation, clearly labeled")
    ev.add_argument("--store",default="DEMO_01")
    sub.add_parser("doctor",help="Inspect configuration, without printing secrets")
    sub.add_parser("smoke-meta",help="Explicit paid text request to verify Meta credentials")
    args=parser.parse_args(argv)
    try:
        settings=Settings.from_env(**({"home":args.home} if args.home else {}))
        from .db import Database
        db=Database(settings)
        if getattr(args,"store",None)=="DEMO_01" and not db.objects("products","DEMO_01") and db.metadata("default_store"):
            args.store=db.metadata("default_store")
        if args.command=="demo":
            from .demo import make_demo
            from .pipeline import run_pipeline
            from .evaluation import evaluate_synthetic
            if db.objects("products"):
                raise ValueError("Demo requires an empty runtime; use --home with a new directory")
            profile = None
            if args.datasets:
                from .source_demo import build_profile
                profile = build_profile(args.datasets, settings.home)
            data=make_demo(settings,args.days,args.seed,profile)
            r=run_pipeline(settings)
            b=evaluate_synthetic(db)
            show({"runtime":str(settings.home),"data":data,"health":r["health"]["status"],
                  "selected_model":r["model"].get("model"),"benchmark":b,
                  "next":"python -m retail_pulse serve"})
        elif args.command=="prepare-real":
            from .real_data import prepare_real_data
            show(prepare_real_data(settings,args.datasets))
        elif args.command=="camera-demo":
            from .camera_demo import prepare_camera_demo
            show(prepare_camera_demo(settings,args.datasets))
        elif args.command=="serve":
            if args.host not in {"127.0.0.1","localhost"} and not settings.api_token:
                raise ValueError("Non-local binding requires RETAIL_PULSE_API_TOKEN; production still needs TLS and proper identity/access controls")
            import uvicorn
            from .api import create_app
            uvicorn.run(create_app(settings),host=args.host,port=args.port,workers=1,access_log=False)
        elif args.command=="run":
            from .pipeline import run_pipeline
            r=run_pipeline(settings,args.store,args.as_of)
            show({"health":r["health"]["status"],"as_of":r["as_of"],"report":str(settings.home/"reports"/f"overview_{args.store}.json")})
        elif args.command=="import":
            from .ingestion import import_file
            show(import_file(db,args.table,args.file,args.timezone,args.clock_offset))
        elif args.command=="media":
            from .perception import register_media,analyze_media
            from .ingestion import normalize_time
            e=register_media(db,args.file,args.store,args.camera,normalize_time(args.start,args.timezone,args.clock_offset),args.time_scale)
            result={"evidence":e.model_dump(mode="json")}
            if args.analyze:
                from .pipeline import run_pipeline
                from .agents import run_agent
                result["analysis"]=analyze_media(db,e.evidence_id,args.sam_prompt)
                r=run_pipeline(settings,args.store)
                result["health"]=r["health"]
                result["health_agent"]=run_agent(db,args.store,"Review ML health after surveillance extraction.","health",settings.mode)
            show(result)
        elif args.command=="ask":
            from .agents import run_agent
            show(run_agent(db,args.store,args.question,args.role,args.mode or settings.mode))
        elif args.command=="health":
            from .monitor import monitor_once
            show(monitor_once(settings,args.store,args.agent,args.as_of))
        elif args.command=="watch":
            from .monitor import watch
            watch(settings,args.store,args.interval,args.agent)
        elif args.command=="evaluate":
            from .evaluation import evaluate_synthetic
            show(evaluate_synthetic(db,args.store))
        elif args.command=="doctor":
            from .meta_client import usage_summary
            show({"home":str(settings.home),"mode":settings.mode,"api_key_present":bool(settings.api_key),
                  "external_media_authorized":settings.external_media,"model":settings.muse_model,
                  "products":len(db.objects("products")),"api_usage":usage_summary(db)})
        else:
            from .meta_client import MetaClient,output_text
            with MetaClient(settings) as client:
                response=client.create_response({"model":settings.muse_model,"input":"Reply with the single word READY.","max_output_tokens":1000},"connectivity_smoke",cache=False)
                show({"response":output_text(response),"usage":response.get("usage")})
    except KeyboardInterrupt:
        print("Stopped.",file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise SystemExit(1) from exc


if __name__=="__main__":
    main()
