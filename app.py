import os
from typing import Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

APP = FastAPI(title="OpenCode Python Proxy for Colab")

SERVER_KEY = os.getenv("SERVER_KEY", "change-me-local-key")
UPSTREAM_BASE = os.getenv("UPSTREAM_BASE", "https://opencode.ai/zen").rstrip("/")
UPSTREAM_API_KEY = os.getenv("UPSTREAM_API_KEY", "").strip()
UPSTREAM_MODEL = os.getenv("UPSTREAM_MODEL", "gpt-4o-mini")


def require_local_key(auth: Optional[str], x_api_key: Optional[str]):
    incoming = auth or x_api_key
    if not incoming:
        raise HTTPException(status_code=401, detail="missing local API key")

    token = incoming.replace("Bearer ", "", 1) if incoming.startswith("Bearer ") else incoming
    if token != SERVER_KEY:
        raise HTTPException(status_code=401, detail="invalid local API key")


def build_upstream_headers(auth: Optional[str], x_api_key: Optional[str]):
    headers = {"Content-Type": "application/json"}
    if UPSTREAM_API_KEY:
        headers["Authorization"] = f"Bearer {UPSTREAM_API_KEY}"
    elif auth:
        headers["Authorization"] = auth
    elif x_api_key:
        headers["x-api-key"] = x_api_key
    return headers


async def proxy_json(path: str, method: str, body: dict, auth: Optional[str], x_api_key: Optional[str]):
    upstream_url = f"{UPSTREAM_BASE}{path}"
    headers = build_upstream_headers(auth, x_api_key)

    async with httpx.AsyncClient(timeout=180.0) as client:
        resp = await client.request(method, upstream_url, headers=headers, json=body)
        try:
            data = resp.json()
        except Exception:
            data = {"raw_text": resp.text}
        return JSONResponse(content=data, status_code=resp.status_code)


@APP.get("/healthz")
async def healthz():
    return {"ok": True, "upstream_base": UPSTREAM_BASE}


@APP.get("/v1/models")
async def models(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    require_local_key(authorization, x_api_key)

    headers = build_upstream_headers(authorization, x_api_key)
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{UPSTREAM_BASE}/v1/models", headers=headers)
            if r.status_code == 200:
                try:
                    data = r.json()
                    return JSONResponse(content=data, status_code=200)
                except Exception:
                    pass
    except Exception:
        pass

    return {
        "object": "list",
        "data": [
            {"id": UPSTREAM_MODEL, "object": "model", "created": 0, "owned_by": "colab-proxy"},
            {"id": "gpt-4o-mini", "object": "model", "created": 0, "owned_by": "colab-proxy"},
            {"id": "claude-3-5-sonnet", "object": "model", "created": 0, "owned_by": "colab-proxy"},
        ],
    }


@APP.post("/v1/chat/completions")
async def chat_completions(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    require_local_key(authorization, x_api_key)
    payload = await request.json()
    return await proxy_json("/v1/chat/completions", "POST", payload, authorization, x_api_key)


@APP.post("/v1/responses")
async def responses(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
):
    require_local_key(authorization, x_api_key)
    payload = await request.json()
    return await proxy_json("/v1/responses", "POST", payload, authorization, x_api_key)


@APP.post("/v1/messages")
async def messages(
    request: Request,
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_api_key: Optional[str] = Header(None, alias="x-api-key"),
    anthropic_version: Optional[str] = Header(None, alias="anthropic-version"),
):
    require_local_key(authorization, x_api_key)
    payload = await request.json()
    return await proxy_json("/v1/messages", "POST", payload, authorization, x_api_key)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:APP", host="0.0.0.0", port=8000, reload=False)
