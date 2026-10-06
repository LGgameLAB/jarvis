import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_str(name, default):
    return os.environ.get(name, default)


def _env_float(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _env_int(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _env_bool(name, default):
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    db_path: str = "~/.jarvis/jarvis.db"
    idle_model: str = "qwen2.5:0.5b"
    focused_model: str = "qwen2.5:7b"
    ollama_host: str = "http://127.0.0.1:11434"
    fragment_interval: float = 3.0
    min_fragment_len: int = 12
    max_fragment_len: int = 140
    process_sample_rate: float = 0.6
    hippocampus_size: int = 12
    wake_phrases: tuple = ("get to it, jarvis", "jarvis, work")
    sleep_phrases: tuple = ("back to sleep, jarvis", "be quiet, jarvis", "hush, jarvis")
    exit_phrases: tuple = ("exit", "quit")
    use_model: bool = True
    color: bool = True
    log_path: str = ""

    @property
    def db_path_resolved(self):
        return str(Path(self.db_path).expanduser())

    @classmethod
    def from_env(cls, **overrides):
        values = {
            "db_path": _env_str("JARVIS_DB", cls.db_path),
            "idle_model": _env_str("JARVIS_IDLE_MODEL", cls.idle_model),
            "focused_model": _env_str("JARVIS_FOCUSED_MODEL", cls.focused_model),
            "ollama_host": _env_str("JARVIS_OLLAMA_HOST", cls.ollama_host),
            "fragment_interval": _env_float("JARVIS_FRAGMENT_INTERVAL", cls.fragment_interval),
            "min_fragment_len": _env_int("JARVIS_MIN_FRAGMENT_LEN", cls.min_fragment_len),
            "max_fragment_len": _env_int("JARVIS_MAX_FRAGMENT_LEN", cls.max_fragment_len),
            "process_sample_rate": _env_float("JARVIS_PROCESS_SAMPLE_RATE", cls.process_sample_rate),
            "hippocampus_size": _env_int("JARVIS_HIPPOCAMPUS_SIZE", cls.hippocampus_size),
            "wake_phrases": tuple(
                s.strip() for s in _env_str("JARVIS_WAKE_PHRASES", "|".join(cls.wake_phrases)).split("|") if s.strip()
            ),
            "sleep_phrases": tuple(
                s.strip() for s in _env_str("JARVIS_SLEEP_PHRASES", "|".join(cls.sleep_phrases)).split("|") if s.strip()
            ),
            "exit_phrases": tuple(
                s.strip() for s in _env_str("JARVIS_EXIT_PHRASES", "|".join(cls.exit_phrases)).split("|") if s.strip()
            ),
            "use_model": _env_bool("JARVIS_USE_MODEL", cls.use_model),
            "color": _env_bool("JARVIS_COLOR", cls.color),
            "log_path": _env_str("JARVIS_LOG", cls.log_path),
        }
        values.update(overrides)
        return cls(**values)