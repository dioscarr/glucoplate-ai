# GlucoPlate Premium Launch Readiness

## Executive decision

GlucoPlate should ship first as the fastest, most personal way to answer: **“What can I cook right now?”**

The first release should not attempt to be a full grocery marketplace, nutrition platform, social network, and meal-planning suite simultaneously. The launch product must make the core dinner-decision loop exceptional and trustworthy.

## The premium core loop

1. User enters what they have, crave, or need.
2. GlucoPlate understands time, servings, skill, equipment, exclusions, and cultural preference.
3. The app presents three distinct recipe directions rather than one opaque answer.
4. The user selects and optionally adjusts a direction.
5. The app produces a polished recipe with substitutions and confidence notes.
6. Cooking Mode guides the user step by step and keeps the screen awake.
7. The user rates the result with lightweight feedback.
8. GlucoPlate learns and improves the next recommendation.

## Roadmap authority and synchronization

This document is the authoritative source for launch priority and public go/no-go decisions.

The detailed [Live Cooking, Shopping, and Substitution Plan](../Docs/live-cooking-shopping-plan.md) remains the design and architecture reference for ingredient intelligence, shopping lists, local store and price data, retailer adapters, live rooms, collaboration, points, and replay. Those capabilities must follow the priority boundaries below and must not delay the premium dinner-decision core.

The synchronized execution map is documented in [Product Roadmap Alignment](PRODUCT_ROADMAP_ALIGNMENT.md).

### Current implementation sequence

1. Connect existing recipe UI actions to the Flavor Memory endpoints.
2. Use behavioral signals to rank the three recipe directions.
3. Complete concept selection, generation recovery, and trust states.
4. Build persistent hands-free Cooking Mode.
5. Complete premium recipe detail and lightweight post-cook feedback.
6. Close cookbook, notification-control, privacy, analytics, and production-readiness gaps.

Flavor Memory storage and API foundations are already implemented. Its minimal save/cook/dismiss/repeat learning loop is now part of completing the P0 core experience. Richer preference modeling remains a P2 differentiator.

### Live-shopping scope by priority

**P0:** substitution controls, confidence and allergy notes, add-to-list actions, stable recipe-ingredient identifiers, and a private cooking-session foundation.

**P1:** Smart Pantry Lite, shared household lists, consolidated meal-plan lists, deterministic substitutions, ingredient normalization, and carefully labeled open-food metadata.

**P2:** Confidence Coach, Dinner Decision Room, live video rooms, collaborative substitution challenges, points, activity feed, and replay.

**Deferred:** central store routing, broad price discovery, live inventory claims, retailer OAuth, connected carts, and checkout.

## P0 — Blocking features required to ship

### 1. Real authentication and user isolation
- Firebase Authentication integrated across UI and API.
- Server-side token verification.
- Every saved recipe, preference, push token, recent item, and plan scoped to the authenticated user.
- Account sign-out, deletion, and recovery paths.

### 2. First-run onboarding that creates value
Collect only what changes the first recipe:
- Household size.
- Cooking confidence.
- Avoided ingredients/allergies.
- Favorite cuisines.
- Typical available time.

Allow skip and progressive completion. Do not front-load notification permission.

### 3. Recipe generation experience worthy of trust
- Three recipe concepts before full generation.
- Visible progress states during AI work.
- Retry, edit request, and fallback behavior.
- “Why this fits” explanation.
- Clear estimates and confidence language for nutrition and timing.
- User-visible provider failure handling without exposing technical details.

### 4. Premium recipe detail
- Strong recipe hero and hierarchy.
- Adjustable servings with ingredient scaling.
- Ingredients grouped by phase.
- Timers attached to steps.
- Equipment list.
- Substitution controls.
- Save, share, cook, and add-to-list actions.
- Report/correct recipe feedback.

### 5. Hands-free Cooking Mode
- One step per screen.
- Large type and touch targets.
- Wake lock.
- Step timers.
- Previous/next gestures and buttons.
- Persist progress after refresh or interruption.
- Optional read-aloud capability where supported.
- Offline access to an opened recipe.

### 6. Personal cookbook that works
- Search, filter, sort, favorites, and collections.
- Remove/archive recipe.
- Saved-state synchronization across devices.
- Empty states that return users to recipe creation.

### 7. Useful notifications, not notification infrastructure
Launch with only these notification types:
- Recipe/gallery generation completed.
- User-created meal reminder.
- Optional weekly “use what you have” prompt.

Required controls:
- Per-category opt-in.
- Quiet hours.
- Frequency caps.
- Token cleanup and delivery failure tracking.

### 8. Trust, privacy, and production operations
- Privacy policy and terms.
- Consent and permission explanations.
- Account/data deletion workflow.
- Error monitoring and structured logs.
- Product analytics with documented event names.
- Database backups and restore verification.
- Health checks, alerting, rollback procedure, and rate limiting.
- Accessibility review and mobile-browser test matrix.

## P1 — Ship immediately after launch

### Smart Pantry Lite
Users add ingredients manually, from recent inputs, or from a photo. The app ranks recipes by ingredients already available and clearly lists missing items.

### “Make It Mine” adaptation
One-tap adaptations such as:
- Faster.
- Cheaper.
- Higher protein.
- Kid-friendly.
- Spicier/milder.
- Use a different appliance.
- More authentic to a selected regional style.

### Weekly meal plan
- 3–7 dinner slots.
- Reuse ingredients across meals.
- Generate consolidated grocery list.
- Swap a meal without rebuilding the week.

### Household collaboration
- Shared cookbook and grocery list.
- Household preference conflicts surfaced before generation.
- Assign a meal or ingredient to another household member.

## P2 — Differentiators worth testing

### Cultural Recipe Passport
A discovery experience organized by country, region, technique, and story. Users collect cuisines they have cooked and receive culturally grounded introductions rather than generic “international” categories.

### Leftover Rescue
The user selects a prior recipe or leftovers and GlucoPlate transforms them into a new meal while accounting for food-safety timing.

### Dinner Decision Room
A household receives three options, votes quickly, and GlucoPlate resolves ties based on time, available ingredients, and recent meals.

### Confidence Coach
During cooking, users can ask context-aware questions tied to the current step: what “golden brown” looks like, whether a sauce is too thin, or what substitution is safest.

### Flavor Memory
The P0 learning loop records save, cook, dismiss, repeat, and lightweight post-cook feedback signals. P2 expands this into richer spice, texture, cuisine, ingredient, and effort preference modeling without requiring a long profile.

### Live Cooking Rooms
Authenticated participants join a recipe-linked video room with the current step, ingredient events, substitution challenges, host-confirmed decisions, backend-controlled points, and authorized replay history.

### Realistic Recipe Promise
Every generated recipe receives internal checks for ingredient-step consistency, plausible timing, missing quantities, unsafe handling, and impossible equipment assumptions before display.

## Deliberately defer

- Full store routing as a central launch experience.
- Broad price discovery as primary navigation.
- Live inventory claims without a reliable retailer source.
- Retailer OAuth, connected carts, and checkout.
- Social feed and creator economy.
- Complex calorie or disease-management dashboards.
- Paid subscriptions before retention is demonstrated.
- Broad chatbot UI that competes with the primary recipe flow.

Existing shopping and route capabilities may remain available as secondary or experimental features, but they should not dominate navigation or positioning.

## Launch analytics

### North-star candidate
**Successful cooked recipe sessions per weekly active household.**

### Activation
A new user generates or selects a recipe, opens Cooking Mode, and completes or saves it within the first session.

### Required events
- onboarding_started / completed / skipped
- recipe_request_submitted
- recipe_concepts_shown
- recipe_concept_selected
- recipe_generation_succeeded / failed / retried
- recipe_saved / shared / adapted
- cooking_mode_started / step_completed / completed / abandoned
- recipe_feedback_submitted
- notification_permission_prompted / granted / denied
- notification_opened
- account_deleted

Add later feature events only when their user journeys are activated, including shopping-list, substitution, pantry, Confidence Coach, decision-room, and live-room events. Sensitive allergy details must not be copied into analytics payloads.

### Initial launch targets
- At least 70% recipe-generation success under normal production conditions.
- Median time to first useful recipe concept below 15 seconds.
- At least 40% of activated users save or start cooking a recipe.
- Crash-free/error-free sessions above 99% for critical flows.
- Zero cross-user data exposure in authorization tests.

Targets are hypotheses and should be revised after the first meaningful cohort.

## Go/no-go checklist

Do not publicly launch until all P0 items have an owner, acceptance criteria, test coverage, production verification evidence, and rollback behavior. A feature is not complete because its endpoint exists; it is complete when the user journey, trust controls, telemetry, and recovery states are operational.