from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from storyos.llm.base import ProviderError


class OpenAIProvider:
    name = "openai"

    def __init__(self, settings: dict[str, Any] | None = None) -> None:
        settings = settings or {}
        self.model = str(settings.get("model") or "gpt-4o-mini")
        self.api_key = str(settings.get("api_key") or os.environ.get("OPENAI_API_KEY") or "")
        self.timeout_seconds = int(settings.get("timeout_seconds", 120))
        self.base_url = str(settings.get("base_url") or "https://api.openai.com/v1").rstrip("/")

    def is_available(self) -> bool:
        return bool(self.api_key and not self.api_key.startswith("${"))

    def availability_hint(self) -> str:
        if self.is_available():
            return f"OpenAI model `{self.model}` configured."
        return "Set OPENAI_API_KEY or [openai].api_key in storyos.toml."

    def generate(self, prompt: str) -> str:
        if not self.is_available():
            raise ProviderError(self.availability_hint())

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ProviderError(f"OpenAI API failed ({exc.code}): {detail}") from exc
        except urllib.error.URLError as exc:
            raise ProviderError(f"OpenAI API request failed: {exc.reason}") from exc

        try:
            content = body["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError("OpenAI API returned an unexpected response.") from exc

        text = str(content).strip()
        if not text:
            raise ProviderError("OpenAI API returned empty output.")
        return text
