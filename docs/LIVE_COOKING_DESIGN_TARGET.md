# GlucoPlate Live Cooking Design Target

## Status

**Product direction: approved design target**

Figma reference: https://www.figma.com/design/yqfflFjn2CgdFbee3sOXFo

This document defines the product experience GlucoPlate is now building toward. The design is not a disconnected future concept. It is the target experience that current and future work must progressively enable.

## Product intent

GlucoPlate should evolve from a recipe generator into a collaborative cooking platform where a user can discover a recipe, start cooking, invite others, resolve missing ingredients, shop intelligently, earn progress, and preserve the session history.

The target experience contains six connected surfaces:

1. Live cooking discovery feed.
2. Active video cooking room.
3. AI ingredient substitution assistant.
4. Nearby ingredient shopping and shopping-list actions.
5. XP, challenges, streaks, and reputation.
6. Recorded session history and event timeline.

The live cooking room is the center of this experience. Recipe detail, Cooking Mode, substitutions, shopping, notifications, activity events, analytics, and history should converge on the same cooking-session model.

## Product alignment rule

All new product, frontend, backend, data, analytics, and infrastructure work must answer the following question:

> Does this work directly implement, strengthen, or preserve a clean extension path toward the Live Cooking Design Target?

Work does not need to deliver live video immediately. It must not create a competing interaction model, incompatible data model, dead-end API, or UI pattern that will later need to be replaced to support the target experience.

Any feature proposal or pull request that touches recipes, Cooking Mode, ingredients, substitutions, shopping, profiles, notifications, events, or history must explain how it supports this direction.

## Required design contracts

### One cooking-session foundation

A cooking session begins when a user enters Cooking Mode. The same session must be able to grow from a private single-user experience into a collaborative room without replacing its identity or progress history.

The session contract should support:

- Recipe and recipe-version identity.
- Host and authenticated participants.
- Current step and completed steps.
- Timers and timer ownership.
- Ingredient availability state.
- Applied substitutions and their reasons.
- Shopping-list links.
- Points and challenge outcomes.
- Session visibility and permissions.
- Start, pause, resume, completion, and abandonment states.
- Replay and recording metadata when enabled.

### Event-driven user actions

Important actions should be represented as durable, backend-authoritative events. The initial implementation may process them synchronously, but event names and payloads should remain stable enough to power real-time collaboration, activity feeds, replay, notifications, and analytics later.

Core event families include:

- `cooking_session_created`
- `cooking_session_joined`
- `cooking_step_started`
- `cooking_step_completed`
- `cooking_timer_started`
- `ingredient_marked_missing`
- `substitution_requested`
- `substitution_suggested`
- `substitution_applied`
- `shopping_item_added`
- `challenge_started`
- `challenge_voted`
- `points_awarded`
- `cooking_session_completed`

The server remains authoritative for permissions, substitutions, votes, points, and final session state.

### Recipe-linked ingredient intelligence

Shopping and substitution behavior must remain attached to a stable recipe ingredient. Ingredient rows should be addressable by identifiers rather than by display text alone.

Each ingredient should be able to expose:

- Canonical ingredient identity.
- Quantity and unit.
- Pantry or availability state.
- Allergy and exclusion signals.
- Suggested substitutions with cooking-impact notes.
- Shopping-list state.
- Product, store, price-source, timestamp, and confidence metadata when available.

### Shared interface language

The Figma screens establish the preferred product vocabulary and interaction hierarchy:

- **Live** for discovery and active rooms.
- **Cook** for the active cooking-session entry point.
- **Ask AI** for contextual cooking assistance.
- **Substitute** for ingredient replacement workflows.
- **Shop** for shopping-list, store, product, and price actions.
- **Activity** for social and system events.
- **History** for completed sessions and replay timelines.

New UI should reuse this language rather than introduce parallel names for the same concepts.

## Screen targets

### Live discovery

The discovery feed should eventually show active rooms, scheduled sessions, friends cooking, trending recipes, and relevant filters. Existing recipe discovery work should be reusable as the recipe and room-entry foundation for this surface.

### Live cooking room

The room combines video, participant presence, recipe progression, ingredients, timers, AI assistance, substitutions, shopping actions, chat or reactions, and points. The first Cooking Mode implementation should therefore use modular panels and session-backed state rather than tightly coupling progress to one static page.

### AI substitution assistant

Substitution recommendations must explain flavor, texture, quantity, cooking, and allergy uncertainty. Applying a substitution should update the active recipe/session state and remain visible in history.

### Ingredient shopping

Shopping begins with a GlucoPlate list and trustworthy product links. Price and availability claims must include source, location, observation time, and confidence. The interface must distinguish current, recently checked, last-known, community-submitted, and unavailable data.

### Progress and challenges

Points, streaks, challenges, and reputation are motivational layers over real cooking actions. They must use backend-validated events and must never reward unsafe shortcuts, fabricated completion, or allergy-risk decisions.

### Session history and replay

Completed sessions should preserve participants, steps, timers, substitutions, challenges, shopping decisions, and meaningful comments or reactions. Video replay is optional and private by default; the event timeline must remain useful even when recording is unavailable.

## Delivery strategy

The design target does not require implementing every surface at once. Delivery remains incremental:

### Foundation

- Stable recipe, ingredient, and cooking-session identifiers.
- Private Cooking Mode backed by persistent session state.
- Step progress, timers, substitutions, and shopping-list actions.
- Durable event vocabulary and analytics correlation.

### Collaboration readiness

- Participant and permission model.
- Presence and real-time event delivery.
- Shared step, timer, ingredient, and substitution state.
- Provider-neutral video-room records.

### Differentiation

- Live video and audio.
- Chat, reactions, voting, and challenges.
- Activity feed and gamification.
- Replay timeline and private recordings.
- Store, product, and price integrations.

## Pull request requirements

For work in an affected area, the PR description should include a **Live Cooking Alignment** section containing:

1. Which target screen or design contract the change supports.
2. Which cooking-session or ingredient identifiers it uses or introduces.
3. Which user events it emits or consumes.
4. How permissions and authenticated data isolation are enforced.
5. How the design behaves when AI, video, price, retailer, notification, or real-time services fail.
6. Any intentional deviation from the Figma target and why.

A change should be reconsidered when it:

- Creates recipe progress outside the cooking-session model.
- Uses ingredient display text as the only identity.
- Stores collaboration state only in the browser.
- Lets the client finalize points, votes, substitutions, or permissions.
- Introduces a second shopping-list or substitution concept.
- Makes unsupported live inventory or allergy-safety claims.
- Prevents a private session from later adding participants or replay metadata.

## Definition of aligned

Work is aligned when it improves the current product while making the target experience easier—not harder—to deliver. The team should prefer small, production-ready increments that compose into the Figma experience over isolated features that must later be rewritten.