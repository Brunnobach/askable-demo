# Difficulty Standard

This is Askable's acceptance bar for task difficulty. It overrides any looser difficulty language elsewhere in this repository. `AUTHORING.md` explains how to design to it.

## How difficulty is measured

Each frozen task is run **10 times** by the designated calibration agent and model — currently `terminus-2` with `gemini/gemini-3.8-flash`, as pinned in `calibration-target.json`. The number of passing attempts out of 10 is the task's difficulty measurement.

## The acceptance distribution

Across a delivered set of tasks:

| Passing attempts out of 10 | Share of delivered tasks |
|---|---|
| 0–4 | ≥ 80% |
| 5–6 | ≤ 20% |
| 7–10 | **0% — automatic rejection** |

The distribution applies at both the task level and the dataset level. A single task landing at 7+ is rejected no matter how well it is built.

## Eligibility band for an individual task

`calibration-target.json` sets the per-task band: **1–4 successes out of 10**.

- A task at 5–6 consumes scarce allowance and is usually returned for deepening.
- A task at **0/10 is not accepted automatically** — it is held for human review, because a task the model never solves may be broken or unfair rather than hard.

## Design for ~2 passes in 10 — and mind the noise

Ten attempts is a small sample. A task whose *true* pass rate is 50% has roughly a **1-in-6 chance of observing 7+ passes** and being auto-rejected, and a roughly 45% chance of landing in the 5–6 band. The safe target is a true pass rate around **0.20–0.25** — the model genuinely solves it about 2 attempts in 10. At that level, auto-rejection risk is under 1% and the 5–6 band stays what it should be: buffer for sampling noise, not something you spend.

Practical reading: if your local agent runs (see `AUTHORING.md` §8) show the agent succeeding half the time, the task is not close — it is structurally at risk.

## What a self-check can and cannot tell you

A handful of local runs is a **kill screen, not a measurement**, and the asymmetry is worth understanding before you read anything into the result.

Probability of each outcome from a 3-attempt self-check, by the task's true pass rate:

| True pass rate | 0/3 | 1/3 | 2/3 | 3/3 | Expected at 10 attempts |
|---|---|---|---|---|---|
| 0.10 | 72.9% | 24.3% | 2.7% | 0.1% | 1/10 — in band |
| 0.20 | 51.2% | 38.4% | 9.6% | 0.8% | 2/10 — in band, the target |
| 0.25 | 42.2% | 42.2% | 14.1% | 1.6% | 2/10 — in band |
| 0.40 | 21.6% | 43.2% | 28.8% | 6.4% | 4/10 — top of band |
| 0.50 | 12.5% | 37.5% | 37.5% | 12.5% | 5/10 — **returned** |
| 0.70 | 2.7% | 18.9% | 44.1% | 34.3% | 7/10 — **rejected** |
| 0.80 | 0.8% | 9.6% | 38.4% | 51.2% | 8/10 — **rejected** |

Two readings follow, and only one of them is good news.

**`0/3` means almost nothing.** It is the single most likely outcome for a correctly calibrated task at p=0.20 — and it still happens one time in eight for a task at p=0.50 that will be returned at ten attempts. A zero cannot separate "well designed" from "structurally too easy and I got lucky". Do not submit on the strength of one.

**`3/3` is the only outcome carrying real information.** At the design target it happens under 1% of the time, and at p=0.80 it happens half the time. If the agent sweeps your self-check, the task is too easy. Stop and deepen it.

So the rule is: **a self-check can tell you to stop. It can never tell you that you are done.** Five or more attempts sharpens the picture a little; separating p=0.20 from p=0.50 with any confidence takes roughly twenty, which is more than this step is worth. Askable's ten-attempt run is the measurement. Do not let self-checking eat your build budget.

## Fair versus unfair difficulty

Difficulty must come from the problem being genuinely hard — never from information the agent could not have had.

- **Encouraged:** traps for plausible-but-wrong approaches (minimum two per task); precise behavioural contracts; forced investigation of the environment; hostile-but-stated edge cases.
- **Automatic rejection:** any hidden test checking a requirement the instruction never stated.
- **The human test:** an experienced engineer reading only the instruction and exploring the environment must be able to produce a fully correct solution. We verify this with an independent human solver before calibration.

## Who runs what, and whose credentials

- **You** validate the oracle and self-check difficulty with local Harbor agent runs (`terminus-2` by default; `antigravity` or `gemini-cli` for a Gemini-flavoured pass).
- **Askable's calibration lead** runs the authoritative 10-attempt calibration against `calibration-target.json`. You do not need model API access for acceptance.

**Self-checks run on your own credentials, never on Askable's.** `gemini-3.8-flash` is available on the free tier of Gemini CLI and Antigravity, which is enough for a kill screen and costs nothing. Askable does not issue shared API keys: a shared key has no per-author spend limit, makes runs unattributable, and would put your disclosed self-check beyond reconciliation. If free-tier access is genuinely unavailable to you, say so at proposal and Askable will run the screen instead.

Keep your key in a gitignored `.env` (`.env.example` shows the shape). A key committed to your task repository is a rejection, and we read the commit history.
