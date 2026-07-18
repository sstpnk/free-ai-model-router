"""Shared HTTP client with retry, rate limiting, caching, and security."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.parse import urlparse

import httpx

logger = logging.getLogger(__name__)

USER_AGENT = "FreeAIModelRouter/0.1 (+https://github.com/sstpnk/free-ai-model-router)"


class HttpClient:
    """Async HTTP client with retry, ETag caching, rate limiting, and SSRF protection."""

    def __init__(
        self,
        cache_dir: Path,
        allowed_domains: Optional[list[str]] = None,
        default_timeout: float = 30.0,
        max_retries: int = 3,
        rate_per_second: float = 10.0,
    ) -> None:
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.allowed_domains = allowed_domains
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(default_timeout),
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
        )
        self._etag_store: dict[str, str] = {}
        self._last_modified_store: dict[str, str] = {}

    async def close(self) -> None:
        await self._client.aclose()

    def _validate_url(self, url: str) -> None:
        """SSRF protection: reject requests to unexpected domains."""
        if not self.allowed_domains:
            return
        parsed = urlparse(url)
        if parsed.hostname is None:
            raise ValueError(f"Cannot parse hostname from URL: {url}")
        if not any(parsed.hostname == d or parsed.hostname.endswith("." + d) for d in self.allowed_domains):
            raise ValueError(f"Domain {parsed.hostname} not in allowed list")

    def _cache_path(self, url: str, params_hash: str = "") -> Path:
        raw = f"{url}:::{params_hash}"
        key = hashlib.sha256(raw.encode()).hexdigest()[:32]
        return self.cache_dir / f"{key}.json"

    def _read_cache(self, url: str, params_hash: str = "") -> Optional[dict[str, Any]]:
        path = self._cache_path(url, params_hash)
        if not path.exists():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # check if cache has expired
            return data
        except (json.JSONDecodeError, OSError):
            return None

    def _write_cache(self, url: str, data: dict[str, Any], params_hash: str = "") -> None:
        path = self._cache_path(url, params_hash)
        try:
            path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except OSError:
            logger.warning("Failed to write cache for %s", url)

    async def fetch_json(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        params: Optional[dict[str, Any]] = None,
        auth_header: Optional[str] = None,
        auth_token: Optional[str] = None,
        use_cache: bool = True,
        cache_ttl_seconds: int = 7200,
    ) -> dict[str, Any]:
        """Fetch JSON from URL with caching, retries, and conditional requests."""
        self._validate_url(url)
        params_hash = hashlib.md5(json.dumps(params or {}, sort_keys=True).encode()).hexdigest()[:16] if params else ""

        # Check cache
        if use_cache:
            cached = self._read_cache(url, params_hash)
            if cached:
                age_seconds = (datetime.now(timezone.utc) - datetime.fromisoformat(cached.get("_fetched_at", "2000-01-01T00:00:00+00:00"))).total_seconds()
                if age_seconds < cache_ttl_seconds:
                    return cached["data"]

        # Build request headers
        request_headers = dict(headers or {})
        if auth_token and auth_header:
            request_headers[auth_header] = auth_token

        # Add conditional headers from cache
        if url in self._etag_store:
            request_headers["If-None-Match"] = self._etag_store[url]
        if url in self._last_modified_store:
            request_headers["If-Modified-Since"] = self._last_modified_store[url]

        # Retry loop
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                response = await self._client.get(url, headers=request_headers, params=params)

                if response.status_code == 304:
                    # Not Modified — return cached version
                    cached = self._read_cache(url, params_hash)
                    if cached:
                        return cached["data"]

                response.raise_for_status()

                # Store ETag / Last-Modified
                if "etag" in response.headers:
                    self._etag_store[url] = response.headers["etag"]
                if "last-modified" in response.headers:
                    self._last_modified_store[url] = response.headers["last-modified"]

                data = response.json()

                # Validate domain-allowed response
                if not isinstance(data, dict):
                    data = {"data": data}

                # Write cache
                if use_cache:
                    self._write_cache(url, {
                        "_fetched_at": datetime.now(timezone.utc).isoformat(),
                        "_url": url,
                        "data": data,
                    }, params_hash)

                return data

            except httpx.HTTPStatusError as e:
                last_error = e
                logger.warning("HTTP %s for %s (attempt %d/%d)", e.response.status_code, url, attempt + 1, self.max_retries)
                if e.response.status_code in (401, 403, 404):
                    break  # Don't retry auth / not-found errors
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                logger.warning("Network error for %s (attempt %d/%d): %s", url, attempt + 1, self.max_retries, e)
                if attempt < self.max_retries - 1:
                    import asyncio
                    wait = 2 ** attempt
                    logger.info("Retrying in %ds...", wait)
                    await asyncio.sleep(wait)

        raise RuntimeError(f"Failed to fetch {url} after {self.max_retries} attempts") from last_error

    async def fetch_text(
        self,
        url: str,
        *,
        headers: Optional[dict[str, str]] = None,
        auth_header: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> str:
        """Fetch raw text from URL."""
        self._validate_url(url)
        request_headers = dict(headers or {})
        if auth_token and auth_header:
            request_headers[auth_header] = auth_token

        response = await self._client.get(url, headers=request_headers)
        response.raise_for_status()
        return response.text

    async def post_json(
        self,
        url: str,
        json_data: dict[str, Any],
        *,
        headers: Optional[dict[str, str]] = None,
        auth_header: Optional[str] = None,
        auth_token: Optional[str] = None,
    ) -> dict[str, Any]:
        """POST JSON and return parsed response."""
        self._validate_url(url)
        request_headers = dict(headers or {"Content-Type": "application/json"})
        if auth_token and auth_header:
            request_headers[auth_header] = auth_token

        response = await self._client.post(url, headers=request_headers, json=json_data)
        response.raise_for_status()
        return response.json()
