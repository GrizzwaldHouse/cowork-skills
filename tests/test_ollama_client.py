# test_ollama_client.py
# Developer: Marcus Daley
# Date: 2026-04-05
# Purpose: Unit tests for ollama_client.py (all HTTP calls mocked, no network requests)

"""
Unit tests for Ollama API client.

All HTTP calls are mocked using unittest.mock to prevent network requests.
Tests cover health checks, model detection, generation, chat, error handling,
and custom configuration.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError, URLError

# Add ClaudeSkills paths to sys.path
sys.path.insert(0, "C:/ClaudeSkills")
sys.path.insert(0, "C:/ClaudeSkills/scripts")

from ollama.ollama_client import (
    ChatMessage,
    ChatResult,
    GenerateResult,
    ModelInfo,
    OllamaAPIError,
    OllamaClient,
    OllamaConnectionError,
)


class TestOllamaClient(unittest.TestCase):
    """Test suite for OllamaClient."""

    def test_is_running_true(self):
        """Test is_running returns True when server responds with 200."""
        mock_response = Mock()
        mock_response.read.return_value = json.dumps({"models": []}).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            result = client.is_running()

        self.assertTrue(result)

    def test_is_running_false(self):
        """Test is_running returns False when URLError occurs."""
        with patch("urllib.request.urlopen", side_effect=URLError("Connection refused")):
            client = OllamaClient()
            result = client.is_running()

        self.assertFalse(result)

    def test_detect_models(self):
        """Test detect_models parses response with 2 models."""
        mock_response_data = {
            "models": [
                {
                    "name": "llama2:7b",
                    "size": 3826793677,
                    "modified_at": "2024-01-15T12:00:00Z",
                    "details": {
                        "parameter_size": "7B",
                        "quantization_level": "Q4_0",
                        "family": "llama",
                        "format": "gguf",
                    },
                },
                {
                    "name": "mistral:latest",
                    "size": 4109865159,
                    "modified_at": "2024-01-16T14:30:00Z",
                    "details": {
                        "parameter_size": "7B",
                        "quantization_level": "Q4_K_M",
                        "family": "mistral",
                        "format": "gguf",
                    },
                },
            ]
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            models = client.detect_models()

        self.assertEqual(len(models), 2)
        self.assertIsInstance(models[0], ModelInfo)
        self.assertEqual(models[0].name, "llama2:7b")
        self.assertEqual(models[0].parameter_count, "7B")
        self.assertEqual(models[1].name, "mistral:latest")

    def test_detect_models_empty(self):
        """Test detect_models returns empty list when no models installed."""
        mock_response_data = {"models": []}

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            models = client.detect_models()

        self.assertEqual(len(models), 0)

    def test_get_model_info(self):
        """Test get_model_info parses /api/show response."""
        mock_response_data = {
            "modelfile": {"name": "llama2:7b"},
            "modified_at": "2024-01-15T12:00:00Z",
            "details": {
                "size": 3826793677,
                "parameter_size": "7B",
                "quantization_level": "Q4_0",
                "family": "llama",
                "format": "gguf",
            },
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            info = client.get_model_info("llama2:7b")

        self.assertIsInstance(info, ModelInfo)
        self.assertEqual(info.name, "llama2:7b")
        self.assertEqual(info.parameter_count, "7B")
        self.assertEqual(info.quantization, "Q4_0")
        self.assertEqual(info.family, "llama")

    def test_generate(self):
        """Test generate parses /api/generate response with metrics."""
        mock_response_data = {
            "model": "llama2:7b",
            "response": "The capital of France is Paris.",
            "total_duration": 5000000000,  # 5 seconds in nanoseconds
            "eval_count": 20,
            "eval_duration": 1000000000,  # 1 second in nanoseconds
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            result = client.generate("llama2:7b", "What is the capital of France?")

        self.assertIsInstance(result, GenerateResult)
        self.assertEqual(result.response, "The capital of France is Paris.")
        self.assertEqual(result.model, "llama2:7b")
        self.assertEqual(result.eval_count, 20)
        self.assertEqual(result.eval_duration_ns, 1000000000)
        # tokens_per_second = 20 / (1000000000 / 1e9) = 20 / 1.0 = 20.0
        self.assertAlmostEqual(result.tokens_per_second, 20.0, places=1)

    def test_generate_with_options(self):
        """Test generate passes options dict correctly."""
        mock_response_data = {
            "model": "llama2:7b",
            "response": "Test response",
            "total_duration": 1000000000,
            "eval_count": 10,
            "eval_duration": 500000000,
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        captured_request = None

        def capture_request(req, timeout=None):
            nonlocal captured_request
            captured_request = req
            return mock_response

        with patch("urllib.request.urlopen", side_effect=capture_request):
            client = OllamaClient()
            options = {"temperature": 0.7, "top_p": 0.9}
            result = client.generate(
                "llama2:7b", "Test prompt", system="You are helpful", options=options
            )

        # Verify request body contains options
        request_body = json.loads(captured_request.data.decode("utf-8"))
        self.assertIn("options", request_body)
        self.assertEqual(request_body["options"]["temperature"], 0.7)
        self.assertEqual(request_body["options"]["top_p"], 0.9)
        self.assertEqual(request_body["system"], "You are helpful")

    def test_chat(self):
        """Test chat parses /api/chat response."""
        mock_response_data = {
            "model": "llama2:7b",
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?",
            },
            "total_duration": 3000000000,
            "eval_count": 15,
            "eval_duration": 750000000,
        }

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        with patch("urllib.request.urlopen", return_value=mock_response):
            client = OllamaClient()
            messages = [{"role": "user", "content": "Hello"}]
            result = client.chat("llama2:7b", messages)

        self.assertIsInstance(result, ChatResult)
        self.assertIsInstance(result.message, ChatMessage)
        self.assertEqual(result.message.role, "assistant")
        self.assertEqual(result.message.content, "Hello! How can I help you today?")
        self.assertEqual(result.eval_count, 15)
        # tokens_per_second = 15 / (750000000 / 1e9) = 15 / 0.75 = 20.0
        self.assertAlmostEqual(result.tokens_per_second, 20.0, places=1)

    def test_connection_error(self):
        """Test URLError raises OllamaConnectionError."""
        with patch("urllib.request.urlopen", side_effect=URLError("Connection refused")):
            client = OllamaClient()
            with self.assertRaises(OllamaConnectionError) as ctx:
                client.detect_models()

        self.assertIn("Failed to connect", str(ctx.exception))

    def test_api_error(self):
        """Test HTTPError raises OllamaAPIError with status code."""
        # Mock HTTPError with status 404
        mock_http_error = HTTPError(
            url="http://localhost:11434/api/show",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None,
        )
        mock_http_error.read = Mock(return_value=b'{"error": "model not found"}')

        with patch("urllib.request.urlopen", side_effect=mock_http_error):
            client = OllamaClient()
            with self.assertRaises(OllamaAPIError) as ctx:
                client.get_model_info("nonexistent:model")

        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("API error 404", str(ctx.exception))

    def test_custom_base_url(self):
        """Test non-default base URL is used in requests."""
        mock_response_data = {"models": []}

        mock_response = Mock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)

        captured_request = None

        def capture_request(req, timeout=None):
            nonlocal captured_request
            captured_request = req
            return mock_response

        custom_url = "http://192.168.1.100:11434"
        with patch("urllib.request.urlopen", side_effect=capture_request):
            client = OllamaClient(base_url=custom_url)
            client.detect_models()

        # Verify request was sent to custom URL
        self.assertTrue(captured_request.full_url.startswith(custom_url))


if __name__ == "__main__":
    unittest.main()
