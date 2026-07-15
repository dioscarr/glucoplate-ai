# Project Status

Last updated: 2026-07-15

## Current focus

GlucoPlate AI is moving from MVP recipe generation into a full AI cooking companion.

## Recently completed

- Cuisine-first discovery flow.
- Popular recipe name selection.
- Firebase Cloud Messaging foundation.
- End-to-end test notification flow.
- CI test migration for Firebase push endpoints.

## Active priorities

1. Land documentation and milestone structure.
2. Start native PWA milestone.
3. Add iOS-safe layout and device capability manager.
4. Add share, wake lock, haptics, and offline foundations.
5. Prepare Firebase Authentication milestone.

## Known technical debt

- Some storage is still file-backed and should move to database tables.
- Frontend is currently static JavaScript; service boundaries should be improved before features become too large.
- PWA and notification logic should be split into smaller modules.
- Authentication is not yet complete.
- Production privacy, terms, analytics, and observability need dedicated work.

## Current product identity

GlucoPlate should be positioned as an AI cooking companion for everyday home cooks. Nutrition support is useful, but the product should not be limited to a medical or diabetes-only audience.
