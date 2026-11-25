# restaurant-pitch-agent

An AI agent that helps sales reps prepare restaurant visits by reading public reviews and recommending products from a fixed DISH product catalog. Personal learning project to practice spec-driven development with Spec Kit.

## Language
- 用繁體中文回覆我
- All files (specs, code, comments, docs, commit messages) must be written in English

## Workflow
- Follow the Spec Kit flow: constitution → specify → clarify → plan → tasks → analyze → implement
- Do not add features or behavior that are not in the spec and tasks
- If the spec is unclear or conflicts with the code, ask me instead of guessing
- Implement tasks phase by phase. At each checkpoint in tasks.md, run all tests, then stop and wait for my review
- At each checkpoint, propose a commit message that references the task IDs (e.g. "feat: add review loader (T003-T005)")
- If behavior needs to change, update the spec first, then the code, and log the change in docs/spec-changes.md


## Key files
- Constitution: .specify/memory/constitution.md
- Discovery notes: docs/discovery/
- Product catalog: data/products/
- Raw reviews: data/raw/duesseldorf_reviews.csv (never modify)

## Security
- Never read, print or write the contents of .env
- Never put API keys or tokens in any file, command or commit
