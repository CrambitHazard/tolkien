import json
import os
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv


load_dotenv()


class OpenRouterClient:
    """LLM client for OpenRouter Chat Completions API.

    Uses model `deepseek/deepseek-chat-v3.1:free` by default.

    Args:
        api_key: Optional API key override. Falls back to env `OPENROUTER_API_KEY`.
        base_url: Optional base URL. Falls back to env `OPENROUTER_BASE_URL`.
        default_model: Optional model. Falls back to env `MODEL`.

    Raises:
        RuntimeError: When API returns an error or parsing fails.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        default_model: Optional[str] = None,
    ) -> None:
        self.api_key: Optional[str] = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url: str = base_url or os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1",
        )
        self.default_model: str = default_model or os.getenv(
            "MODEL", "deepseek/deepseek-chat-v3.1:free",
        )

    @property
    def is_configured(self) -> bool:
        """Whether an API key is available."""
        return bool(self.api_key)

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 1.0,
        max_tokens: int = 2000,
        model: Optional[str] = None,
        seed: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Send a chat completion request.

        Args:
            messages: OpenAI-format messages: [{"role": "system|user|assistant", "content": "..."}]
            temperature: Sampling temperature.
            max_tokens: Max tokens in the response.
            model: Override model name.
            seed: Optional reproducibility seed.
            response_format: Optional format hint, e.g. {"type": "json_object"}.

        Returns:
            The assistant text content.

        Raises:
            RuntimeError: On HTTP errors or malformed responses.
        """
        if not self.is_configured:
            raise RuntimeError(
                "OpenRouter API key missing. Set OPENROUTER_API_KEY in your environment.",
            )

        url = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if seed is not None:
            payload["seed"] = seed
        if response_format is not None:
            payload["response_format"] = response_format

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://local-agent",
            "X-Title": "3-Choice Chapter Writer",
            "Content-Type": "application/json",
        }

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code != 200:
            raise RuntimeError(
                f"OpenRouter error {response.status_code}: {response.text[:200]}",
            )

        data = response.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Malformed OpenRouter response: {json.dumps(data)[:400]}") from exc
        return text or ""


def get_client() -> OpenRouterClient:
    """Factory to get a configured OpenRouter client.

    Returns:
        Configured `OpenRouterClient`.
    """
    return OpenRouterClient()


def has_online_llm() -> bool:
    """Quick check if an API key is available for online generation."""
    return bool(os.getenv("OPENROUTER_API_KEY"))


