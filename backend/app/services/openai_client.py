import logging
from typing import Any, Optional
import base64
from openai import OpenAI

from app.settings import get_settings

logger = logging.getLogger(__name__)


class OpenAIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._client = OpenAI(api_key=settings.openai_api_key)
        self._text_model = settings.openai_text_model

    def create_text(self, *, prompt: str, model: Optional[str] = None) -> dict[str, Any]:
        use_model = model or self._text_model

        resp = self._client.responses.create(
            model=use_model,
            input=prompt,
        )

        usage = getattr(resp, "usage", None)
        if usage:
            logger.info(
                "OpenAI usage model=%s input_tokens=%s output_tokens=%s",
                use_model,
                getattr(usage, "input_tokens", None),
                getattr(usage, "output_tokens", None),
            )

        output_text = getattr(resp, "output_text", None)
        if callable(output_text):
            output_text = output_text()

        return {"model": use_model, "output_text": output_text, "raw": resp}

    def generate_images(self, *, prompt: str, n: int, model: str, size: str) -> list[bytes]:
        """
        Returns list of image bytes (PNG/JPEG/WEBP depending on model/output_format).
        For GPT image models, the API returns base64 data which we decode. :contentReference[oaicite:1]{index=1}
        """
        img = self.client.images.generate(
            model=model,
            prompt=prompt,
            n=n,
            size=size,
        )

        out: list[bytes] = []
        for item in img.data:
            # GPT image models return b64_json
            out.append(base64.b64decode(item.b64_json))
        return out