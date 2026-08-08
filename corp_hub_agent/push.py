"""HTTP POST helper with exponential backoff retry for transient network errors."""
from __future__ import annotations
import logging
import time

import httpx

from .auth import auth_header

log = logging.getLogger("corp_hub_agent")


def push(
    backend_url: str,
    token: str,
    path: str,
    payload: dict,
    timeout: float = 10.0,
    max_retries: int = 3,
) -> dict:
    """POST payload to backend_url + path with X-Agent-Token header and retries."""
    url = backend_url.rstrip("/") + path
    headers = {
        "Content-Type": "application/json",
        **auth_header(token),
    }

    attempt = 0
    backoff = 1.0

    while True:
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except (httpx.ConnectError, httpx.TimeoutException, httpx.HTTPStatusError) as e:
            attempt += 1
            status_code = getattr(getattr(e, "response", None), "status_code", None)
            
            # Non-transient errors (401, 403, 400) fail fast
            if status_code in (400, 401, 403, 404):
                log.error("Permanent HTTP error %s for %s: %s", status_code, path, e)
                raise

            if attempt >= max_retries:
                log.error("Failed to push to %s after %d attempts: %s", path, max_retries, e)
                raise

            log.warning("Push to %s failed (attempt %d/%d): %s. Retrying in %.1fs...", path, attempt, max_retries, e, backoff)
            time.sleep(backoff)
            backoff *= 2.0
