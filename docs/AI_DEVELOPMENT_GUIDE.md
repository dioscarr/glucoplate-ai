# AI Development Guide

This guide keeps human contributors and AI coding agents aligned.

## Product context

GlucoPlate AI is an AI cooking companion. Prioritize practical cooking flows over novelty. Every feature should help users discover, generate, cook, save, shop, plan, or remember meals.

## Contribution loop

1. Read `PROJECT_STATUS.md` and the relevant milestone file.
2. Keep changes focused.
3. Update docs with the implementation.
4. Add or update tests.
5. Run the most relevant checks.
6. Open a draft PR with clear validation notes.

## Code standards

- Prefer small services over logic-heavy UI scripts.
- Keep browser capability checks in a device manager or PWA utility layer.
- Never expose service account keys or admin secrets in frontend code.
- Use graceful fallbacks for unsupported browser APIs.
- Keep public API responses structured and stable.
- Preserve accessibility: readable labels, large targets, keyboard-safe behavior, and no browser `alert`, `confirm`, or `prompt` dialogs.

## Backend rules

- FastAPI routes should validate input with Pydantic models.
- Service classes should own integrations and business logic.
- Routes should stay thin.
- External providers must have fallback behavior when possible.
- Admin-only endpoints must require an explicit server-side secret or authenticated role.

## Frontend rules

- Keep the current static PWA simple until the product requires a build system.
- Avoid duplicating device checks throughout the app.
- Feature-detect browser APIs instead of assuming platform support.
- Make iOS Home Screen requirements explicit for notifications.
- Prefer toast or inline message UX instead of blocking dialogs.

## Security rules

- Firebase web config may be public.
- Firebase service account JSON must live only in environment variables.
- `PUSH_ADMIN_KEY` must never be committed.
- Do not log tokens, private keys, or user secrets.

## PR checklist

- [ ] Feature maps to a milestone.
- [ ] Docs updated.
- [ ] Tests updated or rationale documented.
- [ ] CI status reviewed.
- [ ] User impact explained.
- [ ] Security and privacy impact considered.
