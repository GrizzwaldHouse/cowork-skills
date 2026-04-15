# ollama_client.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: HTTP client for Ollama API using stdlib only (urllib.request, json)

"""
Ollama API client for local LLM inference.

Provides methods for model detection, generation, chat completion, and model
pulling. All HTTP requests use urllib.request (no external dependencies).
Designed for integration with the ClaudeSkills intelligence pipeline.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_SECONDS = 120
HEALTH_TIMEOUT_SECONDS = 5

# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class OllamaError(Exception):
    """Base exception for all Ollama client errors."""


class OllamaConnectionError(OllamaError):
    """Raised when connection to Ollama server fails."""


class OllamaAPIError(OllamaError):
    """Raised when Ollama API returns an error response."""

    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message


# ---------------------------------------------------------------------------
# Dataclasses (frozen for immutability)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelInfo:
    """Metadata for an Ollama model."""

    name: str
    size: int  # bytes
    parameter_count: str  # e.g. "7B"
    quantization: str
    modified_at: str
    family: str
    format_: str


@dataclass(frozen=True)
class GenerateResult:
    """Result from /api/generate endpoint."""

    response: str
    model: str
    total_duration_ns: int
    eval_count: int
    eval_duration_ns: int
    tokens_per_second: float


@dataclass(frozen=True)
class ChatMessage:
    """Single chat message (role + content)."""

    role: str
    content: str


@dataclass(frozen=True)
class ChatResult:
    """Result from /api/chat endpoint."""

    message: ChatMessage
    model: str
    total_duration_ns: int
    eval_count: int
    eval_duration_ns: int
    tokens_per_second: float


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class OllamaClient:
    """Client for interacting with Ollama API endpoints.

    All methods use urllib.request for HTTP communication. Supports health
    checks, model discovery, generation, chat, and model pulling.
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize Ollama client.

        Args:
            base_url: Ollama server URL (default: http://localhost:11434)
            timeout: Default request timeout in seconds (default: 120)
        """
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def is_running(self) -> bool:
        """Check if Ollama server is running and responsive.

        Returns:
            True if server responds to GET /api/tags, False otherwise.
        """
        try:
            self._request("GET", "/api/tags", timeout=HEALTH_TIMEOUT_SECONDS)
            return True
        except (OllamaConnectionError, OllamaAPIError):
            return False

    def detect_models(self) -> list[ModelInfo]:
        """Retrieve list of available models from Ollama server.

        Returns:
            List of ModelInfo objects for each installed model.

        Raises:
            OllamaConnectionError: If server is unreachable.
            OllamaAPIError: If API returns error response.
        """
        response = self._request("GET", "/api/tags")
        models_list = response.get("models", [])

        return [
            ModelInfo(
                name=m.get("name", ""),
                size=m.get("size", 0),
                parameter_count=m.get("details", {}).get("parameter_size", ""),
                quantization=m.get("details", {}).get("quantization_level", ""),
                modified_at=m.get("modified_at", ""),
                family=m.get("details", {}).get("family", ""),
                format_=m.get("details", {}).get("format", ""),
            )
            for m in models_list
        ]

    def get_model_info(self, name: str) -> ModelInfo:
        """Retrieve detailed information for a specific model.

        Args:
            name: Model name (e.g. "llama2:7b")

        Returns:
            ModelInfo object with model metadata.

        Raises:
            OllamaConnectionError: If server is unreachable.
            OllamaAPIError: If model not found or API error.
        """
        response = self._request("POST", "/api/show", data={"name": name})

        details = response.get("details", {})
        return ModelInfo(
            name=response.get("modelfile", {}).get("name", name),
            size=details.get("size", 0),
            parameter_count=details.get("parameter_size", ""),
            quantization=details.get("quantization_level", ""),
            modified_at=response.get("modified_at", ""),
            family=details.get("family", ""),
            format_=details.get("format", ""),
        )

    def generate(
        self,
        model: str,
        prompt: str,
        system: str = "",
        options: dict[str, Any] | None = None,
    ) -> GenerateResult:
        """Generate text completion from a prompt.

        Args:
            model: Model name (e.g. "llama2:7b")
            prompt: Input prompt text
            system: Optional system prompt
            options: Optional dict of model parameters (temperature, top_p, etc.)

        Returns:
            GenerateResult with response text and performance metrics.

        Raises:
            OllamaConnectionError: If server is unreachable.
            OllamaAPIError: If API returns error response.
        """
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }

        if system:
            payload["system"] = system

        if options:
            payload["options"] = options

        response = self._request("POST", "/api/generate", data=payload)

        total_duration = response.get("total_duration", 0)
        eval_count = response.get("eval_count", 0)
        eval_duration = response.get("eval_duration", 0)

        # Calculate tokens per second (avoid division by zero)
        tokens_per_second = 0.0
        if eval_duration > 0:
            tokens_per_second = eval_count / (eval_duration / 1e9)

        return GenerateResult(
            response=response.get("response", ""),
            model=response.get("model", model),
            total_duration_ns=total_duration,
            eval_count=eval_count,
            eval_duration_ns=eval_duration,
            tokens_per_second=tokens_per_second,
        )

    def chat(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any] | None = None,
    ) -> ChatResult:
        """Send chat messages and receive completion.

        Args:
            model: Model name (e.g. "llama2:7b")
            messages: List of message dicts with "role" and "content" keys
            options: Optional dict of model parameters

        Returns:
            ChatResult with assistant response and performance metrics.

        Raises:
            OllamaConnectionError: If server is unreachable.
            OllamaAPIError: If API returns error response.
        """
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

        if options:
            payload["options"] = options

        response = self._request("POST", "/api/chat", data=payload)

        total_duration = response.get("total_duration", 0)
        eval_count = response.get("eval_count", 0)
        eval_duration = response.get("eval_duration", 0)

        # Calculate tokens per second
        tokens_per_second = 0.0
        if eval_duration > 0:
            tokens_per_second = eval_count / (eval_duration / 1e9)

        message_dict = response.get("message", {})
        message = ChatMessage(
            role=message_dict.get("role", "assistant"),
            content=message_dict.get("content", ""),
        )

        return ChatResult(
            message=message,
            model=response.get("model", model),
            total_duration_ns=total_duration,
            eval_count=eval_count,
            eval_duration_ns=eval_duration,
            tokens_per_second=tokens_per_second,
        )

    def pull_model(self, name: str) -> bool:
        """Download a model from Ollama registry.

        Args:
            name: Model name (e.g. "llama2:7b")

        Returns:
            True if pull succeeded, False otherwise.

        Raises:
            OllamaConnectionError: If server is unreachable.
        """
        try:
            self._request("POST", "/api/pull", data={"name": name, "stream": False})
            return True
        except OllamaAPIError:
            return False

    # ------------------------------------------------------------------
    # Internal methods
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        endpoint: str,
        data: dict[str, Any] | None = None,
        timeout: int | None = None,
    ) -> dict[str, Any]:
        """Execute HTTP request to Ollama API.

        Args:
            method: HTTP method (GET, POST)
            endpoint: API endpoint path (e.g. "/api/tags")
            data: Optional JSON payload for POST requests
            timeout: Optional timeout override (uses self._timeout if None)

        Returns:
            Parsed JSON response as dict.

        Raises:
            OllamaConnectionError: If connection fails.
            OllamaAPIError: If API returns non-200 status.
        """
        url = f"{self._base_url}{endpoint}"
        request_timeout = timeout if timeout is not None else self._timeout

        # Build request
        headers = {"Content-Type": "application/json"} if data else {}
        body = json.dumps(data).encode("utf-8") if data else None

        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=request_timeout) as response:
                response_data = response.read().decode("utf-8")
                return json.loads(response_data)
        except urllib.error.HTTPError as exc:
            # HTTP error response (404, 500, etc.) - MUST come before URLError
            # because HTTPError is a subclass of URLError
            error_body = exc.read().decode("utf-8", errors="replace")
            raise OllamaAPIError(
                f"API error {exc.code}: {error_body}",
                status_code=exc.code,
            ) from exc
        except urllib.error.URLError as exc:
            # Connection error (server down, network issue, timeout)
            raise OllamaConnectionError(f"Failed to connect to {url}: {exc}") from exc
