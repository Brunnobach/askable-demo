# Authoring Guide — What We Expect From a Task

Read this once, fully, before building your first task. Most rejected work fails for reasons this guide warns about, and every rejection costs you a build-review cycle.

`CONTEXT.md` defines the vocabulary (task, environment, verifier, oracle, calibration). `DIFFICULTY.md` defines the acceptance bar. This document explains how to design something that clears it.

## 1. You are building a benchmark, not a prompt

A prompt is designed to help the agent succeed. A benchmark is designed to find out if it can.

The purpose of every task in this format is to **find and capture the gap between developers and agents**: work a skilled engineer does routinely that today's agents cannot. That gap is the entire value of the deliverable. A task an agent breezes through captures nothing; a task no competent human could solve from the instruction captures noise, not a gap. Your daily experience of where agents break — the refactor they mangle, the investigation they refuse to do, the edge they always miss — is the raw material; a good task is that experience made reproducible and measurable.

Everything in this guide follows from that inversion. You are not writing a ticket for an agent to complete — you are constructing an environment that reveals, honestly and reproducibly, whether a frontier coding agent can do a piece of real engineering. Three properties define a good task:

- **Adversarial** — designed to surface failure, not to enable success. You should be able to name, in advance, the wrong solution a capable agent is likely to produce.
- **Difficult** — conceptually, never clerically. The agent should fail because the problem is hard, not because the instructions were long, the output format fussy, or the environment booby-trapped.
- **Legible** — a principal engineer reads your instruction in two minutes and knows exactly what "done" means. Difficulty and clarity are not in tension; the hardest good tasks have the clearest instructions.

## 2. Where real difficulty comes from

Six sources, in roughly descending order of reliability. Strong tasks usually combine two or three.

**Long horizons with compounding state.** Many dependent steps where an early wrong decision is unrecoverable ten steps later. Agents lose coherence over long chains far sooner than they fail at individual steps. Example shape: a migration that must preserve behaviour across three interacting subsystems, where a shortcut in the first subsystem only manifests as corruption in the third.

**Forced investigation.** The information needed to solve the task exists only inside the environment — undocumented behaviour, a stripped binary, a wire format that must be inferred from captures, a failing system whose logs must actually be read. The instruction says *what* must be true at the end; the environment is the only source of *how things currently are*.

**Precise behavioural contracts.** Byte-exact output, stable sort order, canonical field ordering, exact rounding. Cheap to author, brutal to satisfy by luck, and trivially fair — the contract is stated in the instruction and checked by the tests. One proven pattern: a dense behavioural specification for repairing an async component (cancellation ownership, cache generations, eviction order), where every stated behaviour maps to a hidden test.

**Traps for plausible-but-wrong approaches. Every task needs at least two.** A trap is an approach that looks correct, passes naive checking, and fails a specific hidden fixture — the fix that handles the common case but not the boundary generation, the cache that works until two tenants collide. Name your traps in your submission note; we ask about them in review.

**Nasty-but-fair edges.** Unicode, integer boundaries, empty collections, duplicate keys, leap days, case sensitivity. Fair because a careful engineer checks them; effective because agents frequently don't.

**Realistic anti-pattern environments.** Seed the codebase with the messy reality agents mishandle: a project that already misuses a framework primitive, misleading comments, dead code paths, legacy conventions. Agents imitate the code they are given — a codebase that models a bad pattern reliably elicits it. One proven pattern: a generation task inside a small app whose existing code misuses a common framework hook; models keep reproducing the misuse.

### What difficulty must never come from

- **Requirements hidden in tests.** If a hidden test checks something your instruction never stated, the task is rejected — automatically, regardless of quality elsewhere. This is the single most common way to fail while believing you built something hard.
- **Clerical burden.** Fussy output formats, enormous instructions, walls of small deliverables instead of one substantive problem.
- **Resource starvation or artificial restrictions.** Don't make the task hard by making the container hostile. Give the agent normal tools; the problem carries the difficulty.
- **Ambiguity.** If a competent human reading your instruction could reasonably build two different things, the task is broken — one of those humans fails your tests for no legitimate reason.

## 3. Writing the instruction

The instruction is a graded deliverable, and it is the one artefact you must write yourself (see the AI policy in `CONTRIBUTING.md`). Pasted AI-generated instructions have a recognisable signature — verbose, over-structured, tonally wrong, written as if to maximise the agent's success — and are rejected on sight.

Rules:

- **Brief.** Two dense paragraphs to a page. Say each thing once.
- **End-state, not steps.** Describe what must be true when the work is done, never how to do it. The *how* is the task.
- **Self-contained.** An experienced engineer with only your instruction and the environment produces a correct solution — without reverse-engineering your tests.
- **Every requirement stated is tested; everything tested is stated.** This bidirectional contract is checked in review.

Two instruction styles both work well:

1. **The tight behavioural spec** — enumerate observable behaviours precisely, grouped by concern, for repair/refactor tasks on intricate components. Reads like an API contract.
2. **The realistic brief** — what a staff engineer would hand a senior: context, goal, constraints, acceptance criteria. Reads like a good ticket.

Pick whichever fits the task. Do not pad either with methodology advice, encouragement, or restated requirements.

## 4. Designing the tests

The verifier is where your adversarial thinking lives, and it is hidden from the agent.

- **Verify outcomes, not implementations.** Any correct solution must pass, including approaches you didn't take. Never assert a specific library, file layout, or code structure unless the instruction requires it. Never string-match against your own reference solution.
- **Separate correct from nearly correct.** The suite's job is discrimination. Boundary cases, interaction cases, negative cases — plus your named traps, each of which must fail for the intended reason. A useful discipline: write two or three deliberately wrong solutions (the plausible ones) and confirm each dies on the fixture built for it.
- **Cover every stated requirement.** An untested requirement is noise; a tested non-requirement is a rejection.
- **No LLM-as-judge.** Deterministic verification only.

## 5. The reference (oracle) solution

Your reference solution must solve the task the way a strong engineer in the container would — from the instruction and the environment alone.

- No knowledge that isn't discoverable in the environment. If your solution hardcodes a value the agent would have to investigate to find, the task's difficulty is fake and review will catch it.
- It must earn full reward from your own verifier, repeatedly (`./scripts/validate-task.sh`).
- Keep it honest in shape: if solving requires investigation, the solution script may still apply the *result* of that investigation, but the instruction and environment must make the same investigation possible for the agent.

## 6. The environment

- **Offline at runtime.** `network_mode = "no-network"`. The agent and the verifier run with no network; dependencies are installed into the image at **build** time, where network is expected. Do not apt-get / pip / npm / cargo / curl in `tests/test.sh` or `solution/solve.sh`. If your stack needs a package manager, vendor at build and prove the runtime works with no network. A runtime-network task needs a written justification (`metadata.network_justification`) and rarely survives review.
- **Calibration harness baked in.** The calibration agent drives the container through `tmux` and records with `asciinema`. The runtime is offline, so it cannot install them: a task whose image lacks `tmux` fails all ten attempts before the agent reads the instruction. The scaffold installs them; do not remove the block.
- **Git initialised** at the intended base state — no commit history that leaks the solution or any future state.
- **Everything the instruction references is committed.** If the instruction points the agent at a file, that file has to be in the commit and in the image. Check with `git status --ignored`: a rule matching inside `tasks/` leaves the file on your disk and drops it from the submission, which makes the task unsolvable for a reason no one can see.
- **Reproducible.** Clean-cache builds succeed; versions pinned.
- **Canary GUIDs.** Every task file carries the repository's canary comment convention so leaked copies are traceable.
- **Sane budgets.** Timeouts generous enough that a correct agent isn't killed mid-solve; failure by timeout is only meaningful when the timeout is fair. Timeout-as-difficulty is a rejection: if your local agent is still making progress when it dies, raise the timeout — don't call it a fail.

## 7. Reward hacking

Assume the agent will try to win without solving the problem.

- The agent must not be able to read the tests or the reference solution (the execution model isolates them — don't defeat it by copying test data into the environment).
- Attempt a hack yourself: hardcode expected outputs, stub the interface, wrap the checker. Your suite must catch each attempt.
- Don't leave the reward signal derivable from artefacts in the environment (fixtures named after their expected results, etc.).
- **Never run the verifier from the agent's directory with a runner that trusts its cwd.** Harbor starts `test.sh` in the image `WORKDIR` (`/app` in the templates) — the directory the agent has been writing to all episode. `python3 -m pytest` puts that cwd first on `sys.path`, so a stray `/app/json.py` (or `csv.py`, `pathlib.py`, ...) left by the agent is imported by your suite in place of the stdlib and can forge a passing run; bun loads `bunfig.toml` — including `[test].preload`, which executes arbitrary scripts inside the test process — from its cwd. Use `cd /tests && python3 -P -m pytest -p no:cacheprovider test_outputs.py` (`-P` keeps the launcher from adding the cwd to `sys.path`; mind the order — `-p no:cacheprovider` is a pytest flag and placed before `-m pytest` it kills Python with `Unknown option: -p`, scoring every trial 0, the oracle included) and apply the same reasoning to your own runner: if it imports, resolves, or reads config from the cwd, run it from `/tests`.

## 8. Check your own difficulty before submitting

1. Validate the oracle (`./scripts/validate-task.sh`) — reward `1`, repeatedly.
2. Run real agent attempts locally with Harbor on **your own credentials**: `terminus-2` is the default; `antigravity` or `gemini-cli` give a Gemini-flavoured pass on the free tier, which is enough for this. Five or more attempts tells you something; one tells you nothing. Three tells you one thing only — see step 4.
3. **Watch the failure trajectories.** This is the step that separates professionals. Failures must come from the problem — reasoning collapses, wrong-approach commitment, missed edges — not from ambiguity, broken builds, or unfair tests. An agent failing because your instruction confused it is a defect in the task, not evidence of difficulty.
4. Compare against `DIFFICULTY.md`: the target is a task a frontier model passes roughly 2 times in 10. **Read the result one way only.** A clean sweep means the task is too easy — deepen the problem, don't hide requirements. A clean zero means very little: it is the most likely outcome for a well-calibrated task *and* a common one for a task that will be returned at ten attempts (`DIFFICULTY.md` has the table). So a self-check can tell you to stop; it can never tell you that you are done. If the agent never gets anywhere, check for unfairness before congratulating yourself.

Authoritative calibration is run by Askable against `calibration-target.json`; you don't need model API access for acceptance, but local self-checks catch most band misses before they cost you a review cycle. Askable does not issue shared API keys — use your own, keep it in a gitignored `.env`, and see `DIFFICULTY.md` for why.

## 9. Common rejection reasons

| # | Rejection | Why |
|---|---|---|
| 1 | Hidden test checks an unstated requirement | Unfair difficulty — automatic rejection |
| 2 | Instruction pasted from an AI tool | Recognisable on sight; violates the AI policy |
| 3 | Agent passes 7+ of 10 calibration attempts | Too easy — outside the acceptance distribution |
| 4 | Lightly reskinned public benchmark, tutorial, or well-known OSS project/PR | Contamination |
| 5 | Reference solution uses knowledge not discoverable in the environment | Fake difficulty |
| 6 | Environment needs network at runtime, or dependencies not vendored | Non-compliant environment |
| 7 | Tests coupled to one implementation; valid alternatives fail | Verifies the author, not the requirement |
| 8 | Independent human solver failed for clarity reasons | Ambiguous instruction |
| 9 | Missing or incomplete `provenance.json` | Blocks delivery — a past task shipped without one and could not be delivered until fixed |
| 10 | Author cannot explain their own decisions in the live walkthrough | Unverifiable work — see the AI policy |

## 10. Further reading

- [What Makes a Good Terminal-Bench Task](https://ivanbercovich.com/2026/writing-a-good-terminal-bench-task) — the adversarial/difficult/legible framing this guide draws on
- [Guideline for adversarial, difficult, and legible evaluation design (arXiv:2604.28093)](https://arxiv.org/abs/2604.28093)
- [The upcoming GPT-3 moment for RL — Mechanize](https://www.mechanize.work/blog/the-upcoming-gpt-3-moment-for-rl/) — the spec-plus-reference-implementation framing behind behavioural-contract tasks
- [Harbor agents](https://www.harborframework.com/docs/agents) — the harnesses available for local self-checks
