# restaurant-pitch-agent

An AI agent that helps sales reps prepare restaurant visits by reading public reviews and recommending products from a fixed DISH product catalog. Personal learning project to practice spec-driven development with Spec Kit.

## Language
- 用繁體中文回覆我
- All files (specs, code, comments, docs, commit messages) must be written in English

## Workflow
- Follow the Spec Kit flow: constitution → specify → clarify → plan → tasks → analyze → implement
- Do not add features or behavior that are not in the spec and tasks
- If the spec is unclear or conflicts with the code, ask me instead of guessing
- Implement tasks phase by phase, each phase on its own branch with a PR to main; I merge, never merge yourself
- Before implementing a phase, list the unhappy inputs at every external boundary the phase touches (environment variables, CLI options, HTTP calls, files read or written): wrong format, empty, missing, out of range, interrupted or partial. `/speckit-checklist` can help. Each case needs a test; if the spec or contracts do not say what should happen, ask me, then update the spec or contract before writing the test
- At each checkpoint in tasks.md, before proposing the commit:
  1. Run all tests
  2. Run `/code-review` on the phase's changes against main. Reproduce each finding before fixing it; fix confirmed findings test-first with a regression test. Report findings that were not fixed and why
  3. Run all tests again
  Then stop and wait for my review
- At each checkpoint, propose a commit message that references the task IDs (e.g. "feat: add review loader (T003-T005)")
- If behavior needs to change, update the spec first, then the code, and log the change in docs/spec-changes.md. When wording in the spec or a contract changes, search all documents under specs/ and the code for the old wording and update every place


## Key files
- Constitution: .specify/memory/constitution.md
- Discovery notes: docs/discovery/
- Product catalog: data/products/
- Raw reviews: data/raw/duesseldorf_reviews.csv (never modify)

## Security
- Never read, print or write the contents of .env
- Never put API keys or tokens in any file, command or commit
