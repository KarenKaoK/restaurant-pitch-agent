# 01 — Business Research: DISH Digital Solutions

| | |
|---|---|
| **Phase** | Product Discovery |
| **Research date** | 2026-11-25 (product notes in `data/products/` were gathered on 2026-11-24) |
| **Primary market examined** | Germany, English site (`dish.co/DE/en/`) |
| **Status** | Draft for review |

## Scope and method

This document covers what DISH Digital Solutions sells, who it sells to, what restaurant problems each product addresses, and how customer reviews could reveal sales opportunities. It is input for writing the spec. It does not cover architecture or implementation.

**Sources.** Official DISH sources were used first: `dish.co` product, segment and About pages, the machine-readable summaries `dish.co/llms.txt` and `dish.co/llms-full.txt`, and the DISH support site. One web search was used only to confirm the company identity. Every source is listed with its access date in [§7 Sources](#7-sources).

**Evidence labels used throughout:**

- **[F] Verified fact:** stated on an official DISH page that was read on the research date.
- **[F-note]:** stated in the project's own product notes (`data/products/*.md`), which cite official DISH URLs. I did not re-read those URLs on 2026-11-25.
- **[H] Hypothesis:** an inference by the project team. DISH does not state it. It must be validated.

Prices are for Germany, exclude VAT, and are as published on the research date. They change, and they differ by country.

---

## 1. Company overview and business model

### 1.1 Company facts [F]

| Item | Finding | Source |
|---|---|---|
| Legal entity | DISH Digital Solutions GmbH, a wholly owned subsidiary of METRO AG | S1, S2 |
| Headquarters | Düsseldorf, Germany | S2 |
| Founded | 2015 | S1, S2, S3 |
| Acquisition | Acquired Eijsink, a Dutch POS provider, in 2022 | S1, S3 |
| Certification | ISO 27001:2022 (TÜV Rheinland) | S1, S3 |
| Markets | 16 countries, "primarily across Europe". The country selector lists Belgium, Germany, Spain, France, Croatia, Italy, Hungary, Netherlands, Poland, Portugal, Romania, Slovakia, Austria, Czechia, Ukraine and an "International" edition | S2, S3 |
| Positioning | "The leading digital platform for gastronomy in Europe" (DISH's own claim) | S4 |
| Mission | Help hospitality businesses with digital tools "so they can focus on serving their guests" | S2, S3 |
| Languages | 15+ | S3, S4 |

**The published scale figures don't agree [F]:**

- "410 000+ Restaurants & registered customers" (About page and home page stat blocks, S3, S4)
- "more than 330.000 restaurateurs across 16 countries" (About page body text, S3)
- "More than 350,000 restaurants and registered customers" (llms.txt, S1)
- "36 600 000+ bookings" made through DISH solutions (S3, S4)

These figures count **registered customers**, not paying customers. The free and one-time products (see 1.2) probably inflate the count [H]. No figure for paying customers, revenue or headcount was found.

**Do not confuse it with DISH Network.** DISH Network / DISH Business is a different US satellite-TV company that also sells to hotels. Searches for "DISH" return results about both.

### 1.2 Business model [F unless marked]

DISH combines several revenue models across its portfolio:

| Model | Products | Source |
|---|---|---|
| **One-time fixed price** (no subscription, no commission) | DISH Starter (website) | S1, S2, S5 |
| **Monthly subscription with no commission**, tiered by contract length (3, 12 or 36 months) plus a set-up fee | Professional Reservation, Professional Order, Premium bundle | S5 |
| **Hardware + installation + monthly licence** | DISH POS (from €1,684 hardware/installation + €69/month), DISH POS Lite (€249 + €49/month, 36 months) | S6, S10 |
| **Transaction fees (%)** plus terminal rental or purchase | DISH Pay (from 1.89%), Pay Now and Pay Now Pro (1.29%, no monthly fee), POS Lite (1.29%, minimum €49/month) | S7, S12, S13, S10 |
| **Paid add-ons** (monthly, sometimes with usage fees) | SMS Notification package, No-Show card guarantee (€19.90/month + €0.06 per use + 1.89%), AI Marketing Assistant (€24.90/month), AI Phone Assistant (€99 activation + €9.90/month + €0.35 per call) [F-note] | S9, S11, S14 |
| **Bundle discount** | DISH Premium = Starter website + Professional Order + Professional Reservation + Weblisting, at a lower price than buying them separately | S5 |

**Recurring messages on DISH pages [F]:** "0% commission", "transparent fixed monthly price", "no hidden costs". DISH presents itself as the alternative to commission-based booking and delivery platforms.

**Distribution [F, partial]:** DISH Pay Now is "sold online or at METRO stores", and Pay Now Pro can be picked up at METRO stores (S12, S13). A third-party Makro Spain page lists DISH under its digital services (S16, not official DISH).
**[H]** METRO wholesale is probably an important acquisition channel to restaurant owners who already buy there. No DISH source describes the sales model in full (field sales, METRO in-store, inbound online).

---

## 2. Target customers and restaurant segments

### 2.1 Segments DISH names [F]

The home page and About page show the same six segment tiles (S3, S4):

1. Full Service Restaurants
2. Cafés, Ice-cream Shops & Bakeries
3. Snack Shops & Fast Food Restaurants
4. Pubs & Bars
5. Beer Gardens
6. Food Trucks & Food Stands
7. ("Starting something new?", for new openings)

The About page also says "From bars to bistros, food trucks to fine dining restaurants" (S3).

### 2.2 Segment details from segment pages [F]

| Segment | Pain points DISH names | Products DISH features | Source |
|---|---|---|---|
| Full Service Restaurant | "stressful service, double bookings, or long waiting times"; "staff is short, too many tasks"; "the same questions about reservations and billing over and over again" | POS, Payment Solutions, Professional Reservation, Pay, Pay Now, Professional Order, Starter | S8 |
| Snack Shop & Fast Food | "rush hour at lunchtime", "spontaneous takeaway orders", "every second counts" at checkout; no web presence; commission platforms ("100% control, 0% commissions") | Starter, POS, Pay, Pay Now, Professional Reservation, Professional Order | S15 |

The other four segment pages (cafés, pubs/bars, beer gardens, food trucks) were **not read**. See §6.

### 2.3 Size and type signals from product pages [F]

- **DISH POS:** "traditional restaurants and cafés, but also for bars and other catering establishments"; FAQ adds breweries and beer gardens (S6).
- **DISH POS Lite:** "small and medium-sized" restaurants, cafés, coffee bars, fast food, and canteens for sports clubs, associations and schools, plus bakeries. One point of sale, simple menu, no handheld order-taking (S10).
- **DISH Pay:** "particularly suitable for larger businesses and restaurants" (S7).
- **DISH Pay Now:** "small and seasonal businesses" (S15). **Pay Now Pro:** delivery, events, "on the road" (S13).
- **AI Marketing Assistant:** businesses "that want to actively build and nurture guest relationships" (S11).

### 2.4 Implications for this project [H]

- The core audience appears to be **independent, small and mid-sized hospitality businesses**. No DISH page targets enterprise chains. DISH has not stated this directly.
- Product fit depends strongly on segment. A walk-in snack bar has little use for reservations, and a fine-dining restaurant has little use for takeaway ordering. The pitch agent will need to **identify the segment** (from Google category or reviews) before recommending products.

---

## 3. Product portfolio and key capabilities

Main source: Germany site. **Availability varies by country** (S1), so this list may not apply in other markets.

### 3.1 Portfolio map [F]

| Area | Product | One-line description (DISH wording, paraphrased) | Requires |
|---|---|---|---|
| Online presence | **DISH Starter** (also called "Restaurant-Website" / "DISH Website") | Mobile-optimised restaurant website built "in minutes", digital menu with allergen labels, reservation widget, Google Business Profile setup | — |
| | **DISH Weblisting** | Create a Google Business Profile and manage reviews. Seen only as part of Premium; its own page returns 404 | Premium |
| Reservations | **DISH Professional Reservation** | 24/7 online booking via website or Google, drag-and-drop table management, capacity control, automatic confirmations, email/SMS reminders | — |
| | SMS Notification package | Up to 3 SMS per booking (confirmation, reminder, cancellation) [F-note] | Reservation |
| | No-Show card guarantee | Guests leave card details; a set fee can be charged for no-shows or late cancellations; rules by day, time and party size | Reservation |
| | AI Phone Assistant | Answers calls the restaurant can't take and creates reservations; **pilot only in DE and AT** [F-note] | Reservation or Premium |
| Guest marketing | **AI Marketing Assistant** | Builds a guest database from reservations, website, QR codes and social media; automated welcome, re-engagement, birthday and loyalty campaigns; AI-written newsletters; analytics | Reservation or Premium |
| Online ordering | **DISH Professional Order** | Takeaway and delivery ordering via own website or Google; owner controls menu, prices, availability and promotions; PayPal etc.; no per-order commission | — |
| Bundle | **DISH Premium** | Starter/Website + Professional Order + Professional Reservation + Weblisting; automated SEO, AI text translation; support by phone, email or WhatsApp | — |
| Point of sale | **DISH POS** | Cloud POS with offline mini-server, touchscreen and optional handheld, bill splitting, table plan, real-time sales/stock, quick price changes, QR ordering and self-checkout, DATEV export, German fiscal compliance (GoBD, TSE, DSFinV-K) | — |
| | POS add-on: QR Ordering | Guests scan, order and pay at the table | POS |
| | POS add-on: Order Aggregator | Pulls Lieferando, Wolt etc. orders into the POS and syncs the menu | POS |
| | POS add-on: Order2POS | Click & collect webshop; orders print automatically | POS |
| | **Bar Kitchen Manager** | Kitchen and bar display screens: tickets routed by station, auto-sorting, rush, change and cancel updates, separate dine-in, takeaway and delivery tickets, guest pickup screen | POS |
| | **DISH POS Lite** | All-in-one counter POS (orders, payments, menu, reports) for simple single-till businesses; live "within just a few days" | — |
| Payments | **DISH Pay** | Card terminals (V400c Plus, S1F2 with Wi-Fi/SIM, Tap-to-Pay handheld that combines ordering and payment), QR payments, online payments, tipping, payout app, POS integration | — |
| | **DISH Pay Now** | €39 contactless-only reader, no monthly fee or contract, needs Wi-Fi, tipping, digital receipts. **Cannot read chip or magnetic stripe** | — |
| | **DISH Pay Now Pro** | €79 reader with built-in eSIM, works without Wi-Fi or a phone, for delivery and events | — |

Detailed pricing for the core products is in `data/products/*.md` and in sources S5–S14.

### 3.2 Naming inconsistencies to handle [F]

- The website product appears as "DISH Starter", "Restaurant-Website" and "DISH Website" on different pages.
- llms.txt lists "DISH Reservation", "DISH Order" and "DISH Website" as product families, while product pages use the "Professional" names.
- The project's knowledge base should map these names to one canonical product ID.

---

## 4. Restaurant pain points addressed by each product

This section separates **what DISH itself says** each product solves [F] from **the project's interpretation** [H]. The [F] column uses only DISH page wording or close paraphrase.

| Product | Pain points DISH states [F] | Source | Project interpretation [H] |
|---|---|---|---|
| DISH Starter | No/weak online presence; can't be found on Google Search/Maps; no technical skills needed; no subscription/commission | S1, S2, S4 | Outdated or missing menu/hours online cause guests to go elsewhere |
| DISH Weblisting (Premium) | Creating a Google Business Profile; managing reviews | S5 | Owners who don't reply to reviews or whose Google profile data is wrong |
| Professional Reservation | Commission on bookings ("no commission"); no-shows ("reminders help reduce no-shows"); double bookings (segment page); phone booking load; ensuring "full capacity utilisation" | S2, S3, S8 | Unreachable by phone; no online booking; lost reservations |
| No-Show card guarantee | "No-shows can be frustrating and costly" | S9 | Busy, high-demand restaurants that lose revenue on empty reserved tables |
| AI Phone Assistant | Calls missed during busy service or outside opening hours [F-note] | S14 | "Nobody answers the phone" |
| AI Marketing Assistant | Dependence on third-party platforms for audience; winning back lost guests; rewarding regulars; manual marketing effort | S11 | Low repeat visits. Reviews rarely show this pain directly |
| Professional Order | Per-order commissions from delivery platforms; managing takeaway profitably | S2, S5 | No online ordering; takeaway phone line busy; higher prices on delivery apps |
| DISH POS | "No double bookings, no incorrect invoices"; centrally managed orders; easy bill splitting; real-time sales/stock; works through internet outages; fiscal compliance | S6 | Wrong or forgotten orders; wrong bills; slow order-taking; can't split bills |
| Bar Kitchen Manager | Orders "lost in translation between the till and the stove"; "tickets pile up"; "mistakes happen" | S17 | Long food waits; wrong dishes; courses out of sync |
| DISH POS Lite | Peak-time queues; rotating staff or volunteers at the till; limited counter space | S10 | Long queues at the counter |
| DISH Pay | Slow payments; need for flexible (card, QR, online) payment; transparent fees; tipping | S7 | "Cash only"; card machine broken; long wait for the bill |
| DISH Pay Now / Pro | Monthly fees and contracts on card devices; "Cash-only payments can mean missed sales and slower checkouts" | S12, S13 | Small, seasonal or mobile places that are cash-only today |
| Cross-portfolio (segment pages) | Staff shortages; stressful service; long waits; repeated questions about reservations and billing | S8, S15 | — |

---

## 5. Sales opportunities identifiable through customer reviews

**Everything in this section is a hypothesis [H].** DISH does not publish a method for this. The review signals listed are patterns the team expects to find. None has yet been checked against real review data.

### 5.1 Why reviews are a useful but limited signal [H]

- Reviews show the **guest-facing symptoms** of operational problems (waiting, wrong orders, unreachable by phone, cash only). They seldom show internal problems such as stock management, accounting, fiscal compliance or staff scheduling.
- The **owner's replies** to reviews may show more context ("we are short-staffed", "our card terminal was down").
- **Absence** signals (e.g. no website link, no booking button on the Google profile) may come from the Google Business Profile itself rather than review text. Whether to use that data is a scope decision for the spec.
- A complaint does not mean the restaurant lacks the product. The restaurant may already use DISH or a competitor (e.g. a "slow bill" complaint at a place that already has card terminals).

### 5.2 Candidate review signals mapped to products [H]

| Review signal (examples of guest wording) | Probable underlying issue | Candidate DISH product(s) | Confidence / caveats |
|---|---|---|---|
| "Cash only", "had to go to an ATM", "card machine didn't work" | No or unreliable card acceptance | DISH Pay; Pay Now (small/seasonal); Pay Now Pro (mobile/events) | **High** specificity: the signal names the product area directly |
| "Nobody answers the phone", "couldn't get through" | Phone overload during service | Professional Reservation; + AI Phone Assistant (DE/AT pilot only) | Medium: the call may be about something other than booking |
| "Can't book online", "had to call to reserve" | No online reservation channel | Professional Reservation / Starter widget | Medium-high: check the Google profile for an existing booking link |
| "Our reservation was lost", "double-booked" | Manual reservation handling | Professional Reservation; DISH POS (table plan) | Medium |
| Owner replies or reviews mentioning no-shows, or empty reserved tables | No-show losses | No-Show card guarantee; SMS reminders | Low-medium: guests seldom write about this |
| "Order was wrong", "forgot part of our order", "charged for things we didn't order", "couldn't split the bill" | Ordering or billing errors | DISH POS (+ handheld) | Medium: errors can also come from training or staffing |
| "Waited ages for food", "dishes came at different times" | Kitchen communication / ticket flow | Bar Kitchen Manager (requires DISH POS) | Low-medium: may be a kitchen-capacity problem, not a tooling problem |
| "Waited forever to order / pay", busy terrace | Slow order-taking or payment | DISH POS handheld; DISH Pay Tap-to-Pay handheld; QR Ordering | Medium: "slow service" is ambiguous; look for sub-signals |
| "Long queue at the counter" (cafés, snack bars, canteens) | Checkout bottleneck | DISH POS Lite; DISH Pay | Medium |
| "No website", "couldn't find menu online", "opening hours on Google were wrong", "no allergen info" | Weak online presence | DISH Starter; Weblisting (Premium) | Medium-high when combined with Google profile data |
| "Only available on delivery apps", "more expensive on Lieferando", "no online takeaway ordering" | Platform dependence or no own ordering channel | Professional Order; POS Order Aggregator / Order2POS | Medium |
| Many unanswered negative reviews | Owner isn't managing reputation | Weblisting (Premium) | Low-medium: what Weblisting does for reviews is described only briefly |
| "Used to come often, not anymore", no loyalty offer | Weak guest retention | AI Marketing Assistant (requires Reservation) | **Low**: speculative, weak signal |

### 5.3 Rules any recommendation must respect [F, from product pages]

- **Prerequisites:** AI Phone Assistant, No-Show guarantee, SMS package and AI Marketing Assistant need Professional Reservation (or Premium). Bar Kitchen Manager and the POS add-ons need DISH POS.
- **Availability:** AI Phone Assistant is a pilot in Germany and Austria only [F-note]. Other products vary by country (S1).
- **Product limits:** Pay Now accepts contactless only (no chip or magnetic stripe). POS Lite is not suitable for handheld order-taking at the table (S10, S12).
- **Segment fit [H]:** reservation products suit sit-down venues. Ordering products suit takeaway-heavy concepts.

### 5.4 Opportunity-sizing ideas [H]

- Several pain signals in one review set (e.g. cash-only + unreachable by phone + no website) may point to a **bundle opportunity** (Premium + Pay), not a single product.
- Signal **frequency and recency** (e.g. repeated in the last 6 months) is probably a stronger indicator than a single old complaint.

---

## 6. Information gaps and open questions

### 6.1 About DISH (research gaps)

1. **Customer counts:** 330k, 350k and 410k figures appear. Which is current, and how many are paying restaurants?
2. **Sales motion:** How do DISH sales reps work today (field, inside sales, METRO in-store)? Who would use this tool, and what do they prepare before a call? *(Most important open question for product discovery.)*
3. **Country availability matrix:** Which products are live in which of the 16 countries? Only Germany was examined.
4. **DISH Weblisting:** Its own page returns 404. What exactly does its review management do (replying, monitoring, review requests)? This matters because it is the product most directly linked to reviews.
5. **Segment pages not read:** cafés/bakeries, pubs/bars, beer gardens, food trucks.
6. **Client stories:** The page showed no results when fetched, so there is no official case-study evidence of pain → product outcomes.
7. **Not re-verified this round:** the SMS Notification package and AI Phone Assistant pages (facts come from `data/products/`, collected 2026-11-24). Professional Order and Starter pages were seen only through llms-full.txt and the Premium page.
8. **Bar Kitchen Manager pricing** is not published ("free evaluation").
9. **Competitors** (e.g. other POS and reservation providers in the DACH region) were out of scope but are relevant to objection handling.

### 6.2 For the pitch agent (questions for the spec phase)

1. Which review sources are in scope (Google Reviews only?), in which languages (German reviews are likely), and are there terms-of-service constraints on collecting them?
2. Is Google Business Profile data (website link, booking button, category, attributes like "accepts credit cards") in scope alongside review text?
3. How do we detect whether a restaurant **already uses** DISH or a competitor, so we don't pitch what it already has?
4. Which country or countries does the prototype target (this affects product availability, e.g. the AI Phone Assistant pilot)?
5. What counts as "enough evidence" for a recommendation (minimum number of reviews, recency window)?
6. How should low-confidence signals (retention, no-shows) be presented: as recommendations, or only as discovery questions for the sales rep?
7. Ground truth: is there any way to validate signal → product mappings (e.g. sales-rep feedback, labelled examples)?

---

## 7. Sources

All accessed **2026-11-25** unless noted. "Official" = published by DISH Digital Solutions.

| ID | Source | URL | Type |
|---|---|---|---|
| S1 | DISH llms.txt | https://www.dish.co/llms.txt | Official |
| S2 | DISH llms-full.txt | https://www.dish.co/llms-full.txt | Official |
| S3 | About us (DE/en) | https://www.dish.co/DE/en/about/ | Official |
| S4 | Home (DE/en) | https://www.dish.co/DE/en/ | Official |
| S5 | DISH Premium (DE/en) | https://www.dish.co/DE/en/dish-premium/ | Official |
| S6 | DISH POS (DE/en) | https://www.dish.co/DE/en/dish-pos/ | Official |
| S7 | DISH Pay (DE/en) | https://www.dish.co/DE/en/dish-pay/ | Official |
| S8 | Full Service Restaurant segment | https://www.dish.co/DE/en/full-service-restaurant/ | Official |
| S9 | No-Show options | https://www.dish.co/DE/en/dish-professional-reservation/no-show-options/ | Official |
| S10 | DISH POS Lite | https://www.dish.co/DE/en/dish-pos-lite/ | Official |
| S11 | AI Marketing Assistant | https://www.dish.co/DE/en/dish-professional-reservation/ai-marketingassistant/ | Official |
| S12 | DISH Pay Now | https://www.dish.co/DE/en/dish-pay-now/ | Official |
| S13 | DISH Pay Now Pro | https://www.dish.co/DE/en/dish-pay-now-pro/ | Official |
| S14 | AI Phone Assistant (support) — via `data/products/dish-ai-phone-assistant.md`, accessed 2026-11-24 | https://support.dish.co/en_GB/ai-phone-assistant-everything-you-need-to-know | Official |
| S15 | Snack Bar & Fast Food segment | https://www.dish.co/DE/en/snack-bar-and-fast-food-restaurant/ | Official |
| S16 | Makro Spain digital services | https://www.makro.es/servicios/servicios-digitales/Digital-Solutions | METRO group (not DISH); not read in full |
| S17 | Bar Kitchen Manager | https://www.dish.co/DE/en/bar-kitchen-manager/ | Official |

Pages that failed: `https://www.dish.co/DE/en/dish-weblisting/` (HTTP 404). `https://www.dish.co/DE/en/inspiration/client-stories/` loaded but showed "No results found".
