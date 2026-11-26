# Restaurant Pitch Agent Constitution

## Core Principles

### I. Evidence-Grounded Output

- Every pain point the agent reports MUST cite at least one review from the input dataset as
  evidence, identified by its review ID.
- Quoted evidence MUST be a verbatim excerpt of the `text` field of the cited review in
  `data/processed/reviews.csv`. The agent MUST NOT invent, paraphrase as a quote, or merge
  reviews into a single quote.
- Every piece of evidence on a sales card MUST show the review's `text_source`
  (`original`, `translated` or `expanded`), so the rep knows whether the quote is the guest's
  own wording.
- A pain point or recommendation that cannot be traced to stored review evidence MUST NOT
  appear on a sales card.
- Talking points MUST be worded from the guest's perspective (e.g. "several guests mention…"),
  not as an accusation of the owner.

**Rationale:** The sales card is only useful if the rep and the restaurant owner can verify
every claim. Unsupported claims damage the rep's credibility (discovery doc 02, P-7).

### II. Catalog Fidelity

- The agent MUST recommend only products defined in the project catalog (`data/products/`).
  It MUST NOT recommend, name or describe products, features or prices that are not in it.
- Product descriptions on a sales card MUST be consistent with the catalog's "Official facts".
  Project-authored sales notes MUST NOT be presented as official DISH facts.
- Recommended products MUST be identified by the `product_id` in their catalog frontmatter.
- Recommendations MUST respect the prerequisites and product limits recorded in the catalog.
  A recommendation that violates them is a defect. Prerequisites in the frontmatter
  `requires` field are checked deterministically (Principle VI); product limits written as
  text are checked in the human review at each checkpoint.
- v1 does not consider country availability.
- Each recommendation MUST state which pain point(s) and evidence it addresses.

**Rationale:** Promising features that do not exist, or products a restaurant cannot buy,
breaks trust and the sale (US-08, US-17).

### III. Honest Uncertainty

- Every pain point and recommendation MUST carry an explicit confidence level.
- When the evidence does not meet the threshold defined in the spec, the agent MUST say
  "not enough evidence" instead of guessing or filling the card with weak claims.
- Low-confidence findings MUST be presented as discovery questions for the rep, not as facts.
- v1 does not assess review recency. The agent MUST NOT use review dates to infer whether a
  problem is recent, ongoing or resolved.
- The agent MUST NOT recommend any product for the following restaurants, and the sales card
  MUST state the reason no product is recommended:
  - `status` is `closed` (the restaurant has closed);
  - `segment` is `chain` (chain restaurants are outside the target group of independent,
    small and mid-sized restaurants).

**Rationale:** An analysis of public reviews is a hypothesis about the restaurant, not a
verdict. Making uncertainty visible prevents overclaiming (US-15, US-16).

### IV. Human in the Loop

- The agent prepares material for a sales rep. It MUST NOT contact restaurants, send
  messages, or take any outward-facing action.
- The rep is the decision-maker: the sales card MUST be exportable as plain text, and the
  agent MUST NOT present its output as a final decision.
- The agent MAY cite prices and pricing models stated in `data/products/`. It MUST NOT
  calculate quotes, combine prices into an offer, or offer discounts.

**Rationale:** Outward automation is a compliance and reputational risk (US-W6). The rep owns
the customer relationship and the final judgement.

### V. Data Integrity and Privacy

- The agent's inputs MUST come only from `data/processed/reviews.csv`,
  `data/processed/restaurants.csv` and `data/products/`. The agent MUST NOT read anything in
  `data/raw/` or `data/eval/`. Labels and ground truth in `data/eval/` are used only for
  evaluation.
- Raw input data in `data/raw/` is read-only. Code and tooling MUST NOT modify it; processed
  data MUST be written to `data/processed/` and be reproducible from the raw file.
- The system MUST NOT store, display or log reviewer identity data (name, profile URL,
  reviewer ID, photo, reviewer statistics).
- Every review MUST keep its `platform` and `source_url`.
- Secrets MUST NOT appear in any file, command output, log or commit. AI assistants used
  for development MUST NOT read, print or write `.env`. The application MUST read API keys
  only from environment variables and MUST NOT print keys to the screen or write them to logs.

**Rationale:** Reviews can be personal data under GDPR, and this is a public repository.
Immutable raw data keeps every result traceable to its source.

### VI. Tested and Reproducible

- Deterministic logic (data loading, validation, catalog rules, evidence checks, card
  formatting) MUST be developed test-first (TDD): write the test, confirm it fails, write just
  enough code to make it pass, then refactor.
- In `tasks.md`, the test task for each deterministic feature MUST come before its
  implementation task.
- LLM-generated output is not developed with TDD. It is verified by the evaluation (labelled
  cases and deterministic checks) described below.
- All tests MUST pass at every task-phase checkpoint.
- The evaluation MUST be runnable with a single command.
- Deterministic checks MUST pass on every generated sales card:
  - the output format is valid;
  - every cited review exists, and every quote is a verbatim excerpt of that review's `text`
    field;
  - every cited review has the same `restaurant_id` as the sales card's restaurant;
  - every recommended product exists in `data/products/`;
  - every recommended product whose frontmatter has a `requires` field is recommended
    together with the required product;
  - a sales card for a restaurant whose `status` is `closed` or whose `segment` is `chain`
    contains no product recommendations.
- Product limits written as text in `data/products/` are not checked automatically. They are
  checked in the human review at each task-phase checkpoint.
- The evaluation MUST report recommendation accuracy on the labelled cases.
- In v1, each evaluation case is run exactly once.
- Each evaluation run MUST record the git commit and the model name.

**Rationale:** LLM output varies between runs. Automated evidence and catalog checks catch
hallucinations that manual review can miss, and recorded inputs make results comparable.

## Scope and Data Constraints

- The prototype works on a predefined offline dataset of restaurants and reviews. Live review
  collection, CRM integration, route planning, territory-wide lead scoring, price quotes and
  review-recency assessment are out of scope unless a spec explicitly adds them.
- The target market is Germany. All review data in `data/processed/` is in English, so the
  agent does not handle translation. All project files are written in English.
- The product catalog in `data/products/` is the single source of truth for products. Changing
  the catalog is a data change and MUST be committed separately from code changes.
- Features, behaviour and dependencies MUST NOT be added unless they are in the current spec
  and tasks. Prefer the simplest design that satisfies the spec.

## Development Workflow

- Work follows the Spec Kit flow: constitution → specify → clarify → plan → tasks → analyze →
  implement.
- Implementation proceeds phase by phase as defined in `tasks.md`. At each checkpoint all tests
  MUST be run, and work MUST stop for human review before the next phase begins.
- Each checkpoint proposes a commit message that references the task IDs it covers
  (e.g. `feat: add review loader (T003-T005)`).
- If the spec is unclear or conflicts with the code, the implementer MUST ask the project owner
  instead of guessing.
- Behaviour changes follow the order: update the spec, then the code, then log the change in
  `docs/spec-changes.md`.
- Every plan MUST include a Constitution Check that confirms compliance with each principle or
  documents a justified exception.

## Governance

- This constitution supersedes other project practices. Where `CLAUDE.md` or other guidance
  conflicts with it, the constitution wins until it is amended.
- Amendments are made with `/speckit-constitution`, reviewed by the project owner, and
  committed with a message that states the new version.
- Versioning follows semantic versioning:
  - MAJOR: a principle is removed or redefined in a backward-incompatible way.
  - MINOR: a principle or section is added, or guidance is materially expanded.
  - PATCH: clarifications and wording fixes with no change in meaning.
- Compliance is reviewed at three points: the Constitution Check in each plan, the
  `/speckit-analyze` step before implementation, and the human review at each task-phase
  checkpoint. Violations found there MUST be fixed or recorded as justified exceptions in the
  plan.

**Version**: 1.0.0 | **Ratified**: 2026-11-25 | **Last Amended**: 2026-11-25
