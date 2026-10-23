# Contributing a Terminal Task

This repository is source-available under the `LICENSE`; it is not an open-source project. Before creating a task, sign the Askable participant agreement, clone this repository, and do all your work in your own **private** GitHub repository created from it.

## AI-use policy

You may use AI coding agents (Claude Code, Codex CLI, Cursor, Antigravity, and similar) to help build the environment, the tests, and the reference solution. We expect you to — fluency with these tools is part of why you were selected.

Three conditions are absolute:

1. **You own every line.** You must personally verify every file in the task and be able to explain and defend each decision in a live 30-minute walkthrough. "The agent wrote it and it passed" is a failing answer. Work you cannot defend is treated as unverified and rejected.
2. **The instruction is yours.** `instruction.md` must be hand-written, or edited so heavily that every requirement is your own. Pasted AI-generated instructions have a recognisable signature and are rejected on sight (see `AUTHORING.md` §3).
3. **Disclose your tools.** List every AI tool used on the task in `metadata.ai_tools_used` in `task.toml` (e.g. `["claude-code", "cursor"]`; use `[]` if none). The automated checks validate the field's format.

Your private repository's incremental commit history — including the dead ends — is part of how we verify this. A single giant commit is a red flag regardless of how the work was produced.

Every contributor must complete `tasks/<task>/attestations/<github-handle>.md` against the task-code commit. The attestation affirms the conditions above, authority to contribute the material, and assignment of all contribution rights to Askable.

## Third-party material and provenance

Create or update `tasks/<task>/provenance.json` for every third-party dependency, code sample, dataset, binary, and fixture. Each item requires:

- name
- source URL or origin
- license
- version or content hash
- explanation of why its license or permission permits Askable's intended AI-training use

Use an empty `third_party_material` array only when no third-party material is included. Do not include anything whose rights are uncertain.

## Submission process

1. Write the task (see `AUTHORING.md`) and confirm the oracle solution earns reward `1`.
2. Set an approved category, a non-empty primary-language list, and `ai_tools_used` in `task.toml`.
3. Commit task code and provenance. Save that SHA as `TASK_CODE_COMMIT`.
4. Complete all contributor attestations using `TASK_CODE_COMMIT`.
5. Self-check difficulty with local Harbor agent runs before submitting, on your own credentials (`terminus-2`, `antigravity`, or `gemini-cli` — see `AUTHORING.md` §8; `DIFFICULTY.md` explains what the result can and cannot tell you). We expect this — an out-of-band submission costs a full review round-trip. Commit the result as `calibration/self-check.json` (`calibrate-task.sh --self-check`); `calibration/results.json` is reserved for the authoritative run Askable performs against `calibration-target.json`. Record what you actually ran — agent, model, attempt batching, and any environment workaround — so we can reconcile your number with ours when they differ.
6. Run local checks:

   ```bash
   python3 -m unittest discover -s tests -v
   ./scripts/validate-submissions.sh
   ./scripts/validate-all.sh
   ```

7. Keep all task files, attestations, both commits, and your self-check calibration results in your private repository, then either add `@xicovarisco` as a read collaborator or send the archive produced by `./scripts/export-task.sh tasks/<task>`. Submitting without calibration results is normal — Askable runs the authoritative calibration.
