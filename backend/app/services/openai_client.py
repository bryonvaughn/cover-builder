import base64
from typing import Any
from openai import OpenAI
from app.settings import get_settings


class OpenAIClient:
    """
    - create_text(prompt) -> {"model": ..., "output_text": "..."}
    - generate_images(...) -> list[bytes] (PNG bytes)
    """

    def __init__(self) -> None:
        self.settings = get_settings()

        api_key = getattr(self.settings, "openai_api_key", None)
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY (openai_api_key) in settings")

        # Always create the SDK client
        self.client = OpenAI(api_key=api_key)

        # Belt-and-suspenders: if something weird happened, fail NOW (not later)
        if self.client is None:
            raise RuntimeError(
                "OpenAI SDK client is None after initialization. "
                "This suggests your OpenAI import or instantiation is being shadowed."
            )

        self.text_model = getattr(self.settings, "text_model", None) or "gpt-4.1-mini"
        self.image_model = getattr(self.settings, "image_model", None) or "gpt-image-1.5"
        self.image_size = getattr(self.settings, "image_size", None) or "1024x1536"

    def create_text(self, *, prompt: str, model: str | None = None) -> dict[str, Any]:
        if self.client is None:
            raise RuntimeError("OpenAI client is not initialized (self.client is None)")

        use_model = model or self.text_model
        resp = self.client.responses.create(
            model=use_model,
            input=prompt,
        )
        output_text = getattr(resp, "output_text", "") or ""
        return {"model": use_model, "output_text": output_text}

    def generate_images(
        self,
        *,
        prompt: str,
        n: int = 1,
        model: str | None = None,
        size: str | None = None,
    ) -> list[bytes]:
        if self.client is None:
            raise RuntimeError("OpenAI client is not initialized (self.client is None)")

        use_model = model or self.image_model
        use_size = size or self.image_size

        img = self.client.images.generate(
            model=use_model,
            prompt=prompt,
            size=use_size,
            n=n,
        )

        out: list[bytes] = []
        for item in img.data:
            b64 = getattr(item, "b64_json", None)
            if b64:
                out.append(base64.b64decode(b64))
                continue

            url = getattr(item, "url", None)
            if url:
                raise RuntimeError(
                    "OpenAI returned image URLs instead of base64. "
                    "Adjust the images.generate call to request base64 output for your SDK version."
                )

            raise RuntimeError("OpenAI returned an image item with no b64_json or url")

        return out
