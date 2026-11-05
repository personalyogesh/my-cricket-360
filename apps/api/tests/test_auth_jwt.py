"""Token failure cases and a real RS256 verification against a local JWKS."""

from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from api.auth import _jwks_clients
from api.config import get_settings
from tests.helpers import auth_header


def test_expired_and_garbage_tokens_are_rejected(client) -> None:
    from api.auth import create_dev_access_token

    expired = create_dev_access_token(user_id=uuid.uuid4(), email="old@example.com", expires_in=-10)
    assert client.get("/v1/me", headers=auth_header(expired)).status_code == 401
    assert client.get("/v1/me", headers=auth_header("not-a-jwt")).status_code == 401


def test_supabase_jwks_verifies_rs256_and_rejects_bad_claims(client, monkeypatch) -> None:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(key.public_key()))
    jwk.update({"kid": "test-key", "use": "sig", "alg": "RS256"})
    body = json.dumps({"keys": [jwk]}).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, fmt: str, *args) -> None:
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    port = server.server_address[1]
    issuer = "http://local.supabase.auth/auth/v1"
    try:
        monkeypatch.setenv("MC360_AUTH_MODE", "supabase")
        monkeypatch.setenv("SUPABASE_JWKS_URL", f"http://127.0.0.1:{port}/.well-known/jwks.json")
        get_settings.cache_clear()
        _jwks_clients.clear()

        user_id = uuid.uuid4()
        token = jwt.encode(
            {
                "sub": str(user_id),
                "email": "jwks@example.com",
                "aud": "authenticated",
                "iss": issuer,
                "exp": int(time.time()) + 300,
            },
            key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )
        ok = client.get("/v1/me", headers=auth_header(token))
        assert ok.status_code == 200, ok.text
        assert ok.json()["user"]["email"] == "jwks@example.com"
        assert ok.json()["user"]["id"] == str(user_id)

        wrong_aud = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "email": "nope@example.com",
                "aud": "anon",
                "iss": issuer,
                "exp": int(time.time()) + 300,
            },
            key,
            algorithm="RS256",
            headers={"kid": "test-key"},
        )
        _jwks_clients.clear()
        assert client.get("/v1/me", headers=auth_header(wrong_aud)).status_code == 401

        dev_token = jwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "email": "dev@example.com",
                "aud": "authenticated",
                "iss": issuer,
                "exp": int(time.time()) + 300,
            },
            "test-secret-not-for-prod-32chars!!",
            algorithm="HS256",
        )
        assert client.get("/v1/me", headers=auth_header(dev_token)).status_code == 401
    finally:
        server.shutdown()
        get_settings.cache_clear()
        _jwks_clients.clear()
