# 02 — User Discovery: DISH Sales Representatives

| | |
|---|---|
| **Phase** | User Discovery |
| **Research date** | 2026-11-25 |
| **Builds on** | [`01-business-research.md`](01-business-research.md) |
| **Status** | Draft for human review |

## Scope and evidence labels

This document describes the people the Restaurant Pitch Agent is for: the sales representatives who sell DISH products to restaurants. It is based only on public sources. **No DISH or METRO employee was interviewed.** None of the workflows below should be read as DISH's actual internal process.

- **[F] Verified fact:** stated in an official DISH or METRO source (e.g. `dish.co`, `karriere.metro.de`, DISH's own job postings), read on 2026-11-25.
- **[F-3P] Fact from a third-party copy:** text of an official METRO/DISH job posting, read on a job board that republishes it. The wording is attributed to the employer, but the original could not be loaded.
- **[H] Hypothesis:** project-team inference. Not stated by DISH or METRO. Must be validated.

### Research note: who employs DISH's field sales reps

The public field-sales postings for DISH products are advertised by **METRO Deutschland Consulting GmbH** (METRO's German organisation), not by DISH Digital Solutions GmbH [F: R1; F-3P: R2]. The METRO career page calls the field rep "das Gesicht von DISH in Ihrem Gebiet" ("the face of DISH in your area") [F: R1]. In this document, "DISH sales representative" means anyone whose job is selling DISH products to restaurants, whatever their legal employer.

On the research date, DISH's own job portal had no open sales roles [F: R4]. Search results show earlier DISH postings for a Country Manager (Germany, Italy) and a Sales Enablement Specialist, but those pages returned 404 or 403 and could not be read [see §9].

---

## 1. Primary user persona

### "Field Digital Sales Manager" (Außendienst)

> *A composite persona. The facts come from public job postings (R1, R2). The personal details are illustrative [H].*

| Attribute | Description | Basis |
|---|---|---|
| Role title | Digital Sales Manager / Sales Manager Außendienst (field sales) for restaurant solutions | [F] R1, [F-3P] R2 |
| Employer | METRO Deutschland Consulting GmbH, selling DISH products | [F] R1, [F-3P] R2 |
| Territory | Owns a regional territory in Germany; plans their own tours; ideally lives in the territory | [F] R1, [F-3P] R2 |
| Customers | Restaurant owners ("Gastronomen"): new prospects and existing METRO customers | [F] R1 |
| Products presented | DISH Website, DISH reservation tool, DISH Order shop system, DISH POS; payment solutions are in some postings | [F] R1, [F-3P] R2 |
| Background | Sales experience, "gerne aus dem Bereich Gastronomie, Versicherungen, Online Marketing, Payment, Telekommunikation" (ideally from gastronomy, insurance, online marketing, payment or telecoms) | [F] R1, [F-3P] R2 |
| Work style | "strukturierte, selbstständige Arbeitsweise ist ein Muss" (a structured, independent way of working is a must); on the road a lot; company car | [F] R1, [F-3P] R2 |
| Pay | Bonus model tied to sales success and target achievement | [F] R1, [F-3P] R2 |
| Working partners | Inside sales ("Vertriebsinnendienst"), METRO field sales colleagues, product development team, coaches / "House of Learning" | [F] R1, [F-3P] R2 |
| Language | German-speaking market; most restaurant reviews in the territory are probably in German | [H] |
| Tech comfort | "gutes digitales Verständnis" (good digital understanding); works from a laptop or phone between visits | [F] R1 (first part), [H] (second part) |

**Illustrative profile [H]:** *Lena, 29, covers a territory in and around Düsseldorf. She visits 4–6 restaurants a day and prepares in the car park or the evening before. With so many DISH products, add-ons and bundles, she isn't always sure which one or two fit a given restaurant best.*

### Secondary users (out of scope for the prototype, noted for later)

| User | Why relevant | Basis |
|---|---|---|
| Inside sales (Digital Inside Sales Manager) | Forms "ein starkes Duo" (a strong duo) with field sales; may book appointments or qualify leads | [F] R1 |
| Sales leadership / enablement | DISH has advertised Sales Enablement and Country Manager roles; they could use aggregated insights | [F] search result titles only (see §9); details [H] |
| Product team | Receives structured field feedback from reps | [F] R1, [F-3P] R2 |

---

## 2. User responsibilities

### 2.1 Stated in public postings [F / F-3P]

| # | Responsibility | Source wording (German → English) | Source |
|---|---|---|---|
| R-1 | **Customer visits and territory management** | "Sie planen Ihre Touren eigenverantwortlich und bauen sich einen Kundenstamm in Ihrem Gebiet auf." (You plan your tours independently and build a customer base in your area.) | R1 |
| R-2 | **New-customer acquisition**, including cold acquisition | "Sie begeistern neue Gastronomen für unsere digitalen DISH Lösungen." (You get new restaurateurs excited about our digital DISH solutions.) Also "Kaltakquise" (cold acquisition) | R1 |
| R-3 | **Developing existing METRO customers** | "Sie beraten bestehende Kunden der METRO individuell zu unseren digitalen Produkten" (You advise existing METRO customers individually on our digital products.) | R1 |
| R-4 | **Product consultation** | Present DISH Website, reservation tool, Order shop system, POS "und zeigen ihren Nutzen auf" (and show their benefits) | R1, R2 |
| R-5 | **Structured feedback to the product team** | "Sie sammeln Rückmeldungen aus der Praxis und geben diese strukturiert an unser Produktteam weiter." (You collect practical feedback and pass it on in a structured way to the product team.) | R1, R2 |
| R-6 | **Teamwork with inside sales and METRO field sales** | "Gemeinsam mit dem Vertriebsinnendienst bilden Sie ein starkes Duo." (Together with inside sales you form a strong duo.) | R1, R2 |
| R-7 | **KPI reporting and activity documentation** | "verbindliche Dokumentation von mindestens 20 wöchentlichen Kundenterminen in unserem internen Sales Tool" (binding documentation of at least 20 weekly customer appointments in the internal sales tool) | R2 |
| R-8 | **Target achievement** | "betriebswirtschaftliche Steuerung der Zielerreichung" (business-management steering of target achievement) | R1, R2 |

### 2.2 Implied responsibilities [H]

- Researching each restaurant before a visit (online presence, current tools, reputation).
- Choosing which of many DISH products to lead with for each restaurant.
- Handling objections (cost, contract length, "I already use a platform").
- Logging visit outcomes and follow-ups in the internal sales tool.

---

## 3. Potential pain points

All pain points here are **hypotheses [H]**. Each is linked to the public fact that suggests it. None has been confirmed with a sales rep.

| # | Pain point [H] | Why we suspect it (linked fact) | Severity guess |
|---|---|---|---|
| P-1 | **Little time to prepare per visit.** At 20+ documented appointments a week, plus travel, cold visits and admin, research time per restaurant is short. | ≥20 weekly appointments [F-3P R2]; travel across the territory [F R1] | High |
| P-2 | **Generic pitches.** Without restaurant-specific evidence, reps open with a product tour rather than the owner's actual problem, which lowers engagement. | Postings ask reps to "show the benefits" of four or more products [F R1] | High |
| P-3 | **Product-matching difficulty.** The portfolio is broad (20+ products, add-ons and bundles, with prerequisites and country limits), so picking the right one or two for a restaurant is hard, especially for newer reps. | Portfolio breadth [F: doc 01 §3]; candidates from non-gastronomy backgrounds welcome [F R1] | Medium-High |
| P-4 | **Weak opener in cold acquisition.** A cold visit needs a credible reason to talk; "I sell software" is easy to refuse. | Cold acquisition and new-customer acquisition named as core [F R1] | High |
| P-5 | **Research is scattered.** Google reviews, the Google profile, the website and delivery platforms all have to be checked by hand, often on a phone. | [H] only. No public source | Medium |
| P-6 | **Unstructured insights.** Observations about the restaurant and feedback for the product team are written ad hoc, so they're hard to reuse or hand over to inside sales. | Feedback must be "strukturiert" (structured) [F R1]; inside/field duo [F R1] | Medium |
| P-7 | **Risk of overclaiming.** Under target pressure, a rep may attribute problems to a restaurant without evidence or promise features that don't exist, which damages trust. | Bonus tied to targets [F R1, R2]; [H] behaviour | Medium |
| P-8 | **Language and volume of reviews.** Busy restaurants have hundreds of reviews in several languages, and reading them takes too long. | [H] only | Medium |

---

## 4. User goals and needs

### 4.1 Goals [H, derived from responsibilities R-1 – R-8]

| Goal | Linked responsibility |
|---|---|
| G-1. Open each conversation with something specific and relevant to that restaurant | R-2, R-4 |
| G-2. Recommend the one or two DISH products that best fit, not the whole catalogue | R-4 |
| G-3. Prepare for each visit in minutes, not tens of minutes | R-1, R-7 |
| G-4. Back up every claim with evidence the owner will recognise as true | R-4 |
| G-5. Ask good discovery questions to confirm or reject assumptions | R-2, R-3 |
| G-6. Capture insights in a reusable, shareable form | R-5, R-6, R-7 |
| G-7. Hit targets by focusing on the prospects most likely to need DISH | R-8 |

### 4.2 Needs (what the prototype must provide) [H]

| Need | Serves goals |
|---|---|
| N-1. A short, scannable summary of a restaurant's likely operational pain points, based on its reviews | G-1, G-3 |
| N-2. **Direct quotes from reviews** as evidence for each pain point | G-4 |
| N-3. Product recommendations that respect prerequisites, country availability and segment fit | G-2 |
| N-4. Suggested talking points tied to the evidence, worded without blaming the owner | G-1 |
| N-5. Suggested discovery questions for the visit | G-5 |
| N-6. A clear confidence signal and an explicit "not enough evidence" result | G-4, P-7 |
| N-7. Output that can be read on a phone or copied into notes or the CRM | G-3, G-6 |

---

## 5. Hypothesized current workflow (As-Is)

> **Disclaimer:** This workflow is a **hypothesis** built from public job postings. It does **not** describe DISH's or METRO's actual internal processes, which were not observed.

| Step | Activity | Basis | Hypothesized friction |
|---|---|---|---|
| 1 | **Plan the territory route** and pick which restaurants to visit (existing METRO customers, prospects, leads from inside sales) | [F] tours planned independently, METRO customers, inside-sales duo (R1) | Choosing whom to visit is based on gut feel or lists without pain signals [H] |
| 2 | **Pre-visit research:** look at the restaurant's Google profile, read a sample of reviews, check website and booking/ordering options | [H] | Time-consuming, done on a phone, coverage varies (P-1, P-5, P-8) |
| 3 | **Choose an angle:** decide which DISH product(s) to lead with | [F] present product benefits (R1); choice method [H] | Defaults to a favourite product or a generic tour (P-2, P-3) |
| 4 | **Visit or call:** open the conversation, present products, handle objections | [F] on-site visits, product presentation (R1) | Cold opener is weak (P-4) |
| 5 | **Document** the appointment and outcome in the internal sales tool | [F-3P] ≥20 weekly appointments documented (R2) | Free-text notes, inconsistent structure (P-6) |
| 6 | **Follow up** with inside sales; send product feedback to the product team | [F] R1, R2 | Insights lost between steps (P-6) |

---

## 6. Proposed workflow with the Restaurant Pitch Agent (To-Be)

> This workflow is a **proposal for a prototype**. It does not assume the agent would fit existing DISH tools or processes. It targets steps 2–3 of the As-Is workflow (pre-visit research and choosing an angle) and supports step 5. **The rep stays the decision-maker.** The agent prepares; it does not sell.

| Step | Activity | Change vs. As-Is |
|---|---|---|
| 1 | Rep plans the route as today | Unchanged |
| 2 | Rep **selects a restaurant** (e.g. by name and location) and asks for a sales card | Replaces manual review reading |
| 3 | Agent analyses the restaurant's customer reviews and **identifies likely pain points, each backed by quoted review evidence** | New: structured, evidence-backed |
| 4 | Agent **matches pain points to DISH products**, respecting prerequisites, availability and segment fit, and states its confidence | New: consistent product matching |
| 5 | Agent produces a **sales card**: summary, top pain points + evidence, recommended product(s), talking points, discovery questions, caveats | New |
| 6 | **Rep reviews the card**: checks the evidence, drops or edits anything that doesn't fit, and decides the angle | Human in the loop (keeps P-7 in check) |
| 7 | Rep visits or calls the restaurant, using the card's opener and questions; **validates hypotheses with the owner** | Better-informed conversation |
| 8 | Rep records the outcome and copies relevant card content into notes or the sales tool *(integration out of scope)* | Supports structured documentation |
| 9 | *(Optional, later)* Rep marks whether the recommendation was useful, as an input for evaluation | Feeds the AI Evaluation phase |

**Data scope:** the prototype uses a predefined offline dataset of restaurants and reviews. For details and implications, see [`03-user-stories.md` → Prototype data scope](03-user-stories.md#prototype-data-scope). In step 2, "selects a restaurant" therefore means choosing one from that dataset.

**Out of scope for the prototype [proposed]:** live review collection and data updates, CRM integration, route planning, lead scoring across a whole territory, automatic outreach to restaurants, pricing or quote generation, and inside-sales or management views.

---

## 7. Assumptions and validation methods

| ID | Assumption [H] | Risk if wrong | Validation method | Pass signal |
|---|---|---|---|---|
| A-1 | Reps research restaurants before visits, and that research takes meaningful time | Low value: the agent saves time nobody spends | Interviews with 3–5 hospitality SaaS field reps (DISH/METRO if possible, otherwise comparable companies); ask them to walk through their last prep | Reps describe ≥5 min of prep per visit, or say they skip prep for lack of time |
| A-2 | Guest reviews contain enough operational signals to suggest DISH-relevant pain points | Core value fails | Manually label reviews for a sample of ~20 restaurants against the signal list in doc 01 §5.2 | ≥50% of restaurants show ≥1 signal with ≥2 supporting reviews |
| A-3 | Evidence-backed pitches are more persuasive than generic product tours | The card format isn't valued | Show reps a generic pitch and an evidence-based card side by side; ask which they'd use | Most reps prefer the evidence-based card |
| A-4 | Reps trust AI output only if they can see the sources | Low adoption | Usability test: card with quotes vs. card without; measure trust ratings | Higher trust with quotes |
| A-5 | Reps prepare on a phone or laptop, often between visits | Format mismatch | Interview + contextual question ("where and when do you prepare?") | Confirms mobile/short-format need |
| A-6 | A sales card is useful even when it's partly wrong, as long as the rep can edit or drop items | Errors damage trust | Usability test with deliberately mixed-quality cards | Reps can spot and correct weak items quickly |
| A-7 | German-language reviews dominate in the target market | Language coverage is wrong | Count review languages for a sample of restaurants | Majority German |
| A-8 | Owners respond better to "guests mention X" than to "you have problem X" | Opener feels accusatory | Role-play with reps or hospitality owners; collect qualitative feedback | Preferred wording identified |
| A-9 | Public Google reviews can be used within the platform's terms for this purpose | Legal/compliance blocker | Review terms of service and data-protection requirements before building | Permitted approach documented |

---

## 8. Open questions

**About the real users (to ask DISH/METRO sales, if access is possible):**

1. Who is the actual primary user: DISH-employed sales, METRO Deutschland field sales, inside sales, or METRO store staff?
2. What do reps currently do before a visit, and how long does it take?
3. What is the "internal sales tool"? What does it already show about a restaurant (purchase history at METRO, current DISH products)?
4. Do reps already receive lead lists or customer insights (e.g. from METRO purchase data)?
5. Which products are reps measured on or incentivised to sell? Do incentives favour certain products?
6. Which objections come up most often?
7. Are reps allowed to use AI-generated research in customer conversations? Are there compliance rules?

**About the prototype scope:**

8. Should the prototype support new-prospect acquisition, existing-customer upsell, or both? *(Upsell needs to know which products the customer already has.)*
9. One country (Germany) only, or several?
10. What is the minimum evidence needed before a recommendation is shown?
11. How should "not enough evidence" be shown so the card is still useful (e.g. discovery questions only)?

---

## 9. References

All accessed **2026-11-25**.

| ID | Source | URL | Type | Notes |
|---|---|---|---|---|
| R1 | METRO Karriere — "Jobs im Vertrieb für digitale Lösungen" (DISH field and inside sales) | https://karriere.metro.de/vertrieb_dish | Official (METRO, parent of DISH) | Category page; main source for responsibilities |
| R2 | "Sales Manager Außendienst (m/w/d) für Kassensysteme und Payment Lösungen für die Gastronomie" — METRO Deutschland Consulting GmbH, Hannover | https://vertriebsjobs.com/job/sales-manager-aussendienst-m-w-d-fuer-kassensysteme-und-payment-loesungen-fuer-die-gastronomie-7/ | Third-party copy of official posting [F-3P] | Shown as "posted 63 days ago"; source of the "≥20 weekly appointments" fact |
| R3 | DISH Career page | https://www.dish.co/XX/en/dish-career | Official (DISH) | Culture; "data-driven company within the METRO Growth Plan"; no sales roles listed |
| R4 | DISH job portal (Personio) | https://dishdigital.jobs.personio.de/ | Official (DISH) | On 2026-11-25: only "Senior Data Scientist (AI Engineering)" and an unsolicited-application listing |
| R5 | DISH unsolicited application posting | https://dishdigital.jobs.personio.com/job/1390072 | Official (DISH) | "More than 410.000 restaurateurs across 16 countries"; "Background in SaaS industry or hospitality is advantegous" |
| R6 | DISH "Working Student – Project Management" (DISH Pay), PDF dated 2024-12-03 | https://alumni.wiwi.uni-wuppertal.de/fileadmin/data/Jobb%c3%b6rse/2024/12_Dezember/JD_WS_DISHPAY.pdf | Official DISH document hosted by a university | Confirms DISH Pay is a "growing product" with promotion materials; not a sales role |
| R7 | Business research | [`01-business-research.md`](01-business-research.md) | Project | Product portfolio, segments, review-signal hypotheses |

**Unavailable sources (could not be verified):**

- DISH Country Manager Germany posting: https://dishdigital.jobs.personio.de/job/1762840 (HTTP 404). A search snippet said a "ten-person Sales team" focused on winning local METRO boards for DISH rollouts. **Not verified, not used as fact.**
- DISH Sales Enablement Specialist posting: https://dishdigital.jobs.personio.de/job/2455198 (404) and a third-party copy (403). A search snippet mentioned supporting "international sales teams with tools, processes and insights", including AI-driven solutions. **Not verified, not used as fact.**
- METRO field-sales postings for Goslar and Kassel (karriere.metro.de, HTTP 404) and Mannheim (stepstone.de, timeout).
- METRO "Meet our people" profiles (HTTP 403).

**Excluded:** job postings for DISH Network / EchoStar (US satellite TV) sales representatives. That is a different company, and its postings appear in search results for "DISH sales representative".
