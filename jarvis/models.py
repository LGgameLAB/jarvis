import json
import urllib.error
import urllib.request

from . import config


def _post_json(url, payload, timeout=60):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


class OllamaClient:
    def __init__(self, host):
        self.host = host.rstrip("/")

    @property
    def is_model(self):
        return True

    def available(self):
        try:
            _post_json(self.host + "/api/tags", {}, timeout=3)
            return True
        except Exception:
            return False

    def generate(self, prompt, system=None, model=None, options=None):
        payload = {"model": model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options
        result = _post_json(self.host + "/api/generate", payload)
        return result.get("response", "").strip()


class FallbackClient:
    def __init__(self, store, cfg):
        self.store = store
        self.cfg = cfg

    @property
    def is_model(self):
        return False

    def available(self):
        return True

    def generate(self, prompt, system=None, model=None, options=None):
        if self.store is not None:
            recent = self.store.recent(3)
            stream = " | ".join(f.text for f in recent) if recent else "nothing yet"
            return ("I'm running in fallback mode (no local model configured). "
                    "My hippocampus remembers: %s." % stream[:200])
        return "I'm running in fallback mode."


class LLMFactory:
    def __init__(self, cfg: config.Config, store=None):
        self.cfg = cfg
        self.ollama = OllamaClient(cfg.ollama_host)
        self.store = store
        self._fallback = FallbackClient(store, cfg)
        self._cached = None

    def default(self):
        if self._cached is not None:
            return self._cached
        if self.cfg.use_model and self.ollama.available():
            self._cached = self.ollama
        else:
            self._cached = self._fallback
        return self._cached

    def idle_client(self):
        return self.default()

    def focused_client(self):
        return self.default()