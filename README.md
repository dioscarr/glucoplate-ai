# ReceiptAI

AI-assisted receipt capture, organization, and spending intelligence app.

ReceiptAI helps everyday consumers, families, freelancers, small businesses, and side-hustle operators turn messy receipts into searchable records, categorized expenses, warranty reminders, return windows, tax-ready exports, and purchase insights.

> **Important:** This project is for personal organization, budgeting support, and software architecture demonstration only. It does not provide tax, legal, financial, accounting, or investment advice. Users should verify important records and consult qualified professionals for tax or business filings.

## Vision

ReceiptAI makes receipts useful after checkout. A user should be able to upload, scan, paste, or manually enter a receipt and quickly understand:

- what was purchased
- where and when it was purchased
- how much was spent
- which category it belongs to
- whether it may matter for taxes, reimbursements, returns, warranties, or budgeting
- what patterns are emerging across their spending

The project is also designed to demonstrate how a modern developer can use AI-assisted engineering in a structured way: clear architecture, API boundaries, agent roles, fallback behavior, safety rules, and developer memory/backlog workflows.

## Why This Pivot

The original GlucoPlate AI concept focused on diabetes-conscious recipes, meal planning, grocery lookup, stores, carts, and AI guardrails. The strongest reusable parts for a broader audience are the product lookup, store discovery, cart/list structure, recents, route/store metadata, AI orchestration, persistence patterns, and portfolio-grade architecture.

Rebranding into a regular receipt app expands the audience from a health-specific niche into a daily utility product for anyone who buys things and wants better organization.

## Target Audience

### Primary Users

- Everyday shoppers who want receipts organized automatically
- Families tracking groceries, household supplies, subscriptions, and errands
- Freelancers and contractors separating business and personal expenses
- Small business owners organizing purchases for bookkeeping and tax prep
- Employees saving receipts for reimbursements
- Renters and homeowners tracking repairs, appliances, warranties, and returns
- Budget-conscious users looking for category-level spending patterns

### Secondary Users

- Developers and hiring managers reviewing an AI system architecture portfolio project
- Product teams studying how to pivot a niche AI app into a broader utility app
- Operators who want lightweight expense workflows without enterprise accounting software

## Current Status

Active MVP prototype with a working FastAPI backend, static web UI, AI provider orchestration, grocery/store/product services, local JSON persistence, cart workflows, route planning, gallery/job patterns, and developer-focused agent memory infrastructure.

The next phase is a product rebrand and domain migration from recipe-first workflows to receipt-first workflows.

## Core Receipt App Capabilities

### Receipt Capture and Storage

- Upload receipt images or paste receipt text
- Manual receipt entry for cash or missing receipts
- Store merchant, date, subtotal, taxes, tips, total, payment method, and line items
- Save receipts to local JSON first, then migrate to database-backed persistence
- Search and filter by merchant, date, category, amount, payment method, and tags

### AI Receipt Understanding

- Extract structured receipt data from OCR/text input
- Categorize purchases automatically
- Detect likely business, tax, reimbursement, return, warranty, grocery, travel, household, and subscription relevance
- Summarize spending patterns in plain language
- Flag uncertain extraction results for user review instead of pretending confidence

### Spending and Organization

- Monthly spending summary
- Category breakdown
- Merchant history
- Duplicate receipt detection
- Return-window reminders
- Warranty tracking
- Export-ready records for CSV/JSON first, later PDF or accounting integrations

### Product, Store, and Cart Reuse

- Link receipt line items to product lookup when possible
- Keep store discovery and enrichment as merchant/store intelligence
- Reuse cart/list concepts as shopping history or planned purchases
- Support route/store planning as a later errand-planning feature, not the core MVP

### Developer / Agent Workflow Infrastructure

- Development-only agent interface helpers for Copilot-driven workflows
- Lightweight file-backed short-term and long-term memory
- Backlog storage for agent/planning tasks
- Session transcript persistence
- Redaction helpers for emails, secrets, tokens, UUIDs, and credit-card-like values
- Middleware that can record important POST/PUT API activity into agent memory

## High-Level Product Flow

```text
Receipt Image / Text / Manual Entry
        ↓
Receipt Intake API
        ↓
OCR / Text Parsing
        ↓
Receipt Extraction Agent
        ↓
Categorization Agent
        ↓
Review + Confidence Guardrails
        ↓
Saved Receipt Record
        ↓
Search / Summary / Export / Reminder / Insight Workflows
```

## AI Architecture

ReceiptAI should use a multi-agent orchestration pattern for receipt understanding.

```text
ReceiptApplicationService
        ↓
ReceiptOrchestrator
        ↓
ExtractionAgent
        ↓
CategorizationAgent
        ↓
PolicyAndPrivacyAgent
        ↓
ReviewerAgent
        ↓
ReceiptResponse
```

The orchestrator coordinates each step and passes structured context forward. If AI execution fails, the system should fall back to a rule-based parser and manual entry flow so the app remains demoable and resilient.

## Proposed API Surface

The existing FastAPI backend can evolve toward endpoints such as:

- `POST /api/receipts/extract` — extract structured receipt data from text or OCR output
- `POST /api/receipts/save` — save a reviewed receipt
- `GET /api/receipts` — list saved receipts
- `GET /api/receipts/{receipt_id}` — get one receipt
- `PUT /api/receipts/{receipt_id}` — update corrected receipt data
- `DELETE /api/receipts/{receipt_id}` — delete a receipt
- `GET /api/receipts/summary/monthly` — monthly spending summary
- `GET /api/receipts/search` — search receipts by merchant, category, tag, or date range
- `POST /api/receipts/export` — export receipts to CSV/JSON
- `POST /api/products/search` — reuse product availability/intelligence support
- `POST /api/stores/search` — reuse store/merchant lookup support
- `GET /api/ai/health` — check AI provider availability
- `GET /health` — application health check

## Safety and Trust Principles

The system must:

- Avoid claiming extracted data is guaranteed correct.
- Require user review for low-confidence totals, dates, merchants, and tax-related categories.
- Avoid tax, legal, accounting, or financial advice.
- Avoid storing full payment card numbers or sensitive personal data.
- Redact secrets, tokens, emails, UUIDs, and credit-card-like values in logs and agent memory.
- Make privacy and data ownership clear to users.
- Prefer conservative confidence behavior over overconfident AI output.

## Python Stack

- Python 3.12+
- FastAPI
- Pydantic
- Pydantic Settings
- SQLAlchemy
- SQLite for local development
- PostgreSQL target for production
- Loguru
- GitHub Copilot SDK / Gemini provider abstraction
- pytest
- httpx
- Ruff

## Repository Structure

```text
app/
  ai/
    agents/
    agent_interface.py
    agent_memory.py
    redaction.py
    receipt_orchestrator.py
  api/
    routes.py
  core/
  models/
  schemas/
  services/
  safety/
  static/
docs/
  product/
  architecture/
  ai-safety/
  data-model/
tests/
.github/
  agent/
```

## Migration Roadmap

1. Rename product surface from GlucoPlate AI to ReceiptAI.
2. Replace recipe-first landing page copy with receipt capture, organization, and spending insight copy.
3. Add receipt schemas for receipt, line item, merchant, category, payment metadata, and confidence fields.
4. Add local receipt store service using the existing JSON persistence pattern.
5. Add receipt extract/save/list/search API endpoints.
6. Add rule-based receipt parser fallback.
7. Add AI receipt extraction and categorization orchestration.
8. Add receipt dashboard UI with upload/manual entry, saved receipts, summaries, and search.
9. Keep recipe-specific features behind legacy docs or remove them after receipt MVP stabilizes.
10. Add tests for receipt parsing, persistence, search, and low-confidence review behavior.

## What This Project Demonstrates

This project is meant to demonstrate more than a receipt tracker. It shows an architecture-first approach to building AI-enabled products:

- defining clear service boundaries
- separating API routes, schemas, services, and AI orchestration
- using specialized agents instead of one monolithic AI call
- validating and reviewing AI output before saving user records
- keeping local fallback behavior for reliability
- adding privacy and confidence constraints for user financial records
- supporting product workflows beyond chat, including search, stores, exports, reminders, and summaries
- creating lightweight memory/backlog infrastructure for AI-assisted development workflows

## Roadmap

Planned improvements:

- Add screenshots and demo GIFs
- Build the receipt-first data model
- Add receipt extraction endpoint and parser fallback
- Add receipt dashboard UI
- Add monthly summary and category breakdown
- Add export support
- Add database-backed persistence
- Add authentication and user profiles
- Add stronger privacy controls
- Add automated tests for core services and agent orchestration
- Add CI checks for linting and tests
- Improve production deployment documentation
