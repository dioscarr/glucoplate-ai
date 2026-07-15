# Project Documentation

## Product mission

GlucoPlate AI helps people answer: **What can I cook right now that fits my situation?**

The long-term product is an AI cooking companion, not only a recipe generator. It should support discovery, personalization, cooking guidance, shopping, meal planning, reminders, and native-feeling mobile experiences.

## Core product pillars

1. **Discover**: cuisine-first browsing, popular recipe names, ingredient-based suggestions, and natural-language recipe creation.
2. **Generate**: AI recipe generation with structured ingredients, steps, substitutions, safety notes, and nutrition estimates.
3. **Cook**: step-by-step cook mode with timers, large controls, and eventually wake lock and haptics.
4. **Save**: personal cookbook, favorites, recents, and eventually cloud-backed accounts.
5. **Shop**: grocery list, product search, carts, and route planning.
6. **Plan**: weekly meal plans and pantry-aware recommendations.
7. **Notify**: Firebase-powered reminders, test notifications, and targeted recipe nudges.

## Current architecture

```text
Static PWA frontend
        ↓
FastAPI backend
        ↓
Recipe, profile, cart, push, and AI services
        ↓
Local fallback AI + configured external AI providers
        ↓
SQLite locally, PostgreSQL target for production
        ↓
Firebase Cloud Messaging for push notifications
```

## Development workflow

1. Define the feature in a milestone file.
2. Implement the smallest useful slice.
3. Update API and product documentation.
4. Add or update tests.
5. Open a draft PR.
6. Validate CI.
7. Merge only after the milestone checklist is current.

## Documentation map

- `docs/README.md`: documentation index.
- `docs/PROJECT_DOCUMENTATION.md`: product and architecture overview.
- `docs/IOS_PWA_NATIVE_CAPABILITIES.md`: native-feeling web app plan.
- `docs/AI_DEVELOPMENT_GUIDE.md`: coding and agent contribution rules.
- `milestones/`: execution plan by release stage.
- `PROJECT_STATUS.md`: live snapshot of product status.
- `ROADMAP.md`: high-level release sequence.
- `CHANGELOG.md`: human-readable release history.
