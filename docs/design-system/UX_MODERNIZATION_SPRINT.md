# UX Modernization Sprint

## Why This Sprint Exists

The current GlucoPlate AI app proves the core product idea, but the experience still feels like separate tools stitched together. This sprint turns the interface into a modern product workspace: recipe generation, nutrition review, safety guardrails, product lookup, store discovery, cart creation, and route planning should feel like one connected journey.

## Product Experience Direction

GlucoPlate AI should feel like:

- a premium health-tech product
- a warm food-planning assistant
- a practical grocery workflow
- a safety-aware AI system
- a portfolio-grade engineering demo

It should not feel like:

- a raw API demo
- a disconnected map/product/cart experiment
- a generic recipe generator
- a medical diagnosis tool
- a collection of browser dialogs

## Modern Product Shell

This sprint introduces a new static entry point:

```text
app/static/modern.html
```

The previous page remains available at:

```text
app/static/index.html
```

The FastAPI root now redirects to the modern shell:

```text
/ → /static/modern.html
```

## Target Journey

```text
1. User sees a polished product shell
2. User understands the promise immediately
3. User describes the meal they want
4. App generates a structured recipe
5. Nutrition and safety stay visually connected
6. Ingredients become product lookup actions
7. Store discovery and route planning live in the same workspace
8. User can save recipes and create carts
```

## Design Decisions

### 1. Modern Shell First

Instead of rewriting the existing large static page in-place, the sprint adds a cleaner modern shell beside it. This reduces risk and lets the team compare both versions while migrating features intentionally.

### 2. One Connected Workspace

The new layout is organized around two areas:

- **Recipe workspace** — recipe, nutrition, ingredients, substitutions, safety
- **Shopping control center** — products, stores, carts, route planning

### 3. Premium Visual System

The style uses:

- glassy surfaces
- large rounded cards
- strong hero typography
- teal/green food-health palette
- amber accents
- dark-mode support
- better spacing and shadows
- clearer empty/loading states

### 4. API Integration Preserved

The modern shell calls the existing backend endpoints:

- `/api/ai/health`
- `/api/recipes/generate`
- `/api/recipes/save`
- `/api/products/search`
- `/api/stores/search`
- `/api/carts`
- `/api/route/plan`

### 5. No Browser Dialogs

The modern shell uses toast notifications instead of `alert`, `confirm`, or `prompt`.

## UX Team Checklist

### Product Design

- Confirm the primary flow feels obvious within five seconds.
- Decide whether the composer should remain beside the hero or become a dedicated first panel.
- Define the ideal generated recipe state.

### Visual Design

- Review spacing, shadows, typography, and color balance.
- Tune dark mode.
- Create final design tokens.

### UX Writing

- Tighten helper copy.
- Improve product/store/cart empty states.
- Standardize safety disclaimer language.

### Frontend Engineering

- Split CSS and JavaScript from `modern.html` into separate files.
- Migrate mature parts of the old UI into the modern shell.
- Add Playwright smoke tests.

### QA and Accessibility

- Test keyboard navigation.
- Confirm contrast in light and dark modes.
- Confirm mobile usability.
- Confirm no dead-end actions.

## Acceptance Criteria

- `/` opens the modern shell.
- Classic UI remains available.
- Recipe generation works.
- Product lookup works from ingredients.
- Store discovery works with location or demo fallback.
- Cart creation works from a generated recipe.
- Route planning works from discovered stores.
- Toasts replace browser dialogs.
- Tests protect the modern UX anchors.

## Next Iteration

1. Add screenshots to README and booklet.
2. Split modern shell into `modern.css` and `modern.js`.
3. Add Playwright tests for the happy path.
4. Improve cart visibility and saved recipe list in the modern shell.
5. Add a mobile-first review pass.
