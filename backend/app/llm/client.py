import asyncio
import json

import httpx

from app.config import settings

YANDEX_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
_RETRYABLE = (httpx.ConnectError, httpx.ReadTimeout)


class LLMClient:
    def __init__(self, cfg=settings):
        self.cfg = cfg
        self._headers = {
            "Authorization": f"Api-Key {cfg.yandex_api_key}",
            "x-folder-id": cfg.yandex_folder_id,
        }

    def _body(self, messages, temperature, max_tokens, stream=False):
        return {
            "modelUri": self.cfg.yandex_model_uri,
            "completionOptions": {
                "stream": stream,
                "temperature": temperature,
                "maxTokens": str(max_tokens),
            },
            "messages": messages,
        }

    async def chat(self, messages, temperature=0.3, max_tokens=2000, response_format="text"):
        if response_format == "json":
            messages = list(messages)
            messages[0] = {
                **messages[0],
                "text": messages[0]["text"] + "\nВерни только валидный JSON без markdown-обёртки.",
            }

        body = self._body(messages, temperature, max_tokens)
        text = await self._post(body)

        if response_format == "json":
            return self._parse_json(text)
        return text

    async def stream(self, messages, temperature=0.3, max_tokens=2000):
        body = self._body(messages, temperature, max_tokens, stream=True)
        async with httpx.AsyncClient(timeout=60) as client:
            async with client.stream("POST", YANDEX_URL, json=body, headers=self._headers) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data:"):
                        data = json.loads(line[5:].strip())
                        delta = (
                            data.get("result", {})
                            .get("alternatives", [{}])[0]
                            .get("message", {})
                            .get("text", "")
                        )
                        if delta:
                            yield delta

    async def _post(self, body):
        delays = [1, 2, 4]
        last_exc = None
        for delay in [0, *delays]:
            if delay:
                await asyncio.sleep(delay)
            try:
                async with httpx.AsyncClient(timeout=60) as client:
                    resp = await client.post(YANDEX_URL, json=body, headers=self._headers)
                    resp.raise_for_status()
                    return resp.json()["result"]["alternatives"][0]["message"]["text"]
            except _RETRYABLE as e:
                last_exc = e
        raise last_exc

    def _parse_json(self, text):
        text = text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        return json.loads(text)
