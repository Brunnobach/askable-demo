# Harbor Terminal Tasks

The vocabulary for authoring and validating terminal tasks in this repository. Read this first: it defines *what the pieces are*. The `README.md` and `CONTRIBUTING.md` explain *how to create, run, and submit* them.

A **task** is a self-contained challenge: an agent is dropped into a container with an instruction, does work, and a verifier decides whether it succeeded. This repo is a template for writing such tasks for Askable and proving they meet the difficulty and provenance bar.

## Platform

**Harbor**:
The framework that builds a task's environment, runs an agent or the oracle against it, and executes the verifier. The tool you invoke locally is `harbor`.

**Terminal-Bench**:
The benchmark of terminal tasks that Harbor was built to run. A task authored here follows the Terminal-Bench task structure.
_Avoid_: tbench (except as the domain name).

**Agent**:
The AI system under test. It reads the instruction and works inside the environment; it never sees the verifier or the oracle solution.

**terminus-2**:
The default agent harness (model + scaffolding) used for calibration in this repo. It drives the container through `tmux`, so every task image must install it at build time (`AUTHORING.md` §6). Paired with the model named in `calibration-target.json` — currently `gemini/gemini-3.8-flash` at 10 attempts. Calibration difficulty is defined relative to this designated agent+model, not agents in general.

**Harness**:
Any Harbor-supported agent used to run attempts against a task. `terminus-2` is the calibration default; authors may also self-check locally with `antigravity` or `gemini-cli` for a Gemini-flavoured pass. The authoritative run always uses whatever `calibration-target.json` specifies.

## Task anatomy

**Task**:
The unit of work in this repo: one directory under `tasks/` bundling an instruction, an environment, a verifier, an oracle solution, and submission records. The whole thing is what gets calibrated and submitted.

**Instruction**:
The agent-facing description of what to accomplish (`instruction.md`). The verifier must check only behavior the instruction actually states.
_Avoid_: prompt, spec.

**Environment**:
The container the task runs in, built once from `environment/Dockerfile` and reused for both the agent and the verifier. The agent works in whatever the Dockerfile's `WORKDIR` sets. Holds only what an agent needs to attempt the task — never verifier-only tooling.

**Verifier**:
The code that decides whether an attempt succeeded and emits a reward. Its entry point is `tests/test.sh`; it installs its own tooling, runs the test suite against the filesystem the agent modified, and writes the reward.
_Avoid_: grader, checker, "the tests" (the suite is part of the verifier, not the whole of it).

**Reward**:
The verifier's outcome for one attempt. `1` means the attempt satisfied the task; `0` means it did not.
_Avoid_: score, pass/fail, result.

## Solutions

A **solution** is always qualified by who authored it. Never use "solution" unqualified — it hides the distinction that matters here.
_Avoid_: bare "solution".

**Oracle solution**:
The reference solution an author writes (`solution/solve.sh`) to prove the task is solvable. Applied by the oracle, never seen by the agent, and must earn reward `1`.

**Agent solution**:
The work an agent produces in a trial. Unlike the oracle solution it is not assumed to work — a trial exists precisely to find out whether it earns reward `1`.

**Oracle**:
The mode in which Harbor applies the oracle solution instead of running an agent, then runs the verifier. Passing oracle validation (reward `1`) is the precondition for everything else.
_Avoid_: reference run, ground truth.

## Difficulty and submission

**Trial**:
A single run of the task — either an oracle validation or one run that produces an agent solution — together with its logs and reward.

**Calibration**:
The fixed-attempt measurement that fixes a task's difficulty. The designated agent, model, attempt count, and eligibility band all come from `calibration-target.json`. A task is eligible only if the number of successful attempts lands inside the band: hard enough to be interesting, easy enough to be solvable.

**Self-check**:
An author's own difficulty measurement, recorded in `calibration/self-check.json` and marked `"authoritative": false`. It may use any agent and model (`--target`), so it is evidence about a task, never the measurement that decides acceptance. Only Askable's run against `calibration-target.json` writes `calibration/results.json`.

**Pass rate**:
The fraction of calibration attempts that earned reward `1`, out of the target's `attempt_count`.

**Category**:
The single approved kind a task belongs to (Bug Fix, Generation, Feature Request, Refactor, Translation/Migration, Decompilation/Reverse Engineering, Security Patch/Exploitation), set in `task.toml`.

**Provenance**:
The record (`provenance.json`) of every third-party dependency, sample, dataset, binary, or fixture in a task, with the license and the reason its terms permit Askable's AI-training use. An empty record asserts the task contains none.

**Attestation**:
A contributor's signed, commit-bound declaration (`attestations/<github-handle>.md`) affirming a hand-written instruction, personal verification of every task file, disclosure of AI tools used, authority to contribute, and assignment of rights to Askable. Bound to the exact task-code commit it covers.
