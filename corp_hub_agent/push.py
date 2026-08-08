"""HTTP push helper: POST JSON to backend with retry + backoff."""
from __future__ import annotations
import logging
import time

import httpx

from .auth import auth_header

log = logging.getLogger("corp_hub_agent")

MAX_RETRIES = 3
BACKOFF_SECONDS = [2, 5, 15]


def push(
    backend_url: str,
    token: str,
    path: str,
    payload: dict,
    timeout: float = 10.0,
) -> bool:
    """POST payload to backend_path. Retries transient failures (5xx/network).

    Returns True on success (2xx), False on terminal 4xx or retries exhausted.
    """
    url = backend_url.rstrip("/") + path
    headers = {"Content-Type": "application/json", **auth_header(token)}
    last_error = ""

    for attempt in range(MAX_RETRIES):
        try:
            resp = httpx.post(url, json=payload, headers=headers, timeout=timeout)
            if resp.status_code < 300:
                return True
            if 400 <= resp.status_code < 500:
                # Terminal — bad token, unknown host, invalid payload. Don't retry.
                log.error("push %s: terminal %s %s", path, resp.status_code, resp.text[:200])
                return False
            last_error = f"HTTP {resp.status_code}: {resp.text[:120]}"
        except httpx.HTTPError as e:
            last_error = f"network error: {e}"

        if attempt < MAX_RETRIES - 1:
            sleep_s = BACKOFF_SECONDS[min(attempt, len(BACKOFF_SECONDS) - 1)]
            log.warning("push %s: %s — retry in %ss", path, last_error, sleep_s)
            time.sleep(sleep_s)

    log.error("push %s: failed after %d retries: %s", path, MAX_RETRIES, last_error)
    return False
