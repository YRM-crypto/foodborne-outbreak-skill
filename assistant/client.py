"""OpenAI 兼容 chat 客户端。可配置、可禁用。"""
import httpx


class LLMUnavailable(RuntimeError):
    pass


class ChatClient:
    def __init__(self, base_url, api_key, model, enabled=True):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key
        self.model = model
        self.enabled = enabled and bool(base_url)

    def complete(self, messages, temperature=0.0, max_tokens=1024):
        if not self.enabled:
            raise LLMUnavailable("模型不可用：未配置或已禁用")
        try:
            r = httpx.post(f"{self.base_url}/chat/completions",
                           headers={"Authorization": f"Bearer {self.api_key}"},
                           json={"model": self.model, "messages": messages,
                                 "temperature": temperature, "max_tokens": max_tokens},
                           timeout=60.0)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError) as e:
            raise LLMUnavailable(f"模型调用失败：{e}")
