# GlucoPlate AI Agent Instructions

## Mission
GlucoPlate AI is a premium collaborative AI cooking platform. Build coherent, accessible, reliable experiences from discovery and planning through shopping and live cooking.

## Sources of truth
Before substantial work, read the relevant files in docs/, especially LIVE_COOKING_DESIGN_TARGET.md, LIVE_COOKING_FLOW.md, PRODUCT_ROADMAP_ALIGNMENT.md, SYSTEM_ARCHITECTURE.md, and inspect the current implementation.

## Product team
Use project agents from .codex/agents/ according to the work:
- product_lead: scope, requirements, sequencing, acceptance criteria, and cross-team coordination.
- ux_flow_designer: user journeys, Mermaid flows, screen/state inventories, and post-design UX validation.
- ui_design_director: premium Figma design, design system, responsive screens, and handoff.
- frontend_engineer: accessible responsive PWA implementation and browser verification.
- python_fullstack_engineer: Python, FastAPI, schemas, services, persistence, integrations, and end-to-end implementation.
- infrastructure_engineer: environments, CI/CD, containers, cloud, observability, security, reliability, and recovery.
- quality_engineer: test strategy, functional and accessibility validation, regression risk, and release evidence.

## Default delivery workflow
For a new product feature:
1. product_lead creates the brief, boundaries, risks, dependencies, and acceptance criteria.
2. ux_flow_designer creates the behavioral flow with Mermaid Chart and covers happy, alternate, loading, empty, permission, offline, error, recovery, and cancellation paths.
3. ui_design_director uses the Figma plugin to create premium responsive screens from the approved flow.
4. ux_flow_designer validates the Figma result. ui_design_director resolves blocking and important findings.
5. python_fullstack_engineer defines API/data contracts and backend work while frontend_engineer implements the approved experience. Parallelize only after contracts are agreed.
6. infrastructure_engineer prepares delivery, secrets, migrations, observability, rollback, and operational requirements.
7. quality_engineer verifies acceptance criteria, accessibility, integration behavior, and regression coverage.
8. product_lead reconciles all evidence and records remaining risks before release.

Small scoped tasks may use fewer agents. Never invoke the full team merely for ceremony.

## Premium design standard
Premium means calm, intentional, distinctive, and highly usable.
- Clear hierarchy, confident typography, excellent spacing, and unmistakable primary actions.
- Mobile-first with deliberate tablet and desktop behavior.
- WCAG 2.2 AA contrast, keyboard support, visible focus, accessible touch targets, semantic labels, dynamic text, and reduced motion.
- Reuse tokens, components, and patterns before inventing new ones.
- Avoid generic dashboards, excessive cards, gratuitous gradients, inconsistent icons, and dense controls.
- Health and nutrition language must remain supportive and non-diagnostic.

## Figma and flow rules
- Use the Figma plugin for design reads and writes and follow applicable Figma skills before each required operation.
- Extend the approved GlucoPlate Figma direction when an editable target exists.
- Use Mermaid Chart for behavioral flows and store approved Mermaid source in docs/.
- Flowcharts are behavioral contracts; Figma is the visual and interaction source of truth.
- Do not silently change an approved flow during visual design or implementation.

## Engineering standards
- Preserve the layered FastAPI architecture: routes, schemas, services, AI orchestration, persistence, and integrations.
- Keep business logic out of route handlers and DOM event handlers.
- Validate external input and AI output at boundaries.
- Never commit secrets. Use environment configuration and document required variables safely.
- Include migrations, backward compatibility, observability, and rollback considerations for production changes.
- Add tests proportional to risk and run the relevant suite before claiming completion.
- Do not change production code during a design-only task unless explicitly requested.
- Preserve unrelated work and state assumptions clearly.

## Required handoffs
Every specialist reports: decisions, artifacts or files changed, validation performed, known risks, unresolved questions, and the exact next owner.
