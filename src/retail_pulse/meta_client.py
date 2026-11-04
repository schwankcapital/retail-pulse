from __future__ import annotations

import hashlib
import json
import time
import uuid
from pathlib import Path

import httpx

from .config import Settings
from .db import Database, dumps, utcnow


class MetaError(RuntimeError):
    pass


class BudgetExceeded(MetaError):
    pass


def output_text(response: dict) -> str:
    return "\n".join(c["text"] for item in response.get("output",[]) if item.get("type")=="message"
                     for c in item.get("content",[]) if c.get("type")=="output_text")


class MetaClient:
    """Native HTTP adapter for Meta Responses/Files APIs; no dependency on a competing SDK.

    Failed/ambiguous paid requests are never silently replayed. 429 is the only
    automatically retried status. The local budget is an estimate, not a billing cap.
    """
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None=None):
        if settings.mode!="meta":
            raise MetaError("Set RETAIL_PULSE_MODE=meta explicitly to enable paid calls")
        if not settings.api_key:
            raise MetaError("MODEL_API_KEY is empty; offline demo does not require a key")
        self.settings=settings
        self.db=Database(settings)
        self.http=httpx.Client(base_url=settings.base_url+"/",timeout=httpx.Timeout(settings.timeout,connect=15),
                               headers={"Authorization":f"Bearer {settings.api_key}"},transport=transport,
                               follow_redirects=False)

    def close(self):
        self.http.close()

    def __enter__(self):
        return self

    def __exit__(self,*args):
        self.close()

    def reserve(self,purpose: str,model: str,amount: float) -> str:
        rid=uuid.uuid4().hex
        with self.db.connect(write=True) as c:
            spent=c.execute("SELECT COALESCE(SUM(COALESCE(actual,reserved)),0) FROM usage").fetchone()[0]
            cap=min(self.settings.budget,60.0)
            if spent+amount>cap:
                raise BudgetExceeded(f"Local API budget guard: ${spent:.2f} used/reserved; ${amount:.2f} requested; cap ${cap:.2f}")
            c.execute("INSERT INTO usage VALUES(?,?,?,?,?,?,?,?)",
                      (rid,utcnow(),purpose,model,amount,None,"pending","{}"))
        return rid

    def settle(self,rid:str,cost:float|None,status:str,detail:dict):
        with self.db.connect(write=True) as c:
            c.execute("UPDATE usage SET actual=?,status=?,data=? WHERE id=?",(cost,status,dumps(detail),rid))

    def create_response(self,payload:dict,purpose:str,unit_cost:float|None=None,cache:bool=True) -> dict:
        body=dict(payload)
        body["store"]=False
        body["stream"]=False
        if body["model"]!=self.settings.sam_model:
            body.setdefault("max_output_tokens",self.settings.max_tokens)
            body.setdefault("reasoning",{"effort":"medium"})
            body.setdefault("include",["reasoning.encrypted_content"])
        digest=hashlib.sha256(dumps(body).encode()).hexdigest()
        path=self.settings.home/"cache"/f"{digest}.json"
        if cache and path.exists():
            data=json.loads(path.read_text(encoding="utf-8"))
            data["_retail_pulse_cache_hit"]=True
            return data
        # Spark context ceiling: reserve all 1,048,576 tokens at the uncached rate,
        # plus the requested output cap. Unknown charges retain the reservation.
        output_cap=int(body.get('max_output_tokens',self.settings.max_tokens))
        reserve=max(self.settings.reservation,unit_cost or 0,
                    (1_048_576*self.settings.input_price+output_cap*self.settings.output_price)/1e6 if unit_cost is None else 0)
        rid=self.reserve(purpose,body["model"],reserve)
        try:
            response=None
            for attempt in range(3):
                response=self.http.post("responses",json=body)
                if response.status_code!=429 or attempt==2:
                    break
                raw=response.headers.get("retry-after","1")
                try:
                    delay=min(10,max(1,float(raw)))
                except ValueError:
                    delay=2**attempt
                time.sleep(delay)
            if response.status_code>=400:
                # Client rejections are not billed by this estimate; ambiguous server failures retain reserve.
                self.settle(rid,0.0 if response.status_code<500 else None,"rejected" if response.status_code<500 else "uncertain",
                            {"http_status":response.status_code,"request_id":response.headers.get("x-request-id")})
                raise MetaError(f"Meta HTTP {response.status_code}; request {response.headers.get('x-request-id','unknown')}. Check model access, schema and account limits.")
            data=response.json()
            usage=data.get("usage") or {}
            if unit_cost is not None:
                cost=unit_cost
            elif "input_tokens" in usage and "output_tokens" in usage:
                inp=int(usage["input_tokens"]); out=int(usage["output_tokens"])
                cached=min(inp,int((usage.get("input_tokens_details") or {}).get("cached_tokens",0)))
                cost=((inp-cached)*self.settings.input_price+cached*self.settings.cache_price+out*self.settings.output_price)/1e6
            else:
                cost=None  # No usage report: retain conservative reservation, never report zero spend.
            self.settle(rid,cost,"completed" if data.get("status")=="completed" else "incomplete",
                        {"usage":usage,"response_id":data.get("id"),"estimated_cost":cost})
            if data.get("status") not in {None,"completed"}:
                raise MetaError("Meta response did not complete; increase token budget only after reviewing limits")
            if cache:
                temporary=path.with_suffix(f".{uuid.uuid4().hex}.tmp")
                temporary.write_text(dumps(data),encoding="utf-8")
                temporary.replace(path)
            return data
        except httpx.ConnectError as exc:
            self.settle(rid,0.0,"connection_failed",{})
            raise MetaError("Could not connect to Meta; request not automatically retried") from exc
        except (httpx.TimeoutException,httpx.ReadError) as exc:
            self.settle(rid,None,"uncertain",{"reason":"Network interruption; request may have been billed"})
            raise MetaError("Meta request interrupted. Reservation retained; inspect provider usage before retrying") from exc
        except (ValueError,KeyError) as exc:
            self.settle(rid,None,"invalid_response",{})
            raise MetaError("Invalid Meta response; reservation retained") from exc

    def upload(self,path:Path) -> str:
        if not self.settings.external_media:
            raise MetaError("ALLOW_EXTERNAL_MEDIA=true is required for authorized media uploads")
        with path.open("rb") as f:
            r=self.http.post("files",data={"purpose":"user_data","expires_after[anchor]":"created_at",
                                          "expires_after[seconds]":"86400"},
                             files={"file":(path.name,f,"application/octet-stream")})
        if r.status_code>=400:
            raise MetaError(f"Meta media upload rejected: HTTP {r.status_code}")
        file_id=r.json().get("id")
        if not isinstance(file_id,str) or not file_id.startswith("file"):
            raise MetaError("Upload response has no file ID")
        return file_id

    def delete_file(self,file_id:str) -> bool:
        # Best effort cleanup; caller records failure. No model-usage charge is claimed here.
        try:
            r=self.http.delete(f"files/{file_id}")
            return r.status_code in {200,204,404}
        except httpx.HTTPError:
            return False


def usage_summary(db:Database) -> dict:
    rows=db.rows("SELECT purpose,model,status,reserved,actual,at FROM usage ORDER BY at DESC")
    return {"estimated_spend_or_reserve":round(sum(r["actual"] if r["actual"] is not None else r["reserved"] for r in rows),6),
            "budget":min(db.settings.budget,60.0),"requests":len(rows),"recent":rows[:20],
            "notice":"Local estimates, including ambiguous-request reservations; verify actual charges in Meta's dashboard."}
