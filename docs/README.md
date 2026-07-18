# GlucoPlate AI Documentation

This folder is the working knowledge base for GlucoPlate AI. It should stay current as the product evolves.

## Start here

- [System architecture](SYSTEM_ARCHITECTURE.md) — system-level flow across the PWA, FastAPI APIs, domain services, AI providers, persistence, and platform integrations
- [Live Cooking Design Target](LIVE_COOKING_DESIGN_TARGET.md) — approved product experience and mandatory alignment contracts
- [Live Cooking Flow](LIVE_COOKING_FLOW.md) — implementation-grounded create/join/cook flow and the required extension path for video, AI, substitutions, shopping, activity, and replay
- [Product roadmap alignment](PRODUCT_ROADMAP_ALIGNMENT.md) — sequencing and scope rules for delivering the target incrementally
- [Project documentation](PROJECT_DOCUMENTATION.md)
- [iOS and PWA native capabilities](IOS_PWA_NATIVE_CAPABILITIES.md)
- [AI development guide](AI_DEVELOPMENT_GUIDE.md)
- [Deployment secrets](DEPLOYMENT_SECRETS.md)
- [Design and engineering booklet](DESIGN_AND_ENGINEERING_BOOKLET.md)
- [Community AI recipe blog detail](COMMUNITY_AI_RECIPE_BLOG_DETAIL.md)

## Documentation rules

1. Every milestone should have a matching file in `milestones/`.
2. Every significant architecture decision should be captured in `docs/decisions/`.
3. Every feature PR should update the relevant milestone checklist.
4. Every change affecting recipes, Cooking Mode, ingredients, substitutions, shopping, profiles, notifications, activity, analytics, or history must include a **Live Cooking Alignment** section in the PR description.
5. Affected work must implement, strengthen, or preserve a clean path toward the [Live Cooking Design Target](LIVE_COOKING_DESIGN_TARGET.md). It must not create competing session, ingredient, shopping, substitution, activity, or history models.
6. Every next-task proposal affecting the live experience must identify the node or transition in the [Live Cooking Flow](LIVE_COOKING_FLOW.md) that it implements or strengthens.
7. Security-sensitive values belong in deployment environment variables, not documentation examples with real secrets.

## Current product direction

GlucoPlate AI is becoming a collaborative AI cooking platform. The first release focuses on discovering recipes, generating meals, saving favorites, and cooking step by step, but these capabilities form the foundation of a broader live experience with participant rooms, contextual AI help, substitutions, shopping, progress, activity, and private session history.

Approved Figma direction: https://www.figma.com/design/yqfflFjn2CgdFbee3sOXFo
