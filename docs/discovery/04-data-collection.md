# 04 — Data Collection: Offline Restaurant Review Dataset

| | |
|---|---|
| **Phase** | Product Discovery → input for Spec |
| **Research date** | 2026-11-25 |
| **Builds on** | [`01-business-research.md`](01-business-research.md), [`02-user-discovery.md`](02-user-discovery.md), [`03-user-stories.md`](03-user-stories.md) (→ *Prototype data scope*) |
| **Status** | **Draft for review. No collector will be built until this approach is approved.** |

## Scope and evidence labels

The prototype uses a **predefined offline dataset** of restaurants and customer reviews (doc 03, *Prototype data scope*). This document compares ways to obtain that dataset and proposes an approach.

- **[F] Verified fact:** stated on the provider's own page (documentation, pricing, terms), read on 2026-11-25.
- **[F-2] Secondary:** from search-result summaries or third-party pages; not confirmed on the primary page.
- **[H] Assessment:** the project team's judgement.

> **Not legal advice.** The terms-of-service findings below summarise public documents. Before real third-party review data is collected or stored, a qualified person should review the plan, especially because of GDPR (the target market is Germany) and the fact that this is a **public portfolio repository**, where a committed dataset counts as redistribution.

---

## 1. Key findings (summary)

1. **Google's own policy forbids storing Google reviews.** The Places API policies say not to "copy and save business names, addresses, or user reviews", and to "Cache or store Google Maps Content only as expressly permitted under the Google Maps Platform Service Specific Terms" [F: S3]. Only place IDs may be stored indefinitely [F: S3]. **An offline dataset of Google reviews conflicts with this policy, whatever tool collects it.**
2. **The official Google API returns at most 5 reviews per place, sorted by relevance** [F: S1]. That is too few to measure how often or how recently a pain point comes up (US-04).
3. **Scraping tools (Playwright, Selenium) and scraping services (Apify, SerpApi) can collect many more reviews, but they don't remove the terms-of-service problem.** Google's Terms of Service prohibit "using automated means to access content from any of our services in violation of the machine-readable instructions on our web pages" [F: S8]. Paid services take on the technical work, not the user's legal responsibility (Apify: "You're responsible for having a legal basis to collect and use it under privacy laws" [F: S6]).
4. **Licensed open datasets exist, but none found covers German restaurants.** The Yelp Open Dataset is "intended for educational use" and covers 11 metropolitan areas [F: S9]. Its exact cities were not stated on the page, and earlier editions were mostly North American [F-2]. The UCSD Google Local dataset is research-oriented and US-based [F-2: S11].
5. **Reviews are personal data under GDPR** when they can be linked to a reviewer. "Under GDPR, all personal data is protected, and it does not matter at all where the data comes from" (Apify legal blog) [F: S7]. Data minimisation applies.

**Proposed direction (details in §5):** build the prototype dataset from **synthetic, hand-curated German reviews** that are clearly labelled as such, plus an optional **licensed open dataset** to test realism. Collecting real Google reviews is deferred until a legal review approves it.

---

## 2. Requirements for the dataset and collection utility

From the task brief and docs 01–03:

| # | Requirement | Source |
|---|---|---|
| D-1 | Restaurant name and category | Brief; segment fit (doc 01 §2) |
| D-2 | Review text | Brief; evidence quotes (US-03) |
| D-3 | Review rating | Brief |
| D-4 | Review date | Brief; recency (US-04) |
| D-5 | Source metadata (source, collection date, licence/provenance, original ID if any) | Brief; data provenance (doc 03) |
| D-6 | JSON or CSV output | Brief |
| D-7 | Duplicate removal | Brief |
| D-8 | **No unnecessary reviewer personal data** | Brief; GDPR |
| D-9 | Enough reviews per restaurant to see patterns (≥ ~30 suggested [H]) | US-04, assumption A-2 (doc 02) |
| D-10 | Mostly German-language reviews | Assumption A-7, US-05 |
| D-11 | Usable offline and committable to the repository without legal risk | Doc 03 data scope; public portfolio repo |
| D-12 | Ideally includes **known ground truth** (which pain points a restaurant really has) to support the AI Evaluation phase | README development approach, step 5 |

---

## 3. Approaches researched

### 3.1 Google Places API (official)

| Aspect | Finding |
|---|---|
| Review availability | "A maximum of 5 reviews can be returned", "sorted by relevance" [F: S1]. No sorting or paging parameter for reviews was found [F: S1]. `userRatingCount` gives the total number of reviews [F: S1] |
| Data completeness | Per review: localized `text`, `originalText`, `rating` (1–5), `publishTime`, `relativePublishTimeDescription`, `authorAttribution`, `googleMapsUri`, `flagContentUri`, `visitDate` [F-2: model summary of S1; field names in S3 match] |
| Implementation complexity | Low. Official REST API with an API key and field masks |
| Cost | Reviews fall under the "Place Details Enterprise + Atmosphere" SKU, and a request is "billed at the highest SKU applicable to your request" [F: S2]. Price per 1,000 requests and free monthly usage **not confirmed** (pricing page not read) |
| Reliability | High: stable, supported API |
| Terms and data usage | **Restrictive.** Don't "copy and save … user reviews"; don't "create content based on Google Maps Content"; must credit the author and link to the source review; must give "a clear notice that describes how reviews are being ordered and filtered" [F: S3]. Only place IDs may be stored indefinitely [F: S3] |
| Fit for offline prototype | **Poor.** Storing reviews offline goes against the policy, and 5 reviews per place is too few. *Possible future use:* live lookup at request time, with attribution (out of scope for the prototype, see US-W7) |

### 3.2 Playwright (browser automation, self-built scraper)

| Aspect | Finding |
|---|---|
| Review availability | Potentially all reviews visible in the Google Maps web interface [H] |
| Data completeness | Whatever the page shows (text, stars, relative date, reviewer name, owner reply). Dates are often relative ("vor 2 Monaten", i.e. "2 months ago"), so exact dates need approximation [H] |
| Implementation complexity | **High.** Dynamic, frequently changing interface, infinite scroll, consent dialogs (EU), anti-bot measures. Ongoing maintenance [H] |
| Cost | Free software; developer time and possibly proxies [H] |
| Reliability | **Low.** Breaks whenever the interface changes; risk of IP blocks [H] |
| Terms and data usage | Google ToS prohibit automated access that violates machine-readable instructions such as robots.txt; scraping content that doesn't belong to you is listed under termination [F: S8]. The storage restrictions in §3.1 reflect Google's general position [F: S3]. GDPR applies to collected personal data [F: S7] |
| Fit for offline prototype | **Poor**: high effort, high legal and reliability risk |

### 3.3 Selenium (browser automation, self-built scraper)

Same assessment as Playwright: same data, same Terms-of-Service and GDPR issues. Selenium is an older tool and often needs more setup for dynamic pages and waiting logic [H]. **Fit: poor.**

### 3.4 Apify — Google Maps Reviews Scraper (managed scraping service)

| Aspect | Finding |
|---|---|
| Review availability | Configurable "Max number of reviews per place"; sorting (e.g. newest); start date; language [F: S6] |
| Data completeness | **Rich.** `text`, `textTranslated`, `stars`, `publishedAtDate`, `originalLanguage`, `responseFromOwnerText`/`Date`, `reviewId`, `reviewUrl`, `placeId`, `totalScore`, `reviewsCount`, `scrapedAt`, plus reviewer fields (`name`, `reviewerId`, `reviewerUrl`, `reviewerPhotoUrl`, …) [F: S6] |
| Personal data control | A `personalData` toggle: "This returns personal data. You're responsible for having a legal basis to collect and use it under privacy laws." [F: S6] Turning it off supports D-8 |
| Implementation complexity | Low to medium: a hosted actor called through an API or the web console |
| Cost | "from $0.30 / 1,000 scraped reviews", with $5 free credit per month [F: S6]. Other pages show $0.35–0.50 [F-2]. A 20-restaurant × 100-review dataset would cost roughly **$1** [H, calculation] |
| Reliability | Medium: maintained by the vendor, but depends on Google's interface. The page lists known issues (e.g. a filter "temporarily ignored") [F: S6] |
| Terms and data usage | The data is still Google content, so the same issues as §3.2 apply. Apify's legal blog: scraping public data is "generally legal in the EU", but "If the URLs you want to scrape are disallowed, you should not scrape them", and GDPR applies regardless of source [F: S7]. Apify disclaims: "We are lawyers, but we are not your lawyers." [F: S7] |
| Fit for offline prototype | **Technically good, legally unresolved.** The best real-data option *if* a legal review approves collecting and storing Google reviews |

### 3.5 SerpApi — Google Maps Reviews API (managed scraping service)

| Aspect | Finding |
|---|---|
| Review availability | `num` 1–60 per request (default 10); paging via `next_page_token`; `sort_by`: `qualityScore`, `newestFirst`, `ratingHigh`, `ratingLow`; language via `hl` [F: S4] |
| Data completeness | Per review: `rating`, `date`, `iso_date`, `iso_date_of_last_edit`, `snippet`, `review_id`, `link`, `details`, `likes`, `images`, plus a `user` object (name, link, contributor_id, thumbnail, …) [F: S4]. Owner response and review language **not shown** in the sample [F: S4] |
| Personal data control | No toggle found. Reviewer fields would have to be dropped after collection [H] |
| Implementation complexity | Low: one REST endpoint with paging |
| Cost | Free: 250 searches/month; Starter $25 (1,000); Developer $75 (5,000) [F: S5]. Only successful searches are counted [F: S5]. Whether each reviews page counts as one search is not stated explicitly for this engine [F: S5]. Roughly 20 restaurants × 100 reviews ≈ 40–200 calls, which may fit the free tier [H] |
| Reliability | Medium to high: vendor-maintained. "U.S. Legal Shield" from the Production plan upward ("up to $2 million in coverage … as long as your use of the data or service is not illegal") [F: S5] |
| Terms and data usage | The data is still Google content; same storage and GDPR issues as §3.4. The Legal Shield is a US product and does not cover GDPR compliance in the EU [H] |
| Fit for offline prototype | **Technically good, legally unresolved.** Similar to Apify |

### 3.6 Existing licensed review datasets

| Dataset | Availability and scope | Licence / usage | Fit |
|---|---|---|---|
| **Yelp Open Dataset** | 6,990,280 reviews, 150,346 businesses, 11 metropolitan areas; "intended for educational use" [F: S9]. Cities not listed on the page; earlier editions were mostly North American [F-2: S10] | Educational use; secondary sources describe it as non-commercial, non-sublicensable and revocable [F-2: S10]. The licence text wasn't read | **Partial.** Real, licensed, large, with ratings and dates. But **English, not German, and not Google**. Good for testing the analysis on real text. Redistributing it in the repo is probably not allowed [H] |
| **UCSD Google Local** (McAuley lab) | Google Maps reviews and metadata, **US only** [F-2: S11] | Research use; the page asks users to cite the papers. No explicit licence found [F-2: S11] | **Weak.** US restaurants, unclear licence, and Google-sourced content |
| **Kaggle / other public dumps** | Many exist [H] | Often scraped, with unclear provenance [H] | **Avoid** unless provenance is clear |
| **German restaurant review dataset (licensed)** | **None found** in this research | — | Gap, see §7 |

### 3.7 Additional option: synthetic, hand-curated reviews (not in the brief, added for comparison)

| Aspect | Assessment [H] |
|---|---|
| Review availability | Unlimited. Written for fictional restaurants by the team, optionally drafted with AI help and then edited by hand |
| Data completeness | All required fields (D-1 – D-5); German language; exact dates |
| Implementation complexity | Low (no scraping); writing effort is moderate |
| Cost | Close to zero |
| Reliability | Full control; fully reproducible |
| Terms and data usage | No third-party content and no reviewer personal data. **Safe to commit to a public repository** |
| Fit for offline prototype | **Strong.** Can include a **known ground truth** (e.g. "Restaurant A is cash-only and hard to reach by phone"), which directly supports the AI Evaluation phase (D-12). Also allows deliberate edge cases: no signal, mixed signals, sarcasm, off-topic reviews |
| Main weakness | **Less realistic.** Risk of writing reviews that match the rules too neatly. This must be offset by realism checks (see §5) |

---

## 4. Comparison matrix

Ratings: ●●● good · ●●○ medium · ●○○ poor. Ratings are the team's assessment [H], based on the facts in §3.

| Criterion | Places API | Playwright | Selenium | Apify | SerpApi | Licensed (Yelp) | Synthetic |
|---|---|---|---|---|---|---|---|
| Review availability | ●○○ (max 5) | ●●● | ●●● | ●●● | ●●● | ●●● | ●●● |
| Data completeness (D-1–D-5) | ●●○ | ●●○ | ●●○ | ●●● | ●●● | ●●○ | ●●● |
| German-language / DE restaurants | ●●● | ●●● | ●●● | ●●● | ●●● | ●○○ | ●●● |
| Implementation complexity (●●● = simple) | ●●● | ●○○ | ●○○ | ●●○ | ●●● | ●●○ | ●●● |
| Cost (●●● = cheap) | ●●○ (unconfirmed) | ●●○ | ●●○ | ●●● | ●●● | ●●● | ●●● |
| Reliability | ●●● | ●○○ | ●○○ | ●●○ | ●●○ | ●●● | ●●● |
| ToS / data-use risk (●●● = low risk) | ●○○ for storage | ●○○ | ●○○ | ●○○ | ●○○ | ●●○ | ●●● |
| Personal-data minimisation | ●●○ | ●●○ | ●●○ | ●●● (toggle) | ●●○ | ●●○ | ●●● |
| Ground truth for evaluation | ●○○ | ●○○ | ●○○ | ●○○ | ●○○ | ●○○ | ●●● |
| **Overall fit for offline prototype** | **Poor** | **Poor** | **Poor** | **Conditional** (legal review) | **Conditional** (legal review) | **Partial** (realism test) | **Recommended** |

---

## 5. Proposed approach (for review)

### 5.1 Recommendation [H]

A **two-tier dataset**, with real Google data deferred:

| Tier | Purpose | Source | Status |
|---|---|---|---|
| **Tier 1: core prototype dataset** | Development, demo, and **evaluation with ground truth** | **Synthetic German reviews** for ~15–20 fictional restaurants covering the segments in doc 01 §2 (full service, café/bakery, snack bar/fast food, bar, food truck), each with a labelled set of intended pain points, including "no signal" controls | **Proposed** |
| **Tier 2: realism check (optional)** | Check that the analysis works on real, messy review text | **Yelp Open Dataset** sample, used locally under its educational-use terms and **not committed** to the repository | Proposed, pending licence check |
| **Tier 3: real German Google reviews** | Closest to real use | Apify (with `personalData` off) or SerpApi | **Deferred.** Only after a legal and terms-of-service review approves collection and storage (see §7) |

**Why:**

- It meets the offline requirement with **no terms-of-service conflict** and no reviewer personal data.
- It is safe to publish in a **public portfolio repository**.
- It gives **ground truth**, which the AI Evaluation phase needs and which scraped data can't provide.
- It is reproducible and cheap.
- It keeps the future path open: the dataset format (§5.3) is the same whatever the source, so the source can be replaced later (doc 03, *Future extensibility*).

**Main risk:** synthetic reviews may be too clean. **Mitigations:**

- Write in varied styles and lengths.
- Include mixed and indirect signals, irrelevant reviews and sarcasm.
- Spread ratings realistically.
- Compare the analysis output on Tier 1 with Tier 2.
- Have reviewers check whether the reviews read like real ones.

### 5.2 Collection utility: functional requirements (no implementation)

The "utility" covers whichever source is approved: importing synthetic files, a licensed dataset, or (later) a scraping service. It must:

| # | Requirement |
|---|---|
| C-1 | Produce records with the fields in §5.3 and write them as **JSON** (primary) and/or **CSV** |
| C-2 | Record **source metadata** for every record: source name, source type (synthetic / licensed / API / scraped), collection date, licence or terms reference, original review ID if any |
| C-3 | **Remove duplicates** (rules in §5.4) and report how many were removed |
| C-4 | **Never store reviewer identity fields**: name, profile URL, reviewer ID, photo, local-guide status, reviewer review count |
| C-5 | Flag or mask obvious personal data *inside review text* (e.g. a named staff member, phone number, email) for manual review [H: approach to be decided in spec] |
| C-6 | Normalise ratings to a 1–5 scale and dates to a single date format; keep the original date string if it was relative |
| C-7 | Record the review language (detected or given by the source) |
| C-8 | Produce a short summary per run: restaurants, reviews per restaurant, date range, languages, duplicates removed, fields missing |
| C-9 | Be repeatable: the same input gives the same output |

### 5.3 Proposed record format (logical fields, not a technical schema)

**Restaurant**

| Field | Required | Notes |
|---|---|---|
| restaurant_id | yes | Stable project ID |
| name | yes | Fictional for synthetic data |
| category | yes | Mapped to the DISH segments in doc 01 §2 |
| city / country | yes | e.g. Düsseldorf / DE (matches the persona) |
| source_place_id | no | Only for API or scraped sources. Google place IDs may be stored [F: S3] |
| ground_truth_pain_points | synthetic only | Labels for evaluation. Kept separate from what the agent sees |

**Review**

| Field | Required | Notes |
|---|---|---|
| review_id | yes | Source ID, or a generated stable ID |
| restaurant_id | yes | Link to restaurant |
| text | yes | Review text in the original language |
| rating | yes | 1–5 |
| review_date | yes | Single date format; approximate if the source gave a relative date |
| review_date_is_approximate | yes | true/false |
| language | yes | e.g. `de` |
| owner_response_text | no | Useful context (doc 02 §5.1). Only if the source provides it |

**Source metadata (per record or per dataset)**

| Field | Required |
|---|---|
| source_name (e.g. `synthetic`, `yelp-open-dataset`) | yes |
| source_type (synthetic / licensed / api / scraped) | yes |
| collected_at | yes |
| licence_or_terms_ref | yes |
| source_url | no (none for synthetic) |

**Explicitly excluded (D-8):** reviewer name, reviewer ID, profile URL, avatar/photo, local-guide flag, reviewer statistics, review images.

### 5.4 Duplicate-removal rules (proposed)

1. **Same source review ID** within the same source → keep one.
2. **Same restaurant + same normalised text** (lower-case, whitespace collapsed) + same rating → keep the earliest. This catches re-scrapes and cross-posting.
3. **Near-duplicates** (e.g. the same text with minor edits) → flag for manual review rather than deleting automatically [H].
4. Restaurants: same name + same address/city → merge.

---

## 6. Assumptions and validation

| ID | Assumption [H] | How to validate |
|---|---|---|
| DA-1 | Synthetic reviews are realistic enough to show the prototype's value | Blind check: reviewers sort a mix of real and synthetic snippets; compare analysis results on Tier 1 vs Tier 2 |
| DA-2 | ~15–20 restaurants × ~30–100 reviews is enough for a prototype demo and first evaluation | Check during spec and evaluation planning |
| DA-3 | Signals in English Yelp reviews carry over to German reviews | Compare signal types found; treat as a limitation |
| DA-4 | Showing reviews without reviewer identity is enough for the sales rep (doc 02, US-03) | Usability test of the sales card |

---

## 7. Open questions for review

1. **Approve the recommended approach?** Synthetic Tier 1, optional Yelp Tier 2, Google-sourced Tier 3 deferred.
2. If **real German Google reviews** are needed, who carries out the legal and terms-of-service review? It must cover Google Maps Platform terms, Google's ToS on automated access, Apify/SerpApi terms, and GDPR (legal basis, minimisation, retention, publishing in a public repository).
3. Should the dataset be **committed to the public repository**? (Recommended only for synthetic data.)
4. Should AI be allowed to help draft synthetic reviews (with human editing), and how should that be disclosed in the dataset metadata?
5. Which segments and how many restaurants should Tier 1 cover? Proposal: at least one per DISH segment in doc 01 §2, plus "no signal" controls.
6. Not verified in this research, to check if Tier 3 is pursued:
   - Google Places pricing for the Enterprise + Atmosphere SKU, and any free usage
   - The exact text of the Google Maps Platform Terms §3.2.3 and the Service Specific Terms (pages couldn't be extracted)
   - Google Maps' robots.txt rules
   - The Yelp dataset's licence text and city list
   - Whether SerpApi counts each reviews page as one search

---

## 8. Sources

All accessed **2026-11-25**.

| ID | Source | URL | Type |
|---|---|---|---|
| S1 | Google Places API (New): Place resource reference | https://developers.google.com/maps/documentation/places/web-service/reference/rest/v1/places | Official (Google) |
| S2 | Google Places API: Usage and billing | https://developers.google.com/maps/documentation/places/web-service/usage-and-billing | Official (Google) |
| S3 | Google Places API: Policies | https://developers.google.com/maps/documentation/places/web-service/policies | Official (Google) |
| S4 | SerpApi: Google Maps Reviews API | https://serpapi.com/google-maps-reviews-api | Official (vendor) |
| S5 | SerpApi: Pricing | https://serpapi.com/pricing | Official (vendor) |
| S6 | Apify: Google Maps Reviews Scraper (compass) | https://apify.com/compass/google-maps-reviews-scraper | Official (vendor) |
| S7 | Apify blog: "Is web scraping legal?" (Feb 2026) | https://blog.apify.com/is-web-scraping-legal/ | Vendor publication; not legal advice |
| S8 | Google Terms of Service (effective 2026-07-30, Germany version) | https://policies.google.com/terms | Official (Google) |
| S9 | Yelp Open Dataset | https://business.yelp.com/data/resources/open-dataset/ | Official (Yelp) |
| S10 | Secondary descriptions of Yelp dataset terms (search results, incl. arXiv papers) | e.g. https://arxiv.org/pdf/2605.07677 | Secondary |
| S11 | UCSD McAuley lab datasets (Google Local) | https://cseweb.ucsd.edu/~jmcauley/datasets.html | Academic; seen via search results only |

**Pages that could not be extracted:** Google Maps Platform Terms of Service (https://cloud.google.com/maps-platform/terms) and Service Specific Terms (https://cloud.google.com/maps-platform/terms/maps-service-terms). Both loaded, but their content was truncated, so §3.2.3 could not be quoted directly.
