"""Bearer-token auth shared by the HTTP gateway and WebSockets."""
from __future__ import annotations

import hmac

from fastapi import HTTPException, Request, WebSocket

from ..security.env_secret import get_or_create_secret

API_TOKEN = get_or_create_secret("MYHOME_API_TOKEN", nbytes=32)


def _token_from_headers(headers) -> str | None:
    auth = headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:]
    return None


def token_ok(token: str | None) -> bool:
    return bool(token) and hmac.compare_digest(token, API_TOKEN)


def require_api_token(request: Request) -> None:
    if not token_ok(_token_from_headers(request.headers)):
        raise HTTPException(status_code=401, detail="unauthorized")


def websocket_authorized(ws: WebSocket) -> bool:
    token = ws.query_params.get("token") or _token_from_headers(ws.headers)
    if token_ok(token):
        return True
    from .authz import verify_member_token

    return verify_member_token(token) is not None
