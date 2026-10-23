# Terminal Task Template

Source-available template for authoring [Harbor](https://www.harborframework.com/) / [Terminal-Bench](https://www.tbench.ai/) evaluation tasks for Askable: self-contained Docker environments in which frontier AI coding agents are evaluated on real engineering problems. It includes working `hello-world` examples, task scaffolding, deterministic oracle validation, an export tool, and a reproducible calibration workflow whose designated model, attempt count, and eligibility band are pinned in `calibration-target.json`.

**The goal of every terminal task is to capture something skilled developers can do that AI agents cannot yet do.** A task earns its place by isolating one of those gaps: an agent fails it for real engineering reasons, while an experienced engineer solves it from the instruction alone. Tasks agents already handle are worthless; so are tasks no human could solve.

This work is for senior, AI-native engineers: people who use modern agentic coding tools daily, know where those agents break, and can turn that knowledge into tasks the agents fail for the right reasons.

Use is restricted by the repository license and the Askable participant agreement. Do not use this repository to create tasks for another purpose.

## Read these first

1. **`AUTHORING.md`** — what a good task is and how to design one. The core document; read it before writing anything.
2. **`DIFFICULTY.md`** — the acceptance bar: how difficulty is measured and what gets rejected.
3. **`CONTRIBUTING.md`** — process, the AI-use policy, provenance, and attestations.
4. **`CONTEXT.md`** — the vocabulary (task, environment, verifier, oracle, calibration) the other documents assume.

## The workflow, end to end

1. **Sign the Askable participant agreement**, then clone this public repository.
2. **Create your own private GitHub repository** from your clone. All your work lives there, under your account, with real incremental commit history — we review that history as part of acceptance.
3. **Install the tooling:** [Docker](https://docs.docker.com/get-docker/), [uv](https://docs.astral.sh/uv/), and Harbor:
   ```bash
   uv tool install harbor
   ```
4. **Scaffold a task** (`./scripts/new-task.sh my-new-task`) and build it: environment, instruction, hidden tests, reference solution, provenance. `AUTHORING.md` is the guide; the AI-use rules are in `CONTRIBUTING.md`.
5. **Validate the oracle and run the local checks** (see below).
6. **Self-check difficulty before you submit** with local Harbor agent runs — `terminus-2` by default, or `antigravity` / `gemini-cli` for a Gemini-flavoured pass — and watch the failure trajectories (`AUTHORING.md` §8). We expect this: a submission that lands outside the difficulty band costs a full review round-trip, and a handful of local runs catches it in an hour. Askable still runs the authoritative calibration — you don't need the designated model's API keys, and any strong agent will expose a too-easy task.
7. **Submit via the two-commit flow** (below), then either:
   - add Askable's reviewer account (`@xicovarisco`) as a read collaborator on your private repository, or
   - run `./scripts/export-task.sh tasks/my-new-task` and send us the archive it produces.

## Create a task

```bash
./scripts/new-task.sh my-new-task
```

The generated task contains the files defined in [CONTEXT.md](CONTEXT.md):

- `instruction.md` — hand-written; see the AI policy in `CONTRIBUTING.md`
- `task.toml` — Harbor configuration
- `environment/Dockerfile`
- `tests/test.sh` — verifier entry point (writes `/logs/verifier/reward.txt` or `reward.json`)
- `solution/solve.sh` — the oracle solution
- `provenance.json`
- `attestations/YOUR_GITHUB_HANDLE.md`

Set exactly one approved `metadata.category` in `task.toml` (see the category list in [CONTEXT.md](CONTEXT.md)), set `metadata.primary_languages` to a non-empty list of the primary implementation languages (`Python`, `Rust`, `TypeScript`, and similar conventional names), and list every AI tool you used in `metadata.ai_tools_used` (e.g. `["claude-code", "cursor"]`; use `[]` if none).

`tasks/hello-world-py` and `tasks/hello-world-ts` are working reference examples only. They are deliberately easy and are not eligible for submission.

## Develop and validate

### How a task runs

The `solution/` and `tests/` directories don't sit next to the agent — they're isolated and appear only for the oracle and verifier phases. [docs/execution-model.md](docs/execution-model.md) explains, with diagrams and a `hello-world` walkthrough, how these directories map into the container, why the agent never sees them, and where each dependency belongs.

### Oracle validation

Validate the reference solution:

```bash
./scripts/validate-task.sh tasks/my-new-task
```

This runs the oracle then the verifier (see [docs/execution-model.md](docs/execution-model.md)); a reward of `1` means the task is solvable.

On failure, the script prints `cat` commands for the relevant trial logs under `./trials/<trial-name>/`:

- `verifier/setup-stdout.txt` — verifier dependency install output
- `verifier/suite-stdout.txt` — test suite output (pass/fail details)
- `agent/oracle.txt` — reference solution output (useful when `solve.sh` failed or did nothing)

`harbor view ./trials` is mainly useful for agent calibration runs, not oracle validation (oracle trials have no agent trajectory to browse).

### Interactive development

Explore a task environment interactively:

```bash
harbor tasks start-env -p tasks/my-new-task -e docker -i
```

### Submission record checks

Validate task metadata and submission records:

```bash
./scripts/validate-submissions.sh
```

## Calibrate difficulty

**Askable runs the authoritative 10-attempt calibration job. You do not need model API keys to submit.** The designated agent, model, attempt count, and eligibility band are defined in `calibration-target.json` at the repo root (currently `terminus-2` with `gemini/gemini-3.8-flash`, 10 attempts, 1–4 successes eligible — see `DIFFICULTY.md` for the full standard). Never edit the target file.

Self-checking before you submit is **expected**: a handful of local agent runs (step 5) catches most band misses before they cost you a full review round-trip. You don't need the designated model — pass `--target` with your own agent/model config; a too-easy task shows up on any strong agent. `gemini-3.8-flash` is on the free tier of Gemini CLI and Antigravity, so a screen costs you time rather than money.

**Run self-checks on your own credentials.** Askable does not issue shared API keys, and a key committed to your task repository is a rejection — we read the commit history. Read the result one way only: a clean sweep means the task is too easy and you should stop; a clean zero means very little. `DIFFICULTY.md` has the numbers. Don't let calibration tuning eat your build budget.

1. Read [CONTRIBUTING.md](CONTRIBUTING.md) and fill out `provenance.json` for the task.
2. Commit the task code and provenance, then capture that commit's SHA:
   ```bash
   git add tasks/my-new-task
   git commit -m "Add my new terminal task"
   TASK_CODE_COMMIT="$(git rev-parse HEAD)"  # SHA of the commit just made; attestations bind to it
   ```
3. Copy `.env.example` to `.env` and add **your own** API key for whichever agent/model you self-check with. `.env` is gitignored; keep it that way.
4. Complete each contributor attestation in `tasks/my-new-task/attestations/YOUR_GITHUB_HANDLE.md` using `TASK_CODE_COMMIT`.
5. Self-check — run the calibration with `--self-check` (add `--target <path>` with your own agent/model config if you don't have keys for the designated model):
   ```bash
   ./scripts/calibrate-task.sh tasks/my-new-task \
     --commit "$TASK_CODE_COMMIT" \
     --env-file .env \
     --self-check
   ```
   The script reads the agent, model, and attempt count from `calibration-target.json` (override with `--target <path>`) and writes `tasks/my-new-task/calibration/self-check.json`, marked `"authoritative": false`. **`calibration/results.json` is reserved for Askable's authoritative run** — keeping them apart matters, because `validate-submissions.sh` binds every attestation to the commit recorded in `results.json`, so a self-check written there at a different commit fails validation for no good reason. A self-check outside the band is reported without failing the command: it is information to act on, not a verdict. The task is eligible only if the number of successful attempts falls inside the target's `min_success`–`max_success` band. Inspect agent trajectories with `harbor view ./jobs`.
6. Commit the completed attestations — plus your self-check calibration results — in a second, immutable submission commit:
   ```bash
   git add tasks/my-new-task/attestations tasks/my-new-task/calibration 2>/dev/null || git add tasks/my-new-task/attestations
   git commit -m "Add submission records for my-new-task"
   ```
   Keep all required task files and both commits in your private repository. This two-commit flow avoids an impossible self-reference: a file inside a Git commit cannot contain that same commit's SHA.

## Share your work

Two equivalent routes:

- **Collaborator access (preferred):** add `@xicovarisco` as a read collaborator on your private repository. We review the tasks and the commit history in place.
- **Export:** package a single task, with a checksummed manifest, into an archive:
  ```bash
  ./scripts/export-task.sh tasks/my-new-task
  ```
  The archive lands in `./exports/`. Submitting without a calibration file is normal — Askable runs the authoritative calibration and adds the results; the export just carries a reminder that acceptance still depends on it.

## Quality checklist

- [ ] The instruction is unambiguous, hand-written per the AI policy, and tests verify only its stated behavior.
- [ ] `task.toml` has an approved category and non-empty primary-language list.
- [ ] `metadata.ai_tools_used` lists every AI tool used on the task (or `[]`).
- [ ] Oracle validation earns reward `1`.
- [ ] The task carries at least two traps for plausible-but-wrong approaches (`AUTHORING.md` §2).
- [ ] `provenance.json` accounts for every third-party material item.
- [ ] Every contributor has completed an attestation.
- [ ] The task's calibration result lands inside the eligibility band in `calibration-target.json`.
- [ ] Any author self-check is committed as `calibration/self-check.json`, not `calibration/results.json`.
- [ ] Verifier **code** lives in `tests/`; verifier **tooling** is either baked into the image at build time or vendored next to the tests and installed offline. Network access in `test.sh` is a defect.
- [ ] `test.sh` never lets the test runner trust the agent's cwd: Harbor starts the verifier in the image `WORKDIR` (`/app`), and `python3 -m pytest` puts that cwd first on `sys.path`, so a stray `/app/json.py` left by the agent would be imported in place of the stdlib and could forge the reward. Use `cd /tests && python3 -P -m pytest -p no:cacheprovider test_outputs.py`, and run any other runner from `/tests` too (`AUTHORING.md` §7).
- [ ] `network_mode` is `"no-network"`, or `metadata.network_justification` explains why the task cannot run offline. Runtime (agent and verifier) has no network; dependencies are installed into the image at **build** time, where network is expected.
- [ ] The environment installs `tmux` (and `asciinema`) at build time — the calibration agent cannot start without them on an offline runtime.
- [ ] The environment has `git` initialized at the intended base state, with no history that leaks the solution or any future state.
- [ ] `git status --ignored` shows nothing under your task directory — a gitignore rule that reaches into `tasks/` drops files from the commit while leaving them on your disk, so the task passes locally and arrives incomplete.
- [ ] No secrets are committed and network access is declared explicitly.

## Local template checks

Requires Python 3.11+ (for `tomllib`); the pinned version is in `.python-version`.

```bash
python3 -m unittest discover -s tests -v
./scripts/validate-submissions.sh
./scripts/validate-all.sh
```

## Reference

- [AUTHORING.md](AUTHORING.md) — how to design a task worth paying for
- [DIFFICULTY.md](DIFFICULTY.md) — the acceptance bar
- [CONTEXT.md](CONTEXT.md) — core concepts and vocabulary
- [docs/execution-model.md](docs/execution-model.md) — how `solution/`, `tests/`, and the agent's work interact with the environment
- [Harbor task structure](https://www.harborframework.com/docs/tasks)
- [Harbor task tutorial](https://www.harborframework.com/docs/tasks/task-tutorial)
- [Terminal-Bench](https://www.tbench.ai/)
