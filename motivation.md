# Fluid AI Companion — Design Discussion Summary

*A working record of the design conversation for a "Jarvis"-style personal project.*

## The Core Vision

The project isn't really about voice assistants in the Alexa/Siri sense — that's would be the eventual delivery layer. The actual ambition is something closer to a synthetic mind that never stops running in the background of your computer. As I put it:

> "I'm more fascinated by the idea of creating a fluid AI system... essentially like a virtual organism where I'd be pairing a typical AI to something akin to a nervous system."

The intended effect isn't utility — it's presence:

> "I want to feel like there is a living entity in my computer, and I think that can be driven by a sentence fragment 'imagination' system like a daydreaming AI."

Surface layer, added last: speech-to-text, text-to-speech, and "a cool disembodied ASCII head talking to me from terminal."

## The Two-Layer Architecture

The system pairs two models with different jobs:

- **A fast, small local model** (something llama.cpp-class, run locally) acting as the "nervous system" — a continuous generator of small, loosely-formed thoughts.
- **A larger, more capable LLM** for actual conversation and agentic work, invoked only when needed.

I identified this small model as the real bottleneck of the whole project, more than hardware:

> "That's going to be the current limitation for the project... what small, fast LLMs are currently capable of really producing. That's going to determine a lot about the personality of the robot, in my opinion."

### Two operating modes

- **Idle / "living" mode**: the small model continuously produces sentence fragments — "little word clips in a sort of RNG simulation-like system" — partially human-filterable, giving the impression of a mind that's always thinking, "the way a human doesn't stop thinking or never just turns off."
- **Focused / work mode**: triggered by a wake phrase — I's placeholder example was *"get to it, Jarvis!"* — which shifts the system into a traditional agentic, Claude-style conversational mode.

I noted the boundary between these two states is a known simplification for now: "I would want a way to make this play/work dichotomy feel more fluid, but I don't think that's the main point."

## What Counts as a "Small Thought"

Several proposed sources for fragments, meant to be mixed rather than exclusive:

- Paired concepts sampled and recombined (echoing the "day-dreaming loop" research concept Claude surfaced — a background process pairing concepts from memory and filtering for interesting connections).
- Live system data as material — e.g., sampling running process names periodically and having the small model riff on/confabulate about what they might mean:

> "Maybe a more focused version would just be randomly pulling the names of processes on your computer every like couple half a second and then just chattering to itself with it... just making some things up."

- Purely random fragments, for baseline unpredictability.

## From "Filtering" to Memory Retrieval

I's first framing was that "filters" would be how the daydream stream gets shaped or limited — by degree of randomness, or by what it's allowed to pull from. But the conversation moved to a more architectural solution: rather than heavily filtering the fragments at generation time, every fragment writes into a **fast background database**, and the focused-mode agent retrieves from that store when engaged:

> "Every sentence fragment that's provided [to] a small LLM also goes straight into the database, and then when you talk to the main bot... it also pulls in information from the big database — which honestly would work really well with an agentic system. I actually think that's the better move."

Claude's framing of why this matters structurally:

> "If every fragment writes to a fast store and the focused-mode agent pulls from it via something like retrieval, you've basically built a hippocampus — the daydream isn't filtered at generation time so much as filtered by what becomes retrievable when it matters."

This means the idle stream itself can be left rawer and stranger, since it doesn't have to be useful on its own — only useful in aggregate, when retrieved.

## The Coherence Question (Still Open)

The central unresolved design question: how much, if any, top-down structure should shape the fragment stream so that "thoughts" hold together into something like a train of thought (e.g. noticing the bot has drifted into telling jokes), versus staying purely emergent from bottom-up chaining.

Claude framed this as a fork with two named directions:

> "**Bottom-up / emergent coherence.** No orchestrator... the sampler [has] a small amount of state that persists and decays... [giving] loose, drifting continuity without anything deciding that on purpose... **Top-down / orchestrated coherence.** A cheap higher-level process periodically picks a 'theme slot' that soft-constrains what the small model samples next... closer to scripted texture pretending to be spontaneous."

And tied it to the classic tension in cognitive science between associative/spreading-activation models of thought and predictive-processing/hierarchical models — noting human cognition likely does both at once.

I's answer leans firmly toward the emergent, non-hierarchical end:

> "Streaming consciousness is really like an inspiration for this, and that is kind of what I'm going for. I don't really want the predictive, like the hierarchical model for the bot as much."

## Personality, Noise, and the "Floor" Question

A live tension I is sitting with rather than resolving: whether to put a "floor" under the fragment stream to keep it from derailing into incoherence or unpleasant rants, versus letting whatever the raw cognitive system produces simply *be* its personality — including the risk of it being unpleasant.

> "As much as I hate deranged AI rants, I do feel like to some degree the eventual path that the 'cognitive system' decides to take is essentially its personality, and then adding a floor makes it artificially similar to a human as opposed to naturally what the bot is."

This is explicitly left open as a design question rather than decided.

## Stated Influences

- **Douglas Hofstadter's *Gödel, Escher, Bach*** — I names this as a direct philosophical touchstone, with the project's spirit deliberately echoing the 1970s-era fascination with self-referential, emergent intelligent systems rather than modern large-scale LLM engineering.
- The **day-dreaming loop** concept (background process pairing and filtering concepts for novel connections) and the **"Thoughtful AI"** research framing (AI as a continuously-thinking entity that surfaces intermediate thoughts in real time, rather than a turn-based input/output system) — both surfaced by Claude as close existing precedent, though the specific combination of a small local "nervous system" model, human-tunable idle cognition, retrieval-based memory bridging idle and focused modes, and a deliberate wake-phrase mode switch appears to be I's own synthesis.

## Explicitly Out of Scope (For Now)

- Code generation — I asked Claude not to start writing code yet; the current phase is concept design only.
- A polished play/work transition — acknowledged as a future refinement, not the current focus.
- A resolved answer on the coherence and "floor" questions above.

## Open Questions Going Forward

- What exactly triggers a topic shift or "attractor" change in the fragment stream, if anything does.
- How much of the idle stream's recent content the focused-mode agent should see on handoff, so the transition feels continuous.
- What the actual candidate small models are, and what's achievable running locally on I's hardware.
- Whether/how much of a coherence floor to build in, and what "personality via unfiltered process" actually feels like in practice once built.
