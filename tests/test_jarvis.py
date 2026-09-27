import pytest
import threading

from jarvis.memory import FragmentStore
from jarvis.config import Config
from jarvis.nervous_system import NervousSystem
from jarvis.models import FallbackClient, LLMFactory
from jarvis.focused import FocusedAgent


@pytest.fixture
def store(tmp_path):
    s = FragmentStore(str(tmp_path / "test.db"))
    yield s
    s.close()


@pytest.fixture
def cfg(tmp_path):
    c = Config(use_model=False, color=False, db_path=str(tmp_path / "test.db"))
    return c


def test_write_and_recent(store):
    store.write("hello world", "stream")
    store.write("second thought", "dream")
    recent = store.recent()
    assert [f.text for f in recent] == ["second thought", "hello world"]
    assert recent[0].source == "dream"


def test_search(store):
    store.write("the network stack hums at night", "stream")
    store.write("unrelated ramble", "dream")
    hits = store.search("network", limit=5)
    assert len(hits) == 1
    assert "network" in hits[0].text


def test_empty_search_returns_recent(store):
    store.write("short thought", "stream")
    assert len(store.search("", limit=5)) == 1


def test_synthesize_respects_bounds(cfg):
    ns = NervousSystem(None, FallbackClient(None, cfg), cfg)
    for _ in range(50):
        text = ns.synthesize("python")
        assert isinstance(text, str)
        assert len(text) > 0
        assert len(text) <= cfg.max_fragment_len


def test_emit_writes_to_store(store, cfg):
    ns = NervousSystem(store, FallbackClient(store, cfg), cfg)
    fragments = []
    ns.run(threading.Event(), sink=fragments.append, interval=0.0, max_fragments=3)
    assert len(fragments) == 3
    assert store.count() == 3
    assert all(f.text for f in fragments)


def test_wake_detection(cfg):
    from jarvis.cli import contains_any
    assert contains_any("get to it, jarvis!", cfg.wake_phrases)
    assert contains_any("Get to it Jarvis", cfg.wake_phrases)
    assert contains_any("jarvis, work", cfg.wake_phrases)
    assert not contains_any("hello jarvis how are you", cfg.wake_phrases)
    assert contains_any("back to sleep, jarvis", cfg.sleep_phrases)


def test_strip_wake(cfg):
    from jarvis.cli import strip_wake
    assert strip_wake("get to it jarvis, what is the weather", cfg) == "what is the weather"
    assert strip_wake("Get to it, Jarvis who are you", cfg) == "who are you"
    assert strip_wake("jarvis, work: read the logs", cfg) == "read the logs"
    assert strip_wake("get to it jarvis", cfg) == ""


def test_env_phrase_splitting_with_pipes(monkeypatch):
    from jarvis.config import Config
    monkeypatch.setenv("JARVIS_WAKE_PHRASES", "hey jarvis|jarvis, go")
    cfg = Config.from_env()
    assert cfg.wake_phrases == ("hey jarvis", "jarvis, go")


def test_focused_agent_fallback_uses_memory(store, cfg):
    store.write("a process named chrome swirling", "stream")
    agent = FocusedAgent(store, FallbackClient(store, cfg), cfg)
    answer = agent.respond("what have you been thinking?")
    assert isinstance(answer, str)
    assert len(answer) > 0


def test_context_includes_memory(store, cfg):
    store.write("the files hum to themselves", "stream")
    agent = FocusedAgent(store, FallbackClient(store, cfg), cfg)
    ctx = agent.context_for("files")
    assert "files" in ctx


def test_llm_factory_fallbacks_when_no_model(cfg):
    factory = LLMFactory(cfg, None)
    client = factory.default()
    assert isinstance(client, FallbackClient)