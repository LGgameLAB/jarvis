from .models import FallbackClient

FOCUSED_SYSTEM = (
    "You are Jarvis, a disembodied intelligence living in a computer. "
    "Below is material your background mind has been thinking (the hippocampus). "
    "Weave it into your answer naturally when relevant. Be direct and useful."
)

FOCUSED_OPTIONS = {"temperature": 0.6}


class FocusedAgent:
    def __init__(self, store, client, cfg):
        self.store = store
        self.client = client
        self.cfg = cfg

    def context_for(self, query):
        memories = self.store.recent(self.cfg.hippocampus_size)
        hits = self.store.searches_for(query, limit=5)
        seen = set()
        merged = []
        for fragment in hits + memories:
            if fragment.id not in seen:
                seen.add(fragment.id)
                merged.append(fragment)
        merged.sort(key=lambda f: f.id, reverse=True)
        merged = merged[: self.cfg.hippocampus_size]
        if not merged:
            return ""
        lines = [f"- [{f.source}] {f.text}" for f in merged]
        return "Recent stream of thought:\n" + "\n".join(lines)

    def respond(self, query):
        context = self.context_for(query)
        if isinstance(self.client, FallbackClient):
            return self.client.generate(query)
        prompt = context + "\n\nUser: " + query if context else query
        return self.client.generate(prompt, system=FOCUSED_SYSTEM, model=self.cfg.focused_model, options=FOCUSED_OPTIONS)

    def memory_summary(self, limit=6):
        fragments = self.store.recent(limit)
        if not fragments:
            return "Nothing in memory yet. Let me idle a moment first."
        return "Recent fragments:\n" + "\n".join(f"  ~ {f.text}" for f in reversed(fragments))