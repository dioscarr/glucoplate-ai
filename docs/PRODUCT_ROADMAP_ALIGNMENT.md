# GlucoPlate Product Roadmap Alignment

## Purpose

This document synchronizes the Premium Launch Readiness plan with the approved Live Cooking Design Target and the detailed Live Cooking, Shopping, and Substitution plan.

The launch-readiness plan remains authoritative for sequencing, release safety, and go/no-go decisions. The [Live Cooking Design Target](LIVE_COOKING_DESIGN_TARGET.md) is authoritative for the product experience and extension contracts that each implementation slice must preserve. The detailed live-cooking and shopping plan remains the technical reference for collaboration, ingredient intelligence, shopping, pricing, retailer integrations, and replay.

## Executive product decision

GlucoPlate launches first as the fastest, most personal way to answer:

> What can I cook right now?

The first public release must make the dinner-decision loop exceptional. However, this launch core is no longer treated as a separate product that will later be replaced by live collaboration. It is the first usable layer of the approved collaborative cooking experience.

Current and future work must progressively enable the Figma target:

https://www.figma.com/design/yqfflFjn2CgdFbee3sOXFo

## Mandatory alignment rule

All work affecting recipes, Cooking Mode, ingredients, substitutions, shopping, profiles, notifications, analytics, activity, or history must directly implement, strengthen, or preserve a clean extension path toward the Live Cooking Design Target.

A P0 feature does not need to include video, participants, challenges, or replay. It must avoid incompatible identifiers, dead-end APIs, browser-only state, duplicated concepts, and static UI structures that would require replacement when collaboration is added.

Every affected pull request should include a **Live Cooking Alignment** section explaining:

1. Which target screen or design contract it supports.
2. Which cooking-session or ingredient identifiers it uses.
3. Which product events it emits or consumes.
4. How permissions and authenticated isolation are enforced.
5. How the experience degrades when optional services fail.
6. Any intentional deviation from the design target.

## One synchronized roadmap

### P0 — Launch core and collaboration foundation

P0 contains the capabilities required to deliver and operate the premium core loop safely while establishing reusable foundations for the approved design:

1. Authentication, server-side token verification, account recovery, deletion, and strict user isolation.
2. Lightweight onboarding for household size, confidence, exclusions/allergies, cuisines, and typical available time.
3. Three recipe concepts before full generation, with progress, retry, fallback, and clear confidence language.
4. Premium recipe detail with scaling, grouped and stably identified ingredients, equipment, substitutions, timers, save/share/cook/add-to-list, and correction feedback.
5. Hands-free Cooking Mode backed by a persistent `CookingSession`, with step progress, wake lock, timers, navigation, optional read-aloud, and offline access to an opened recipe.
6. A reliable personal cookbook with search, filters, favorites, collections, archive/remove behavior, and cross-device synchronization.
7. A deliberately small notification set with opt-in categories, quiet hours, caps, token cleanup, and failure tracking.
8. Durable cooking, ingredient, substitution, and shopping events that can later support real-time rooms, activity feeds, points, and replay.
9. Privacy, analytics, monitoring, backups, restore evidence, alerting, rollback, rate limiting, accessibility, and mobile-browser verification.

### P0 implementation order from the current main branch

1. Wire existing save, cook, dismiss, and repeat actions into Flavor Memory interaction endpoints.
2. Use Flavor Memory signals to rank the three recipe directions.
3. Complete the three-concept selection flow and generation recovery states.
4. Build the `CookingSession` foundation and Cooking Mode interface using modular, session-backed state.
5. Add recipe-detail timers, substitutions, serving scaling, equipment, stable recipe-ingredient IDs, and add-to-list actions.
6. Emit durable events for step progress, timers, missing ingredients, substitutions, shopping actions, and completion.
7. Complete lightweight post-cook feedback and analytics.
8. Close remaining cookbook, notification-control, privacy, and production-readiness gaps.

Flavor Memory storage and API foundations are already present. Flavor Memory is therefore no longer treated only as a distant P2 experiment; its minimal behavioral-learning loop is part of completing the P0 premium core. Rich preference modeling remains a later enhancement.

## How the live-cooking design fits

### Included in P0

The pieces that strengthen the primary recipe journey and establish the shared foundation:

- A private cooking session created when Cooking Mode starts.
- Persistent current-step, completed-step, timer, pause, resume, completion, and abandonment state.
- Stable recipe, recipe-version, and recipe-ingredient identifiers.
- Substitution controls on recipe detail and inside the active session.
- Clear flavor, texture, quantity, cooking, and allergy-confidence notes.
- Add one ingredient or all missing ingredients to a GlucoPlate shopping list.
- Links among recipe ingredients, substitutions, shopping items, and cooking sessions.
- Backend-authoritative cooking events and analytics correlation.
- Authentication and authorization for private recipe, session, event, and list data.
- UI vocabulary and modular layouts that align with Live, Cook, Ask AI, Substitute, Shop, Activity, and History.

These P0 elements must not require live video, store routing, live inventory, retailer OAuth, or checkout integrations. They must be designed so those capabilities can attach without replacing the core session and ingredient models.

### P1 — Collaboration readiness

The following work prepares the product for the full room experience while delivering immediate user value:

- Smart Pantry Lite and pantry-aware missing-item filtering.
- Shared household grocery lists.
- Consolidated grocery lists for weekly meal plans.
- Deterministic substitution rules and structured cooking-impact explanations.
- Ingredient normalization and canonical ingredient identifiers.
- Open Food Facts and USDA adapters where they improve ingredient, nutrition, and allergen metadata.
- Product links as a secondary action when trustworthy matches are available.
- Participant, invitation, role, and permission models for cooking sessions.
- Presence and real-time delivery for shared session events.
- Shared step, timer, ingredient-availability, and substitution state.
- Provider-neutral video-room and replay metadata records, even before a video provider is activated.

### P2 — Live Cooking Experience differentiators

- Confidence Coach tied to the active cooking step.
- Dinner Decision Room voting.
- Live cooking rooms with video, audio, chat, challenges, points, and replay history.
- Collaborative substitution voting and host confirmation.
- Activity-feed publishing and gamification.
- Session history with event timelines and private recordings when enabled.
- Cultural Recipe Passport, Leftover Rescue, and richer Flavor Memory modeling.

### Deliberately deferred integrations

- Full store routing as a central launch experience.
- Broad local price discovery as a primary navigation surface.
- Live inventory claims without a reliable retailer source.
- Retailer OAuth, connected carts, and checkout.
- A public creator economy.
- Paid subscriptions before retention is demonstrated.

Store, price, retailer, video, recording, and cart adapters may be designed behind provider-neutral interfaces, but implementation must not delay P0 or dominate the launch experience.

## Architecture alignment

The synchronized architecture uses one cooking-session foundation from the first Cooking Mode implementation:

```text
Recipe concept
  -> generated recipe and version
  -> recipe detail with stable ingredient IDs
  -> private cooking session
  -> step progress, timers, ingredient state, and substitutions
  -> shopping-list links and durable cooking events
  -> post-cook feedback
  -> Flavor Memory

Extensions on the same session:
  -> Confidence Coach
  -> participants and presence
  -> household decision room
  -> live video room
  -> substitution challenge
  -> points and activity feed
  -> history timeline and replay
```

A `CookingSession` begins as private progress state for one authenticated user. Later releases attach participants, a video-provider room, shared events, points, and replay metadata without replacing the original model or losing earlier session history.

Important product actions should have stable backend-authoritative event names and correlated identifiers. Initial processing may remain synchronous, but the payloads must be usable by real-time collaboration, analytics, notifications, activity feeds, and replay.

## Design alignment

The approved Figma file contains six connected targets:

1. Live cooking discovery feed.
2. Active video cooking room.
3. AI ingredient substitution assistant.
4. Nearby ingredient shopping and shopping-list actions.
5. XP, challenges, streaks, and reputation.
6. Recorded session history and event timeline.

The live room is the center of the product model. Recipe detail and private Cooking Mode are the first states of that same experience, not separate implementations.

Frontend work should favor reusable panels and state boundaries for:

- Session header and presence.
- Recipe steps and progress.
- Video or participant region.
- Ingredients and availability.
- Timers.
- Ask AI.
- Substitutions.
- Shopping.
- Reactions, challenges, and points.
- History and replay.

Not every panel must be visible in P0, but existing layouts must leave a reasonable extension path.

## Analytics alignment

The launch north star remains:

**Successful cooked recipe sessions per weekly active household.**

The existing launch event list remains required. Live-design events should be introduced as their underlying actions become available:

- `cooking_session_created / resumed / completed / abandoned`
- `cooking_step_started / completed`
- `cooking_timer_started / completed / cancelled`
- `ingredient_marked_available / missing`
- `ingredient_added_to_list`
- `shopping_list_created / shared / item_completed`
- `substitution_requested / viewed / applied / rejected`
- `pantry_item_added / removed`
- `cooking_question_asked / resolved`
- `cooking_room_created / joined / completed`
- `substitution_challenge_started / voted / confirmed`
- `points_awarded`
- `replay_viewed`

Events must include authenticated user or household scope, recipe/session correlation, outcome, and failure state where applicable. Sensitive allergy details must not be copied into analytics payloads.

## Scope-control rules

1. P0 delivery wins over P1 and P2 implementation when capacity conflicts, but P0 work must follow the approved design contracts.
2. A backend endpoint alone does not complete a feature; the user flow, telemetry, trust controls, tests, and recovery states must operate together.
3. Open-data integrations must display source quality, timestamps, and uncertainty.
4. The app must never guarantee allergy safety or infer local product availability from generic product metadata.
5. Shopping and live-room architecture must be extensible, but no speculative integration may delay the dinner-decision core.
6. Every new proposal must identify its priority, target screen or design contract, activation impact, north-star impact, operational cost, failure behavior, and rollback behavior.
7. The client must not finalize permissions, points, votes, substitutions, or authoritative session state.
8. Ingredient display text must not be the only identity used for substitutions, shopping, or session history.
9. Collaboration state must not exist only in browser memory.
10. New work must not introduce competing cooking-session, shopping-list, substitution, activity, or history concepts.

## Immediate next slice

The next implementation slice remains:

1. Connect existing recipe UI actions to the Flavor Memory endpoints.
2. Record `saved`, `cooked`, `dismissed`, and `repeated` signals under the active household profile.
3. Add resilient UI behavior so signal failures never block the primary recipe action.
4. Add analytics correlation for recipe and profile context.
5. Use the resulting history to rank the three recipe directions before full generation.
6. Ensure the subsequent Cooking Mode slice starts a persistent session with stable recipe and ingredient correlation rather than page-local progress.

This sequence directly strengthens the premium core loop and prepares the Cooking Mode session work that becomes the foundation of the approved Live Cooking Design Target.