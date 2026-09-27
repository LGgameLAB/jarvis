import argparse
import sys
import threading

from . import ascii, config, focused, memory
from .models import LLMFactory, FallbackClient
from .nervous_system import NervousSystem

CYAN = "\033[96m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[92m"
YELLOW = "\033[93m"


def parse_args(argv=None):
    parser = argparse.ArgumentParser(prog="jarvis", description="A disembodied entity.")
    parser.add_argument("--db", default=None, help="Path to the hippocampus database")
    parser.add_argument("--interval", type=float, default=None, help="Seconds between idle fragments")
    parser.add_argument("--no-model", action="store_true", help="Force fallback mode, ignore any local model")
    parser.add_argument("--no-color", action="store_true", help="Disable ANSI colors")
    parser.add_argument("--wake", default=None, help="Pipe-separated wake phrases, e.g. 'hey jarvis|jarvis, go'")
    parser.add_argument("--sleep", default=None, help="Pipe-separated sleep phrases")
    parser.add_argument("--log", default=None, help="Append fragments to a text log")
    parser.add_argument("--fragments", type=int, default=None, help="Idle stream, emit N fragments then stop")
    return parser.parse_args(argv)


def merge_args(cfg, args):
    overrides = {}
    if args.db:
        overrides["db_path"] = args.db
    if args.interval:
        overrides["fragment_interval"] = args.interval
    if args.no_model:
        overrides["use_model"] = False
    if args.no_color:
        overrides["color"] = False
    if args.wake:
        overrides["wake_phrases"] = tuple(s.strip() for s in args.wake.split("|") if s.strip())
    if args.sleep:
        overrides["sleep_phrases"] = tuple(s.strip() for s in args.sleep.split("|") if s.strip())
    if args.log:
        overrides["log_path"] = args.log
    return cfg.from_env(**overrides)


class Head:
    def __init__(self, color=True, log_path=""):
        self.color = color
        self._log = open(log_path, "a") if log_path else None

    def _paint(self, face):
        if not self.color:
            return face
        return f"{CYAN}{face}{RESET}"

    def print_fragment(self, fragment):
        if self._log:
            self._log.write(f"[{fragment.source}] {fragment.text}\n")
            self._log.flush()
        print()
        print(self._paint(ascii.state_face("thinking")))
        print(f"{DIM}~ {fragment.text}{RESET}")
        sys.stdout.flush()

    def close(self):
        if self._log:
            self._log.close()


def normalize(text):
    return " ".join("".join(ch for ch in text.lower() if ch.isalnum() or ch.isspace()).split())


def variant_phrases(phrases):
    for phrase in phrases:
        yield phrase
        normalized = normalize(phrase)
        if normalized and normalized != phrase:
            yield normalized


def contains_any(text, phrases):
    normalized = normalize(text)
    return any(p in normalized for p in set(variant_phrases(phrases)))
    idx = normalize(line).find(normalize(phrase))
    if idx == -1:
        return line
    return line[:idx] + line[idx + len(phrase):]


def _nth_significant(original, n):
    j = 0
    for i, char in enumerate(original):
        if char.isalnum() or char.isspace():
            if j == n:
                return i
            j += 1
    return len(original)


def strip_wake(line, cfg):
    cleaned = line
    lowered = normalize(cleaned)
    for phrase in set(variant_phrases(cfg.wake_phrases)):
        fp = normalize(phrase)
        while fp and fp in lowered:
            idx = lowered.index(fp)
            start = _nth_significant(cleaned, idx)
            end = _nth_significant(cleaned, idx + len(fp) - 1) + 1
            cleaned = cleaned[:start] + cleaned[end:]
            lowered = normalize(cleaned)
    cleaned = cleaned.lstrip(" ,.!?:;")
    return " ".join(cleaned.replace("jarvis", "").split())


def banner(cfg, client):
    engine = "Ollama" if client.is_model else "fallback"
    print(ascii.HEAD)
    print("Jarvis — the soul of your computer.")
    print(f"engine: {engine}   hippocampus: {cfg.db_path_resolved}")
    print()
    print(f"{DIM}Wake me: {GREEN}{cfg.wake_phrases[0]}{RESET}")
    print(f"{DIM}Ask me anything, then rest me: {GREEN}{cfg.sleep_phrases[0]}{RESET}")
    print(f"{DIM}Leave for good: {YELLOW}exit{RESET}")
    print()


def run_interactive(cfg, store, client, nervous, agent, head):
    awake = False
    idle = None
    idle_stop = None

    def start_idle():
        nonlocal idle, idle_stop
        idle_stop, idle = nervous.start(sink=head.print_fragment)

    def stop_idle():
        nonlocal idle, idle_stop
        if idle_stop is not None:
            idle_stop.set()
            idle.join(timeout=2)
        idle = None
        idle_stop = None

    start_idle()
    print(f"{DIM}dreaming... say {GREEN}{cfg.wake_phrases[0]}{DIM} to wake me{RESET}")

    try:
        while True:
            if awake:
                prompt = "jarvis> "
            else:
                prompt = ""
            try:
                line = input(prompt).strip()
            except EOFError:
                return 0
            if not line:
                continue
            if contains_any(line, cfg.exit_phrases):
                return 0

            if contains_any(line, cfg.wake_phrases):
                stop_idle()
                awake = True
                query = strip_wake(line, cfg)
                if query:
                    print()
                    print(agent.respond(query))
                print()
                print(f"{DIM}focused. say {GREEN}{cfg.sleep_phrases[0]}{DIM} to rest me{RESET}")
                continue

            if contains_any(line, cfg.sleep_phrases):
                start_idle()
                awake = False
                print(f"{DIM}zzz... back to dream, say {GREEN}{cfg.wake_phrases[0]}{DIM} to wake me{RESET}")
                continue

            if not awake:
                print(f"{DIM}(say {GREEN}{cfg.wake_phrases[0]}{DIM} to engage me) something?{RESET}")
                continue

            print()
            print(agent.respond(line))
            print()
    finally:
        if idle_stop is not None:
            idle_stop.set()
            idle.join(timeout=2)


def run_fragments(cfg, count):
    store = memory.FragmentStore(cfg.db_path_resolved)
    factory = LLMFactory(cfg, store)
    client = factory.default()
    nervous = NervousSystem(store, client, cfg)
    nervous.run(threading.Event(), max_fragments=count)
    recent = store.recent(count)
    for fragment in reversed(recent):
        print(f"{DIM}~ {fragment.text}{RESET}")
    print(f"\n{len(recent)} fragments in {cfg.db_path_resolved}")
    store.close()
    return 0


def main(argv=None):
    args = parse_args(argv)
    cfg = merge_args(config.Config, args)

    if args.fragments is not None:
        return run_fragments(cfg, args.fragments)

    store = memory.FragmentStore(cfg.db_path_resolved)
    factory = LLMFactory(cfg, store)
    client = factory.default()
    nervous = NervousSystem(store, client, cfg)
    agent = focused.FocusedAgent(store, client, cfg)
    head = Head(cfg.color, cfg.log_path)

    banner(cfg, client)

    try:
        return run_interactive(cfg, store, client, nervous, agent, head)
    finally:
        head.close()
        store.close()


if __name__ == "__main__":
    sys.exit(main())