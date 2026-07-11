# ReceiptAI Rebrand Roadmap

## Strategic Shift

Move from a diabetes-conscious recipe assistant to a general-purpose receipt app.

Original niche:

- health-aware recipes
- diabetes-conscious meal planning
- nutrition/safety review
- grocery and store support

Expanded market:

- personal receipt organization
- family spending tracking
- reimbursements
- freelancer and contractor expense records
- small-business purchase organization
- warranty and return tracking
- tax-prep support without giving tax advice
- purchase history and merchant intelligence

## Product Positioning

### One-liner

ReceiptAI turns everyday receipts into searchable records, spending summaries, return reminders, warranty notes, and export-ready expense history.

### Expanded Audience

1. Everyday shoppers
   - want receipts organized automatically
   - need to find a purchase later
   - want to avoid losing return or warranty info

2. Families
   - track grocery and household spending
   - understand monthly categories
   - organize purchases by child, household, event, or trip

3. Freelancers and contractors
   - separate business and personal expenses
   - keep proof of purchase
   - export simple records for bookkeeping review

4. Small business owners
   - track supplies, meals, fuel, equipment, software, subscriptions
   - prepare records for a bookkeeper or accountant
   - avoid enterprise accounting complexity in early workflows

5. Employees
   - save receipts for reimbursements
   - organize travel, meals, supplies, and event expenses

6. Homeowners and renters
   - track appliance purchases
   - track repairs and parts
   - keep warranty and return-window details

7. Budget-conscious users
   - see category trends
   - find merchant spending patterns
   - detect duplicate or recurring purchases

## MVP Scope

### Phase 1 — Rebrand and Domain Model

- Rename product-facing copy from GlucoPlate AI to ReceiptAI.
- Replace recipe language with receipt, spending, merchant, category, and export language.
- Add receipt schemas:
  - Receipt
  - ReceiptLineItem
  - Merchant
  - ReceiptCategory
  - PaymentSummary
  - ExtractionConfidence
- Keep existing recipe code in place temporarily to avoid breaking the demo while receipt functionality is introduced.

### Phase 2 — Receipt CRUD

- Add local JSON receipt store service.
- Add endpoints:
  - `POST /api/receipts/save`
  - `GET /api/receipts`
  - `GET /api/receipts/{receipt_id}`
  - `PUT /api/receipts/{receipt_id}`
  - `DELETE /api/receipts/{receipt_id}`
- Add tests for persistence and update/delete behavior.

### Phase 3 — Text Extraction Fallback

- Add `POST /api/receipts/extract`.
- Accept pasted receipt text first.
- Extract merchant, date, subtotal, tax, tip, total, and line items using rule-based parsing.
- Mark uncertain values with confidence fields.
- Return warnings instead of silently guessing.

### Phase 4 — AI Extraction and Categorization

- Add receipt-oriented agents:
  - ReceiptExtractionAgent
  - ReceiptCategorizationAgent
  - PrivacyPolicyAgent
  - ReceiptReviewerAgent
- Use AI only behind provider abstraction.
- Keep local parser fallback when provider is unavailable.
- Never treat AI output as final until reviewed by user.

### Phase 5 — Receipt Dashboard UI

- Replace hero copy and form with receipt capture flow.
- Add manual receipt entry.
- Add paste receipt text flow.
- Add saved receipts list.
- Add search and filters.
- Add monthly summary cards.
- Add category and merchant breakdowns.

### Phase 6 — Export and Practical Utility

- Export CSV/JSON.
- Add tags and notes.
- Add reimbursement flag.
- Add business expense flag.
- Add warranty flag.
- Add return deadline field.
- Add duplicate detection.

## Existing Assets to Reuse

- FastAPI app structure
- Pydantic schema pattern
- local JSON persistence pattern
- recents/history service pattern
- product lookup service
- store locator and enrichment services
- route planning as future errand flow
- AI provider health endpoint
- agent memory and backlog infrastructure
- redaction helpers
- tests and CI structure

## Suggested Naming Options

### Strongest option

ReceiptAI

Clear, simple, searchable, and broad enough for consumers and small businesses.

### Alternatives

- ReceiptFlow
- ReceiptPilot
- SpendSnap
- SnapLedger
- ReceiptVault
- Proofly
- PurchasePilot

## Suggested First GitHub Issues

1. Rebrand app shell from GlucoPlate AI to ReceiptAI.
2. Add receipt data model and schemas.
3. Add local receipt store service.
4. Add receipt CRUD API endpoints.
5. Add pasted-text receipt extraction endpoint.
6. Add receipt categorization and confidence warnings.
7. Add receipt dashboard UI.
8. Add monthly spending summary.
9. Add CSV/JSON export.
10. Add tests for receipt parsing and persistence.

## Definition of Done for the Pivot MVP

- A user can create a receipt manually.
- A user can paste receipt text and receive structured extracted fields.
- A user can review low-confidence fields before saving.
- A user can save, list, search, update, and delete receipts.
- A user can see monthly spending by category and merchant.
- A user can export saved receipts.
- The app no longer looks like a diabetes or recipe app on the main page.
- The README and product docs explain the broader receipt app audience.
