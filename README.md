# Restaurant Pitch Agent

An AI-powered sales intelligence prototype that transforms restaurant customer reviews into personalized sales pitches and actionable product recommendations.

## Project Overview

Sales representatives may spend significant time researching restaurants, identifying operational challenges, and preparing personalized sales strategies.

This project explores how AI can analyze Google Reviews, identify potential business pain points, and recommend relevant DISH products to support sales preparation.

## Project Objectives

- Identify restaurant pain points from customer reviews.
- Extract supporting evidence from customer feedback.
- Match business challenges with relevant DISH products.
- Generate personalized sales cards with product recommendations, sales talking points, and suggested questions.

## Development Approach

This project follows an end-to-end AI product development process:

1. Product Discovery
2. Spec-Driven Development (SDD)
3. Technical Design
4. Implementation
5. AI Evaluation and Validation

The development process emphasizes evidence-based recommendations, reliability, reproducibility, and human review.

## Project Status

Product Discovery — In Progress

## Known limitations

- **v1 does not assess review recency.** Some dates in the processed data are imputed
  (`date_imputed = true`) and are not reliable. Recency assessment will be added once real
  review dates are obtained through an API.
- **LLM output is non-deterministic, and v1 runs each evaluation case only once.** Consistency
  across runs could later be measured with pass^k.
- **v1 does not consider country availability.** Recommendations are checked against product
  prerequisites and limits only, so a product that is not available in a restaurant's country
  (e.g. a pilot limited to certain countries) may still be recommended.
- **v1 reads CSV files directly.** A data-source interface could later be added to support
  sources such as Google Places or a CRM.

## Disclaimer

This is an independent portfolio project inspired by publicly available information about DISH Digital Solutions. It is not an official DISH product.