# Product Requirements

## Product

ReceiptAI is an AI-assisted receipt capture, organization, and spending intelligence app.

## Goal

Help users turn receipts into searchable, categorized, exportable records for personal organization, budgeting, reimbursements, warranties, returns, and small-business expense tracking.

## Target Users

- Everyday shoppers organizing purchases and receipts
- Families tracking grocery, household, and recurring spending
- Freelancers and contractors separating business and personal expenses
- Small business owners preparing records for bookkeeping and tax review
- Employees saving receipts for reimbursements
- Homeowners and renters tracking repairs, appliances, returns, and warranties
- Budget-conscious users looking for merchant and category insights
- Developers studying AI systems architecture
- Recruiters/hiring managers reviewing an AI architecture portfolio project

## MVP Features

1. Create a receipt manually from merchant, date, total, category, and line items.
2. Paste receipt text and extract structured fields using a rule-based parser first.
3. Save receipts to local JSON storage.
4. List, view, update, delete, and search saved receipts.
5. Categorize receipts and line items with confidence values.
6. Return low-confidence extraction warnings so users can review before saving.
7. Generate a monthly spending summary by category and merchant.
8. Export saved receipts to CSV/JSON.
9. Support an AI provider boundary for future OCR/text understanding and categorization.
10. Provide fallback behavior when AI runtime is unavailable.

## Non-Goals

- Tax advice
- Legal advice
- Accounting advice
- Investment or financial planning advice
- Storing full payment card numbers
- Replacing a bookkeeper, accountant, tax professional, or legal professional
- Enterprise accounting integrations in the first MVP

## Success Criteria

- App runs locally and in GitHub Codespaces.
- API returns valid structured receipt JSON.
- Receipt records persist locally without a database.
- Parser fallback works without AI credentials.
- Search can find receipts by merchant, category, tag, and date.
- Monthly summary returns totals by category and merchant.
- Low-confidence fields are clearly flagged for user review.
- AI provider is isolated behind a service boundary.
- Existing useful infrastructure is reused where possible instead of rewriting the whole app.

## Migration Notes

The original GlucoPlate AI app was recipe-first. For the rebrand, keep the strongest reusable pieces:

- FastAPI backend
- static web UI shell
- AI provider health endpoint
- local JSON persistence pattern
- recents/history pattern
- product lookup service
- store locator/enrichment service
- cart/list concepts as purchase history or shopping-list support
- route planning as a later errand-planning feature
- agent memory/backlog infrastructure

Recipe-specific files should be either renamed to receipt-specific equivalents or moved into a legacy/demo area after the receipt MVP is stable.
