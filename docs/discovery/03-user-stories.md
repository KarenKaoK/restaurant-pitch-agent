# 03 — User Stories: Restaurant Pitch Agent (Prototype)

| | |
|---|---|
| **Phase** | User Discovery |
| **Date** | 2026-11-25 |
| **Builds on** | [`01-business-research.md`](01-business-research.md), [`02-user-discovery.md`](02-user-discovery.md) |
| **Status** | Draft for human review |

## Notes

- **Primary user:** the field sales representative selling DISH products to restaurants (persona in doc 02 §1). "Sales rep" below means this persona.
- **All stories are hypotheses [H].** They come from public job postings and project assumptions, not from interviews with DISH or METRO sales staff. They should be validated using the methods in doc 02 §7.
- **No technical implementation** is implied. Stories describe what the user needs, not how it is built.
- **Priority (MoSCoW) for the prototype:**
  - **Must:** without it, the prototype doesn't show its core value.
  - **Should:** important. Include if feasible.
  - **Could:** nice to have. Only if time allows.
  - **Won't (this prototype):** explicitly out of scope. Recorded for later.
- **Links:** each story references the pain points (P-x), needs (N-x) and responsibilities (R-x) in doc 02.

---

## Prototype data scope

The prototype uses a **predefined offline dataset** of restaurant information and customer reviews.

Its main goal is to show three things: AI-powered review analysis, product recommendations backed by evidence, and personalised sales cards.

**Out of scope for this prototype:** live Google Maps integration, automatic review collection, and ongoing data updates (see US-W7).

**Implications:**

- **Selecting a restaurant (US-01)** means choosing one from the dataset, not searching any restaurant live.
- **Recency (US-04)** is measured from the date the dataset was collected, not from today. Every sales card should show that date.
- **Data provenance:** how the dataset's reviews were obtained, and whether they may be used, must be documented. Terms of service and data protection still apply to an offline dataset (doc 02, assumption A-9).
- **Future extensibility (requirement level only):** later it should be possible to replace the offline dataset with a live data source without changing what the sales rep sees on the sales card. *How* this is achieved belongs to the Technical Design phase.

---

## Epic A — Restaurant insight from reviews

| ID | User story | Business value | Priority | Links |
|---|---|---|---|---|
| US-01 | As a sales rep, I want to **select a specific restaurant and get an analysis of its customer reviews** *(prototype: chosen from the predefined dataset)*, so that I don't have to read dozens of reviews myself before a visit. | Cuts prep time per visit. More time for selling and for the ≥20 weekly appointments. | **Must** | P-1, P-5, P-8, N-1, R-1 |
| US-02 | As a sales rep, I want to **see the restaurant's likely operational pain points as a short list**, so that I can grasp the situation in under a minute. | Faster, more focused preparation. | **Must** | P-1, N-1 |
| US-03 | As a sales rep, I want **each pain point backed by direct quotes from real reviews**, so that I can check the claim myself and show the owner credible evidence. | Builds trust with the owner. Lowers the risk of unsupported claims (P-7). | **Must** | P-2, P-7, N-2, R-4 |
| US-04 | As a sales rep, I want to **see how often and how recently each pain point is mentioned** *(prototype: recency measured from the dataset's collection date)*, so that I can tell a recurring problem from a one-off complaint. | Avoids pitching on noise. Focuses on real, current problems. | **Should** | P-7, N-6 |
| US-05 | As a sales rep, I want the analysis to **cover reviews in the local language (German) and other common languages**, so that I don't miss evidence written in another language. | Fuller evidence base in a German-speaking market. | **Should** | P-8 |

## Epic B — Product matching

| ID | User story | Business value | Priority | Links |
|---|---|---|---|---|
| US-06 | As a sales rep, I want **one or two recommended DISH products matched to the identified pain points**, so that I lead with the most relevant solution instead of the whole catalogue. | Higher relevance per conversation. Easier for reps with less product knowledge. | **Must** | P-2, P-3, N-3, R-4 |
| US-07 | As a sales rep, I want each recommendation to **explain which pain point and evidence it addresses**, so that I understand *why* the product is suggested and can explain it to the owner. | Transparent reasoning that reps can check and repeat. | **Must** | P-3, P-7, N-2, N-3 |
| US-08 | As a sales rep, I want recommendations to **respect product prerequisites, country availability and restaurant type**, so that I never pitch something the restaurant can't buy or doesn't need. | Prevents embarrassing or invalid offers (e.g. a pilot-only product, an add-on without its base product, reservations for a walk-in snack bar). | **Must** | P-3, N-3 |
| US-09 | As a sales rep, I want to **see when pain points together suggest a bundle**, so that I can present a combined offer where it fits. | Larger deal size where evidence supports it. | **Could** | R-8 |

## Epic C — Sales card for the conversation

| ID | User story | Business value | Priority | Links |
|---|---|---|---|---|
| US-10 | As a sales rep, I want a **one-page sales card** that combines summary, pain points, evidence, recommended products, talking points and questions, so that I have everything I need for the visit in one place. | One consistent artifact to prepare with. Reduces scattered research. | **Must** | P-1, P-5, N-1, N-7 |
| US-11 | As a sales rep, I want **suggested talking points worded in a respectful, guest-perspective way** (e.g. "several guests mention…"), so that I can open the conversation without seeming to criticise the owner. | Stronger cold opener with less defensiveness from the owner. | **Must** | P-4, N-4, R-2 |
| US-12 | As a sales rep, I want **suggested discovery questions** to confirm or reject each pain point with the owner, so that I check assumptions instead of presenting them as facts. | Better qualification. Treats the analysis as a hypothesis, not a verdict. | **Must** | P-7, N-5, R-2 |
| US-13 | As a sales rep, I want the card to be **readable on a phone**, so that I can prepare in the car or between visits. | Fits the mobile, on-the-road work pattern (to be validated, A-5). | **Should** | P-1, N-7 |
| US-14 | As a sales rep, I want to **copy or export the card content as plain text**, so that I can paste it into my notes or the internal sales tool. | Supports required activity documentation without integration work. | **Should** | P-6, N-7, R-7 |

## Epic D — Trust and reliability

| ID | User story | Business value | Priority | Links |
|---|---|---|---|---|
| US-15 | As a sales rep, I want to **see a confidence level for each pain point and recommendation**, so that I know how much weight to give it. | Prevents overclaiming. Builds justified trust. | **Must** | P-7, N-6 |
| US-16 | As a sales rep, I want the agent to **say clearly when there is not enough evidence** instead of guessing, so that I'm never misled into a wrong pitch. | Protects credibility with restaurant owners. | **Must** | P-7, N-6 |
| US-17 | As a sales rep, I want to be sure that **product descriptions on the card match official DISH product information**, so that I never promise features that don't exist. | Avoids misinformation and broken promises. | **Must** | P-7, N-3 |
| US-18 | As a sales rep, I want to **mark a pain point or recommendation as useful or not useful**, so that the quality of the cards can be measured and improved. | Provides input for the AI Evaluation phase and continuous improvement. | **Could** | R-5 |

## Epic E — Feedback and handover

| ID | User story | Business value | Priority | Links |
|---|---|---|---|---|
| US-19 | As a sales rep, I want to **add my own notes from the visit** to the card (e.g. which pain points the owner confirmed), so that the insight isn't lost after the conversation. | Captures validated insights for follow-up and inside sales. | **Could** | P-6, R-5, R-6 |

## Won't have (this prototype) — recorded for later

| ID | User story | Reason for deferral |
|---|---|---|
| US-W1 | As a sales rep, I want **cards for all restaurants in my territory ranked by opportunity**, so that I can plan my route around the most promising prospects. | Territory-wide lead scoring adds scope and data volume. Single-restaurant cards first. |
| US-W2 | As a sales rep, I want cards **synced automatically into the internal sales tool / CRM**, so that I don't copy anything by hand. | That tool is unknown (doc 02 §8, Q3). Integration is out of scope. |
| US-W3 | As a sales rep, I want to **know which DISH products a restaurant already uses**, so that I pitch an upsell rather than a duplicate. | Needs internal customer data that isn't publicly available. |
| US-W4 | As a sales rep, I want **price quotes generated** for the recommended products, so that I can close on the spot. | Prices vary by country and change. Quoting is a separate process. |
| US-W5 | As a sales manager, I want **aggregated pain-point trends across my team's territories**, so that I can steer sales focus and give product feedback. | Secondary user. Needs multi-restaurant data. |
| US-W6 | As a sales rep, I want the agent to **contact the restaurant for me** (email/message), so that outreach is automated. | Outward-facing automation is a compliance and reputational risk. The rep stays in control. |
| US-W7 | As a sales rep, I want **any restaurant's latest reviews fetched live** (e.g. from Google Maps) and kept up to date, so that every card reflects current guest feedback. | The prototype uses a predefined offline dataset (see "Prototype data scope"). Live collection and continuous updates are deferred. |

---

## Priority summary

| Priority | Stories |
|---|---|
| **Must** (12) | US-01, US-02, US-03, US-06, US-07, US-08, US-10, US-11, US-12, US-15, US-16, US-17 |
| **Should** (4) | US-04, US-05, US-13, US-14 |
| **Could** (3) | US-09, US-18, US-19 |
| **Won't (this prototype)** (7) | US-W1 – US-W7 |

**Proposed minimum prototype scope [H]:** for one restaurant selected from the predefined offline dataset, in one market (Germany), produce an evidence-backed sales card (US-01 – 03, 06 – 08, 10 – 12) with built-in trust safeguards (US-15 – 17). Everything else can come after validation.

## Questions for reviewers

1. Is the field sales rep the right primary user, or should inside sales be considered too?
2. Do you agree with the Must set? It is intentionally kept small.
3. Should US-05 (multi-language) become a Must, given that the target market is German-speaking?
4. Is it acceptable to defer upsell scenarios (US-W3), so that the prototype focuses on **new-customer acquisition**?
