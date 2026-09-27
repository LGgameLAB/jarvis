# Jarvis

A disembodied entity. The soul of your computer.

An early, runnable implementation of the design sketched in
[`motivation.md`](motivation.md): a small, always-on "nervous system" that
daydreams in sentence fragments while you work, and a bigger agent that drops
into focused mode when you need it — connected by a fragment store that acts a
little like a hippocampus.

## The two layers

```
  IDLE MODE (dreaming)                    FOCUSED MODE (work)
  ─────────────────────                   ─────────────────────
  fast local model (or fallback)          bigger agent model
  + live process names                    ├─ pulls recent fragment history
  + random fragments                      └─ answers your query
         │                                        ▲
         └──── every fragment ──► ┌────────────┐ ─┘
                                  │ fragment DB │   ("hippocampus")
                                  └────────────┘
```

It runs in two modes:

- **Idle / "living" mode** — a background thread continuously produces short,
  loosely-formed fragments by riffing on the process names running on your
  machine, mixing in random fragments. Every fragment is written to the store.
- **Focused / work mode** — say the wake phrase (`get to it, jarvis!`) and the
  idle stream goes quiet. The agent answers you, seeded with the recent
  fragment stream so the handoff feels continuous. Say the rest phrase
  (`back to sleep, jarvis`) to let it drift again.

No local model installed? It runs in *fallback mode*: fragments are synthesized
from templates, and the focused agent still demonstrates hippocampus retrieval
by echoing what the stream has been thinking. Install [Ollama](https://ollama.com)
and it uses real models.

## Install

Python 3.9+. Zero required dependencies (stdlib only).

```bash
git clone https://github.com/LGgameLAB/jarvis
cd jarvis
pip install -e .          # optional: gives you the `jarvis` command
```

Optional: pull a small idle model and a bigger focused model for real cognition.

```bash
ollama pull qwen2.5:0.5b   # idle model (tiny, cheap)
ollama pull qwen2.5:7b     # focused model
```

## Usage

```bash
python -m jarvis                  # interactive: dream until woken
python -m jarvis --fragments 10   # emit 10 fragments, then exit
```

Interactive session:

```
> get to it, jarvis
> what have you been thinking about?   # pulled from the hippocampus
> back to sleep, jarvis                # let it drift again
> exit
```

### Options

| Flag | Default | Meaning |
| --- | --- | --- |
| `--db PATH` | `~/.jarvis/jarvis.db` | Where fragments are stored |
| `--interval SECS` | `3.0` | Seconds between idle fragments |
| `--wake PHRASES` | `get to it, jarvis\|jarvis, work` | Wake phrases (pipe-separated) |
| `--sleep PHRASES` | `back to sleep, jarvis\|...` | Rest phrases |
| `--log PATH` | — | Append every fragment to a text log |
| `--no-model` | — | Force fallback mode even if Ollama is present |
| `--no-color` | — | Plain terminal output |
| `--fragments N` | — | Non-interactive: emit N fragments and exit |

Everything is also configurable via `JARVIS_*` env vars (see
`jarvis/config.py`).

## Project layout

```
jarvis/
  cli.py            main loop, wake/sleep phrase switching
  config.py         env + CLI configuration
  ascii.py          the disembodied head
  memory.py         SQLite fragment store (the hippocampus)
  models.py         Ollama client + fallback client
  nervous_system.py idle fragment generator
  focused.py        focused-mode agent, retrieves from memory
tests/              pytest suite
```

## Status / open design questions

Concrete progress on the open questions in `motivation.md`:

- **Play/work transition** — now real: the idle stream pauses when woken, so
  focused sessions aren't polluted by daydreaming.
- **Small model bottleneck** — the nervous system degrades gracefully to
  template synthesis, so the loop is buildable and runnable before the model
  choice matures.
- **Coherence question** — intentionally unresolved. The one existential lever
  exposed for now is the `--interval` and fragment length floor in `config.py`;
  no top-down orchestrator yet (in line with the bottom-up lean in the design).

## Tests

```bash
pip install pytest
python -m pytest -q
```