# GlucoPlate Product Roadmap Alignment

## Purpose

This document synchronizes the Premium Launch Readiness plan with the Live Cooking, Shopping, and Substitution plan.

The launch-readiness plan is the authoritative source for product priority and go/no-go decisions. The live-cooking and shopping plan remains the technical and product design reference for later collaboration, ingredient intelligence, shopping, pricing, and retailer integrations.

## Executive product decision

GlucoPlate launches first as the fastest, most personal way to answer:

> What can I cook right now?

The first public release must make the dinner-decision loop exceptional before GlucoPlate expands into a grocery marketplace, social network, meal-planning suite, or creator platform.

## One synchronized roadmap

### P0 — Launch core

P0 contains only capabilities required to deliver and operate the premium core loop safely:

1. Authentication, server-side token verification, account recovery, deletion, and strict user isolation.
2. Lightweight onboarding for household size, confidence, exclusions/allergies, cuisines, and typical available time.
3. Three recipe concepts before full generation, with progress, retry, fallback, and clear confidence language.
4. Premium recipe detail with scaling, grouped ingredients, equipment, substitutions, timers, save/share/cook/add-to-list, and correction feedback.
5. Hands-free Cooking Mode with persistent step progress, wake lock, timers, navigation, optional read-aloud, and offline access to an opened recipe.
6. A reliable personal cookbook with search, filters, favorites, collections, archive/remove behavior, and cross-device synchronization.
7. A deliberately small notification set with opt-in categories, quiet hours, caps, token cleanup, and failure tracking.
8. Privacy, analytics, monitoring, backups, restore evidence, alerting, rollback, rate limiting, accessibility, and mobile-browser verification.

### P0 implementation order from the current main branch

1. Wire existing save, cook, dismiss, and repeat actions into Flavor Memory interaction endpoints.
2. Use Flavor Memory signals to rank the three recipe directions.
3. Complete the three-concept selection flow and generation recovery states.
4. Build the Cooking Mode session foundation and user interface.
5. Add recipe-detail timers, substitutions, serving scaling, equipment, and add-to-list actions.
6. Complete lightweight post-cook feedback and analytics.
7. Close remaining cookbook, notification-control, privacy, and production-readiness gaps.

Flavor Memory storage and API foundations are already present. Flavor Memory is therefore no longer treated only as a distant P2 experiment; its minimal behavioral-learning loop is part of completing the P0 premium core. Rich preference modeling remains a later enhancement.

## How the live-cooking and shopping plan fits

### Included in P0

Only the pieces that strengthen the primary recipe journey:

- Substitution controls on recipe detail.
- Clear flavor, texture, quantity, cooking, and allergy-confidence notes.
- Add one ingredient or all missing ingredients to a GlucoPlate shopping list.
- Stable recipe-ingredient identifiers needed for substitutions and list items.
- Cooking-session and cooking-event concepts needed to persist Cooking Mode progress.
- Authentication and authorization for private recipe, session, and list data.

These P0 elements must not require live video, store routing, live inventory, retailer OAuth, or checkout integrations.

### P1 — Immediately after launch

The following parts of the live-shopping plan support already-approved P1 work:

- Smart Pantry Lite and pantry-aware missing-item filtering.
- Shared household grocery lists.
- Consolidated grocery lists for weekly meal plans.
- Deterministic substitution rules and structured cooking-impact explanations.
- Ingredient normalization and canonical ingredient identifiers.
- Open Food Facts and USDA adapters where they improve ingredient, nutrition, and allergen metadata.
- Product links as a secondary action when trustworthy matches are available.

### P2 — Differentiators to test

- Confidence Coach tied to the active cooking step.
- Dinner Decision Room voting.
- Live cooking rooms with video, audio, chat, challenges, points, and replay history.
- Collaborative substitution voting and host confirmation.
- Activity-feed publishing and gamification.
- Cultural Recipe Passport, Leftover Rescue, and richer Flavor Memory modeling.

### Deliberately deferred

- Full store routing as a central launch experience.
- Broad local price discovery as a primary navigation surface.
- Live inventory claims without a reliable retailer source.
- Retailer OAuth, connected carts, and checkout.
- Social feed and creator economy.
- Paid subscriptions before retention is demonstrated.

Store, price, retailer, and cart adapters may be designed behind provider-neutral interfaces, but implementation must not delay P0 or dominate the launch experience.

## Architecture alignment

The synchronized architecture uses one cooking-session foundation that can grow without requiring live rooms at launch:

```text
Recipe concept
  -> generated recipe
  -> recipe detail
  -> cooking session
  -> step progress and timers
  -> post-cook feedback
  -> Flavor Memory

Later extensions:
  cooking session
    -> Confidence Coach
    -> household decision room
    -> live video room
    -> substitution challenge
    -> activity feed and replay
```

A `CookingSession` begins as private progress state for one authenticated user. Later releases may attach participants, a video provider room, shared events, points, and replay metadata without replacing the original model.

## Analytics alignment

The launch north star remains:

**Successful cooked recipe sessions per weekly active household.**

The existing launch event list remains required. Live-shopping events are added only when those features are activated:

- ingredient_added_to_list
- shopping_list_created / shared / item_completed
- substitution_viewed / applied / rejected
- pantry_item_added / removed
- cooking_question_asked / resolved
- cooking_room_created / joined / completed
- substitution_challenge_started / voted / confirmed

Events must include authenticated user or household scope, recipe/session correlation, outcome, and failure state where applicable. Sensitive allergy details must not be copied into analytics payloads.

## Scope-control rules

1. P0 work wins over P1 and P2 work when capacity conflicts.
2. A backend endpoint alone does not complete a feature; the user flow, telemetry, trust controls, tests, and recovery states must operate together.
3. Open-data integrations must display source quality, timestamps, and uncertainty.
4. The app must never guarantee allergy safety or infer local product availability from generic product metadata.
5. Shopping and live-room architecture should be extensible, but no speculative integration may delay the dinner-decision core.
6. Every new proposal must identify its priority, activation impact, north-star impact, operational cost, and rollback behavior.

## Immediate next slice

The next implementation slice is:

1. Connect existing recipe UI actions to the Flavor Memory endpoints.
2. Record `saved`, `cooked`, `dismissed`, and `repeated` signals under the active household profile.
3. Add resilient UI behavior so signal failures never block the primary recipe action.
4. Add analytics correlation for recipe and profile context.
5. Use the resulting history to rank the three recipe directions before full generation.

This sequence directly strengthens the premium core loop and prepares the Cooking Mode session work that follows.