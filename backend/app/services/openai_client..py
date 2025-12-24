import logging
from typing import Any, Optional

from openai import OpenAI

from app.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    """
    Small wrapper around the OpenAI Python SDK.
    Keeps OpenAI usage in one place so you can add:
      - cost tracking
      - retries/backoff
      - request IDs
      - standardized prompts
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._text_model = settings.openai_text_model

    @property
    def text_model(self) -> str:
        return self._text_model

    def create_text(self, *, prompt: str, model: Optional[str] = None) -> dict[str, Any]:
        use_model = model or self._text_model

        resp = self._client.responses.create(
            model=use_model,
            input=prompt,
        )

        # Best-effort usage logging (fields may vary by model)
        usage = getattr(resp, "usage", None)
        if usage:
            logger.info(
                "OpenAI usage model=%s input_tokens=%s output_tokens=%s",
                use_model,
                getattr(usage, "input_tokens", None),
                getattr(usage, "output_tokens", None),
            )

        # The SDK examples use response.output_text
        # (it may be a property; keep it flexible)
        output_text = getattr(resp, "output_text", None)
        if callable(output_text):
            output_text = output_text()

        return {
            "model": use_model,
            "output_text": output_text,
            "raw": resp,
        }
