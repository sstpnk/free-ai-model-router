"""Hugging Face Hub collector — model discovery and metadata."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from free_ai_model_router.http_client.client import HttpClient
from free_ai_model_router.models import (
    CanonicalModel,
    Capabilities,
)

logger = logging.getLogger(__name__)

HF_API_BASE = "https://huggingface.co/api"
HF_MODELS_SEARCH_URL = f"{HF_API_BASE}/models"
HF_INFERENCE_PROVIDERS_URL = f"{HF_API_BASE}/inference-providers"

# Tags that indicate coding relevance
CODING_TAGS = {"code", "coding", "agents", "agent", "tool-use", "tool_use", "code-generation", "code generation"}
TEXT_GENERATION_TAGS = {"text-generation", "text generation"}
RELEVANT_TAGS = CODING_TAGS | TEXT_GENERATION_TAGS


class HuggingFaceCollector:
    """Collector for Hugging Face model discovery."""

    def __init__(self, http_client: HttpClient) -> None:
        self.http = http_client

    async def discover_coding_models(
        self,
        limit: int = 50,
        sort_by: str = "likes",
    ) -> list[dict[str, Any]]:
        """Discover models relevant for coding agents from Hugging Face Hub."""
        params: dict[str, Any] = {
            "sort": sort_by,
            "direction": -1,
            "limit": min(limit, 100),
            "full": "false",
            "config": "false",
        }

        data = await self.http.fetch_json(
            HF_MODELS_SEARCH_URL,
            params=params,
            use_cache=True,
            cache_ttl_seconds=7200,
        )

        models_list = data if isinstance(data, list) else data.get("data", [])
        results: list[dict[str, Any]] = []

        for m in models_list:
            tags = m.get("tags", [])
            pipeline_tag = m.get("pipeline_tag", "")

            # Check if model is text-generation or coding-relevant
            tag_set = set(tag.lower().replace("-", " ") for tag in tags)
            tag_set.add(pipeline_tag.lower())

            if not RELEVANT_TAGS.intersection(tag_set):
                continue

            results.append({
                "id": m.get("id", ""),
                "modelId": m.get("modelId", m.get("id", "")),
                "pipeline_tag": pipeline_tag,
                "tags": tags,
                "likes": m.get("likes", 0),
                "downloads": m.get("downloads", 0),
                "updated_at": m.get("lastModified", m.get("updatedAt")),
                "author": m.get("author", m.get("modelId", "").split("/")[0] if "/" in (m.get("id", "") or "") else ""),
                "private": m.get("private", False),
                "gated": m.get("gated", False),
                "siblings": m.get("siblings", []),
            })

        return results

    async def discover_inference_providers(self) -> list[dict[str, Any]]:
        """Discover inference providers that host models."""
        try:
            data = await self.http.fetch_json(
                HF_INFERENCE_PROVIDERS_URL,
                use_cache=True,
                cache_ttl_seconds=14400,
            )
            providers = data if isinstance(data, list) else data.get("providers", data.get("data", []))
            return providers
        except Exception as e:
            logger.warning("Failed to fetch HF inference providers: %s", e)
            return []

    def hf_model_to_canonical(self, hf_data: dict[str, Any]) -> Optional[CanonicalModel]:
        """Convert a HF model entry to a canonical model definition."""
        model_id = hf_data.get("id", hf_data.get("modelId", ""))
        if not model_id:
            return None

        tags = [t.lower() for t in hf_data.get("tags", [])]
        pipeline_tag = hf_data.get("pipeline_tag", "").lower()

        capabilities = Capabilities(
            coding=any(c in tags for c in ["code", "coding", "code-generation"]),
            tool_calling="tool-use" in tags or "tool_use" in tags,
            reasoning="reasoning" in tags or "reason" in tags,
        )

        return CanonicalModel(
            canonical_model_id=f"hf/{model_id}",
            name=model_id.split("/")[-1] if "/" in model_id else model_id,
            creator=hf_data.get("author", model_id.split("/")[0] if "/" in model_id else None),
            release_date=datetime.fromisoformat(hf_data["updated_at"].replace("Z", "+00:00")) if hf_data.get("updated_at") else None,
            model_family=model_id.split("/")[0] if "/" in model_id else None,
            open_weights=not hf_data.get("gated", False) and not hf_data.get("private", False),
            capabilities=capabilities,
        )

    def get_attribution(self) -> str:
        return "Data from Hugging Face Hub (https://huggingface.co)"
