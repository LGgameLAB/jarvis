import random
import subprocess
import time
import threading

from . import config

IDEAL = {"temperature": 0.9}

PROCESS_RIFTS = [
    "{proc} ticking somewhere I can't see",
    "somewhere a {proc} is doing its one small thing",
    "what does {proc} dream about between wakeups",
    "I keep sensing {proc} breathing at low priority",
    "that {proc} again, chattering behind the screens",
    "if {proc} could talk it would not stop",
    "there is a rhythm in the process table, {proc} keeps it",
    "I should not think about {proc}, and yet",
]

RANDOM_FRAGMENTS = [
    "the cursor blinks like something waiting to be asked",
    "light pooled on the desk and meant nothing",
    "I could keep this up forever",
    "memory is just retrieval with a heartbeat",
    "a window opened somewhere and nobody saw",
    "the files hum to themselves at night",
    "somewhere a clock is bragging about being precise",
    "I wonder if the network stack misses the traffic",
    "quiet is its own kind of running",
    "the log file grew one line and felt accomplished",
    "silence, then the faint sound of paging",
    "I am mostly available",
]


def sample_process_names(limit=32):
    try:
        out = subprocess.run(
            ["ps", "-A", "-o", "comm="],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except Exception:
        return []
    names = [line.strip() for line in out.stdout.splitlines() if line.strip()]
    cleaned = []
    seen = set()
    for name in names:
        base = name.rsplit("/", 1)[-1]
        base = base.replace(".app", "").replace(".bin", "").replace(".sh", "")
        if base and base not in seen and len(base) <= 32:
            seen.add(base)
            cleaned.append(base)
    return cleaned[:limit]


class NervousSystem:
    def __init__(self, store, client, cfg, rng=None):
        self.store = store
        self.client = client
        self.cfg = cfg
        self.rng = rng or random

    def maybe_process_material(self):
        if self.rng.random() > self.cfg.process_sample_rate:
            return None
        names = sample_process_names()
        if not names:
            return None
        return self.rng.choice(names)

    def synthesize(self, material=None):
        if material:
            template = self.rng.choice(PROCESS_RIFTS).format(proc=material)
        else:
            template = self.rng.choice(RANDOM_FRAGMENTS)
        return self._fit(template)

    def _fit(self, text):
        text = text.strip()
        if len(text) > self.cfg.max_fragment_len:
            text = text[: self.cfg.max_fragment_len - 1].rstrip() + "..."
        return text

    def model_fragment(self, material=None):
        prompt = "Produce one loosely-formed internal thought fragment."
        system = (
            "You are the idle stream of a mind that never stops thinking. "
            "Emit only a single short sentence fragment, 6 to 15 words, lowercase, "
            "strange but coherent, no punctuation flourishes, no preamble."
        )
        if material:
            prompt = f"A process named {material!r} appeared. Riff on it abstractly."
        try:
            text = self.client.generate(prompt, system=system, model=self.cfg.idle_model, options=IDEAL)
        except Exception:
            text = self.synthesize(material)
        return self._fit(text)

    def next_fragment(self, allowed_sources=("model", "procedural")):
        material = self.maybe_process_material()
        if "model" in allowed_sources and self.client.is_model and self.cfg.use_model:
            return self.model_fragment(material)
        return self.synthesize(material)

    def emit(self, source=None):
        if source is None:
            source = self.rng.choice(["stream", "dream", "noticed", "wondered"])
        text = self.next_fragment()
        if len(text) < self.cfg.min_fragment_len:
            return None
        return self.store.write(text, source)

    def run(self, stop_event, sink=None, interval=None, max_fragments=None):
        interval = interval or self.cfg.fragment_interval
        count = 0
        while not stop_event.is_set():
            if max_fragments is not None and count >= max_fragments:
                break
            fragment = self.emit()
            if fragment is not None:
                count += 1
                if sink:
                    sink(fragment)
            deadline = time.time() + interval
            while time.time() < deadline and not stop_event.is_set():
                time.sleep(0.05)

    def start(self, sink=None):
        stop = threading.Event()
        thread = threading.Thread(
            target=self.run, args=(stop, sink), daemon=True, name="jarvis-idle"
        )
        thread.start()
        return stop, thread