import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from llm.errors import LLMConfigurationError, LLMResponseError, LLMTimeoutError
from llm.openai_client import call_openai


def build_response(content: str):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content=content),
            )
        ]
    )


class OpenAIClientTests(unittest.TestCase):
    @patch("llm.openai_client.time.sleep", return_value=None)
    @patch("llm.openai_client._get_client")
    def test_call_openai_retries_transient_failure_then_succeeds(self, mock_get_client, _mock_sleep):
        client = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=Mock(return_value=build_response("ok")))
            )
        )
        mock_get_client.side_effect = [LLMTimeoutError("temporary issue"), client]

        result = call_openai("system", "user", request_id="req-1")

        self.assertEqual(result, "ok")
        self.assertEqual(mock_get_client.call_count, 2)

    @patch("llm.openai_client._get_client")
    def test_call_openai_does_not_retry_configuration_errors(self, mock_get_client):
        mock_get_client.side_effect = LLMConfigurationError("missing key")

        with self.assertRaises(LLMConfigurationError):
            call_openai("system", "user", request_id="req-2")

        self.assertEqual(mock_get_client.call_count, 1)

    @patch("llm.openai_client._get_client")
    def test_call_openai_raises_typed_response_error_for_empty_content(self, mock_get_client):
        create = Mock(return_value=build_response(""))
        mock_get_client.return_value = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create)
            )
        )

        with self.assertRaises(LLMResponseError):
            call_openai("system", "user", request_id="req-3")

        self.assertEqual(create.call_count, 1)


if __name__ == "__main__":
    unittest.main()
