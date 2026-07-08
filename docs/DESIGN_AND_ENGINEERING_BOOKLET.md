# GlucoPlate AI — Design and Engineering Booklet

> **Purpose:** This booklet tells the story of GlucoPlate AI as both a product and an engineering system. It documents the current MVP, the target product direction, the design system, the architectural model, lower-level engineering patterns, and twenty user-centered use cases.

---

## 1. Executive Story

GlucoPlate AI is an AI-powered, diabetes-conscious recipe, meal-planning, grocery, and store-assistance system. The product is designed for people who want practical meal ideas that consider carb awareness, cultural food preferences, grocery realities, ingredient substitutions, and safety boundaries.

This is not a medical diagnosis or treatment tool. It is a supportive planning system that helps users make better food decisions while clearly reminding them that personal medical decisions belong with clinicians and registered dietitians.

The engineering story is equally important. GlucoPlate AI is built as a portfolio-grade AI systems architecture project. It demonstrates how a modern software architect can move from vision to implementation by defining service boundaries, API contracts, AI orchestration, safety guardrails, fallback behavior, persistence workflows, and developer-agent infrastructure.

The central idea is simple:

```text
A user should be able to say what they want to eat,
what they need to avoid,
how many people they are feeding,
and where they are shopping —
then receive a safe, useful, culturally relevant plan.
```

---

## 2. Product Vision

### Product Mission

Help users plan diabetes-conscious meals with AI support, cultural relevance, nutrition awareness, grocery lookup, nearby store discovery, cart workflows, and safety-first guidance.

### Product Promise

GlucoPlate AI should feel like a practical food-planning assistant, not a medical authority. It helps users think through meals, understand tradeoffs, and move from recipe idea to shopping action.

### Product Positioning

GlucoPlate AI sits at the intersection of:

- AI recipe generation
- health-aware safety guardrails
- cultural food support
- nutrition estimation
- grocery and product search
- local store discovery
- route and cart planning
- portfolio-grade AI architecture
- AI-assisted engineering workflows

### Current MVP Scope

The current MVP includes:

- FastAPI backend
- static web UI
- recipe generation endpoint
- multi-agent recipe orchestration
- Gemini and Copilot-oriented provider flow
- local fallback recipe generation
- nutrition estimate schema
- safety review schema
- store search using OpenStreetMap Overpass
- product metadata lookup using Open Food Facts
- recipe save/list workflows
- cart create/list/get/update/delete workflows
- route planning endpoint
- recipe image gallery job endpoints
- provider health endpoint
- static UI with light/dark theme, tabbed layout, map area, nutrition cards, ingredient chips, and store/product interactions
- request logging and agent-memory capture for important POST/PUT API activity

### Target Product Direction

The target version should evolve into a full meal-planning companion:

- user profiles and saved dietary preferences
- recurring meal plans
- structured nutrition validation
- production-grade database persistence
- authenticated saved carts and recipes
- retailer-specific product pricing and availability
- stronger route optimization
- image generation workflow improvements
- accessibility and mobile polish
- CI/CD, test coverage, observability, and deployment hardening

---

## 3. High-Level System Design

### High-Level Flow

```text
User Intent
  ↓
Recipe Preferences + Health Constraints
  ↓
API Request
  ↓
Recipe Application Service
  ↓
AI Provider Selection
  ↓
Recipe Orchestrator
  ↓
Planner Agent
  ↓
Recipe Agent
  ↓
Nutrition Agent
  ↓
Safety Agent
  ↓
Reviewer Agent
  ↓
Validated Recipe Response
  ↓
Save Recipe / Build Cart / Search Products / Find Stores / Plan Route / Generate Gallery
```

### System Layers

```text
Presentation Layer
  Static HTML/CSS/JavaScript UI
  Theme tokens, tabs, recipe cards, maps, carts, modals, toast feedback

API Layer
  FastAPI routes under /api
  Request/response schema validation
  Health checks and provider status endpoints

Application Layer
  RecipeApplicationService
  PriceAvailabilityService
  StoreLocatorService
  CartStoreService
  RouteService
  RecipeStoreService

AI Orchestration Layer
  RecipeOrchestrator
  ProviderSelector
  Gemini adapter
  Copilot-oriented agent chain
  JSON extraction and response validation

Domain and Safety Layer
  RecipeRequest / RecipeResponse
  NutritionEstimate
  SafetyReview
  NutritionService
  SafetyService
  FallbackRecipeService

Persistence and Integration Layer
  File-backed MVP stores
  OpenStreetMap Overpass integration
  Open Food Facts integration
  static generated images
  future PostgreSQL production store

Developer-Agent Layer
  Agent memory
  Redaction helpers
  backlog/session storage
  API activity capture
```

### Architectural Principles

1. **API-first:** every product feature should be accessible through a clear backend contract.
2. **Safety-first:** health-adjacent AI output must be reviewed before presentation.
3. **Fallback-first:** the demo should still work when external AI or APIs fail.
4. **Service-oriented:** routes should delegate meaningful work to services.
5. **Schema-driven:** request and response models define the contract.
6. **Provider-flexible:** AI provider selection should be abstracted from product workflows.
7. **Portfolio-grade:** the architecture should show decision-making, not just code.
8. **Agent-ready:** the system should be easy for AI coding agents to understand, extend, and test.

---

## 4. High-Level Product Design System

The design system should express three qualities:

1. **Healthy:** fresh, trustworthy, clear, and non-intimidating.
2. **Practical:** focused on food, stores, carts, and real-world planning.
3. **Intelligent:** visibly AI-assisted but grounded in structured, reviewed output.

### Brand Personality

- warm but responsible
- modern but approachable
- culturally flexible
- calm around health topics
- action-oriented around meals and shopping

### Brand Voice

Use language that is:

- helpful
- conservative with medical claims
- direct about tradeoffs
- encouraging without promising outcomes
- clear when information is estimated or unavailable

Avoid language that is:

- clinical overreach
- fear-based
- overly technical for users
- promising diabetes control or treatment
- hiding uncertainty

### Core Visual Identity

The current UI establishes a strong base:

- primary green/teal palette for food, health, and trust
- amber accent for warmth and highlights
- light theme with clean card surfaces
- blue-toned dark theme for a polished technical feel
- rounded cards and pill-shaped chips
- nutrition metric cards
- badges for AI/fallback source clarity
- map and store panels for grocery workflows

### Suggested Brand Tokens

```css
--brand-primary: #156b5b;
--brand-primary-dark: #0f4c41;
--brand-primary-soft: #eaf6f3;
--brand-primary-mid: #1fa281;
--brand-accent: #d97706;
--danger: #b91c1c;
--surface: #ffffff;
--background: #fbfbfb;
--border: #e9eeec;
--text-primary: #11221d;
--text-secondary: #475551;
--radius-card: 12px;
--radius-control: 8px;
--radius-pill: 999px;
```

### Typography Direction

Use a modern system stack for speed and readability:

```css
font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
```

Design intent:

- headings should feel confident and product-like
- labels should be compact and clear
- recipe steps should prioritize readability
- nutrition values should be scannable
- safety warnings should never be hidden in small text

### Component Families

#### 1. Header

Purpose: establish brand, app identity, and theme control.

Elements:

- logo icon
- product name
- short tagline
- theme toggle

#### 2. Input Sidebar

Purpose: capture user intent.

Elements:

- goal input
- servings input
- max carbs input
- preferences input
- avoid ingredients input
- culture/style selector
- AI provider toggle/status
- submit button

#### 3. Recipe Result Card

Purpose: present the generated plan.

Elements:

- title
- AI/fallback provider badge
- summary
- nutrition estimate grid
- ingredient chips
- cooking steps
- substitutions
- safety review
- save/build-cart actions

#### 4. Nutrition Cards

Purpose: quick numeric comparison.

Metrics:

- calories
- protein
- carbs
- fiber
- sugar
- fat
- sodium

#### 5. Safety Box

Purpose: protect user trust.

States:

- approved
- warning
- unavailable/unknown

Rules:

- safety messages must be visually distinct
- disclaimers must be visible
- warnings should not be hidden behind toggles

#### 6. Ingredient Chips

Purpose: bridge recipe and grocery workflows.

Behaviors:

- clickable ingredient lookup
- loading state
- normalized product query
- add-to-cart support

#### 7. Store Map and Store List

Purpose: move from meal plan to shopping action.

Elements:

- map area
- store list
- store details
- address/phone/website/hours when available
- route planning controls

#### 8. Product Cards

Purpose: show product metadata and limitations.

Elements:

- product name
- brand
- barcode
- image
- source
- notes when price/inventory is unavailable

#### 9. Cart Modal or Panel

Purpose: organize shopping intent.

Elements:

- cart name
- grouped items
- quantities
- store associations
- update/delete actions

#### 10. Toasts and Mini-Modals

Purpose: reduce browser-dialog friction.

Use cases:

- saved recipe
- cart updated
- API unavailable
- ingredient lookup complete
- validation feedback

---

## 5. Detailed Engineering Design System

This section defines how the codebase should behave as a system of repeatable engineering patterns.

### 5.1 Route Pattern

Routes should remain thin.

```text
HTTP endpoint
  validates request through schema
  calls application/service layer
  returns response model or normalized response object
```

Good route behavior:

- no business logic that belongs in services
- no direct vendor logic unless route exists only as a diagnostic
- clear response shape
- consistent error shape
- clear docstrings for non-obvious behavior

### 5.2 Service Pattern

Services own product capability.

Examples:

- `RecipeApplicationService` owns recipe generation use case orchestration.
- `StoreLocatorService` owns nearby store discovery.
- `PriceAvailabilityService` owns product availability facade behavior.
- `ProductLookupService` owns Open Food Facts integration.
- `FallbackRecipeService` owns resilient local generation.
- `CartStoreService` owns cart persistence behavior.
- `RouteService` owns store-stop ordering.

Service rules:

- accept typed schema objects where possible
- return typed schema objects where possible
- isolate external API calls
- provide fallback behavior for demo resilience
- remain independently testable

### 5.3 Schema Pattern

Schemas are contracts.

Core recipe schemas:

```text
RecipeRequest
  goal
  servings
  max_carbs_per_serving
  preferences
  avoid_ingredients
  culture

RecipeResponse
  title
  summary
  ingredients
  steps
  nutrition_estimate
  substitutions
  safety_review
  ai_provider
```

Store/product schemas:

```text
StoreSearchRequest
  latitude
  longitude
  radius_meters
  query

Store
  id
  name
  coordinates
  address/contact fields
  source

ProductSearchRequest
  ingredient
  optional store/location fields

ProductAvailability
  ingredient
  product metadata
  price/currency when available
  availability
  source
  notes
```

Schema rules:

- user input constraints belong in Pydantic fields
- response objects should make uncertainty explicit
- source fields should tell users where data came from
- health-adjacent output needs safety metadata

### 5.4 AI Orchestration Pattern

The AI layer should never be a single unreviewed prompt.

```text
Request
  ↓
Provider selection
  ↓
Planning
  ↓
Recipe drafting
  ↓
Nutrition estimation/review
  ↓
Safety review
  ↓
Final reviewer
  ↓
Validated schema response
```

Rules:

- AI output must be parsed into JSON.
- JSON must validate against `RecipeResponse`.
- failed AI calls must fallback locally.
- provider identity must be returned in `ai_provider`.
- safety review must be part of the final response.

### 5.5 Fallback Pattern

Fallback behavior protects demos and user experience.

```text
External AI fails
  → local fallback recipe generation

Overpass store search fails
  → fallback store result explaining search unavailable

Open Food Facts fails
  → unknown availability result with source note
```

Fallback rules:

- never pretend unavailable data is known
- preserve response shape
- give the user a next action
- log failures for developer review

### 5.6 Integration Adapter Pattern

External systems should be wrapped behind adapters/services.

Current integrations:

- Google Gemini adapter for text generation
- GitHub Copilot-oriented agent chain
- OpenStreetMap Overpass for store search
- Open Food Facts for product metadata
- future retailer APIs for price/inventory

Adapter rules:

- isolate API-specific request formatting
- isolate API-specific response parsing
- avoid leaking vendor response shapes into UI
- set user-agent and timeout controls
- degrade gracefully

### 5.7 Persistence Pattern

Current MVP persistence is file-backed. The target production design should migrate to database-backed persistence.

Recommended production model:

```text
users
profiles
recipes
recipe_versions
recipe_generation_events
nutrition_estimates
safety_reviews
carts
cart_items
stores
product_searches
gallery_jobs
agent_memory_events
```

Persistence rules:

- keep generated recipes versioned
- keep AI provider metadata
- keep safety review result with recipe generation
- track source of nutrition/product/store data
- separate user-private data from public reference data

### 5.8 Observability Pattern

The system should tell developers what happened.

Current behavior:

- request logging middleware
- duration logging
- important POST/PUT API activity captured into agent memory
- health endpoint
- AI provider health endpoint

Target observability:

- structured JSON logs
- request correlation IDs
- generation trace IDs
- provider latency metrics
- fallback rate metric
- safety warning rate metric
- product/store API failure rate metric

### 5.9 Security and Privacy Pattern

Health-adjacent products must treat user input carefully.

Rules:

- no secrets in logs
- redact tokens, emails, UUIDs, and payment-like strings in agent memory
- avoid storing sensitive health details unless necessary
- add authentication before persistent user profiles
- add rate limits before public launch
- add CORS policy appropriate to deployment domain
- add content security policy for production static assets

### 5.10 Testing Pattern

Recommended tests:

- schema validation tests
- fallback recipe tests
- safety service tests
- nutrition estimation tests
- route endpoint tests
- product lookup fallback tests
- store search fallback tests
- AI orchestrator fallback tests
- cart persistence tests
- gallery job lifecycle tests

---

## 6. Low-Level Design Patterns

### Pattern 1 — Thin Controller / Rich Service

Routes expose HTTP contracts. Services own behavior.

### Pattern 2 — Facade Service

`PriceAvailabilityService` provides one product-search face while hiding the current Open Food Facts implementation and future retailer adapters.

### Pattern 3 — Provider Selection

The recipe orchestrator selects between local, Gemini, and Copilot-oriented generation without forcing the UI to know provider internals.

### Pattern 4 — Chain of Responsibility

Planner, recipe, nutrition, safety, and reviewer agents act as sequential responsibility steps.

### Pattern 5 — Schema Validation Boundary

AI output is not trusted until it parses as JSON and validates against the response model.

### Pattern 6 — Local Fallback

Fallback services keep the product demoable without external AI or API dependencies.

### Pattern 7 — Source Transparency

Responses include source/provider fields so the UI can show whether the result came from AI, fallback logic, OpenStreetMap, Open Food Facts, or another source.

### Pattern 8 — File-Backed MVP Store

Fast to build, useful for prototyping, intentionally replaceable by a database store.

### Pattern 9 — Agent Memory Capture

Important API events can be summarized into developer-agent memory to support AI-assisted engineering and debugging.

### Pattern 10 — UI Tokenization

CSS variables define colors, radii, surfaces, and theme behavior so branding can evolve without rewriting every component.

### Pattern 11 — Progressive Enhancement

The static UI works as a straightforward application while advanced features such as map, gallery, cart, and provider health layer in progressively.

### Pattern 12 — Explicit Uncertainty

When price, inventory, nutrition, or safety cannot be fully verified, the system should say so clearly.

---

## 7. Twenty Product Use Cases

### Use Case 1 — Generate a Diabetes-Conscious Recipe

A user enters a meal goal, serving count, carb target, preferences, avoid list, and culture. The system returns a recipe with nutrition estimate, substitutions, safety review, and provider source.

### Use Case 2 — Generate a Dominican-Style Meal

A user asks for a Dominican-style dinner with carb awareness. The system preserves cultural relevance while controlling portions and suggesting swaps.

### Use Case 3 — Avoid Specific Ingredients

A user adds ingredients such as pork, shellfish, dairy, or sugar. The recipe generation flow avoids those ingredients and explains substitutions.

### Use Case 4 — Control Carbs Per Serving

A user sets a maximum carb target. The system generates or selects a recipe that respects the target as a planning constraint.

### Use Case 5 — Use Local Fallback Mode

When AI is unavailable or disabled, the fallback service returns a balanced recipe response using local logic.

### Use Case 6 — Compare AI Provider Availability

A user or developer checks AI health. The system reports provider availability, including Gemini configuration and Copilot package availability.

### Use Case 7 — Save a Generated Recipe

A user likes a recipe and saves it to the local store for later review.

### Use Case 8 — List Saved Recipes

A user opens saved recipes and sees previously saved meal ideas.

### Use Case 9 — Track Recent Recipes

A generated recipe is added to recents so the user can return to recent meal ideas quickly.

### Use Case 10 — Click an Ingredient for Product Lookup

A user clicks an ingredient chip. The system normalizes/searches the ingredient and returns product metadata.

### Use Case 11 — Search Product Metadata

A user searches for a packaged product such as brown rice, yogurt, or beans. The system queries Open Food Facts and returns product names, brands, barcodes, images, and source notes.

### Use Case 12 — Explain Missing Price or Inventory

When live price or inventory is unavailable, the product card explains that Open Food Facts provides product metadata, not live store inventory.

### Use Case 13 — Find Nearby Grocery Stores

A user provides location coordinates. The system searches nearby supermarkets, groceries, and convenience stores through OpenStreetMap Overpass.

### Use Case 14 — Fallback Store Search

If the store API fails, the system returns a fallback store result that explains the search is unavailable instead of breaking the UI.

### Use Case 15 — Enrich Store Metadata

The system attempts to fetch website metadata for stores with website URLs and appends that metadata to the store response.

### Use Case 16 — Build a Shopping Cart

A user creates a cart from recipe ingredients and product choices.

### Use Case 17 — Update a Cart

A user modifies cart items, quantities, or selected stores. The system updates the cart through the cart endpoint.

### Use Case 18 — Delete a Cart

A user removes an old or unwanted cart.

### Use Case 19 — Plan a Store Route

A user selects stores or stops. The route service orders the stops from the starting latitude/longitude.

### Use Case 20 — Generate a Recipe Gallery Job

A user requests recipe imagery. The system enqueues a gallery job and lets the UI poll for completion.

---

## 8. Architectural Design

### Current Architecture Diagram

```text
Browser
  |
  | static HTML/CSS/JS
  v
FastAPI App
  |-- /health
  |-- /static/index.html
  |-- /api/recipes/generate
  |-- /api/recipes/save
  |-- /api/recipes/list
  |-- /api/recipes/recents
  |-- /api/recipes/gallery
  |-- /api/stores/search
  |-- /api/stores/enrich
  |-- /api/products/search
  |-- /api/ingredients/normalize
  |-- /api/carts
  |-- /api/route/plan
  |-- /api/ai/health
  |
  v
Services
  |-- RecipeApplicationService
  |-- RecipeOrchestrator
  |-- FallbackRecipeService
  |-- SafetyService
  |-- NutritionService
  |-- StoreLocatorService
  |-- ProductLookupService
  |-- CartStoreService
  |-- RouteService
  |-- GalleryJobService
  |
  v
External/Future Systems
  |-- Gemini
  |-- GitHub Copilot SDK agent chain
  |-- OpenStreetMap Overpass
  |-- Open Food Facts
  |-- future retailer APIs
  |-- future PostgreSQL
```

### Target Production Architecture

```text
Client App
  Static UI now → future componentized SPA or SSR frontend

API Gateway / FastAPI
  Auth, rate limiting, validation, CORS, request IDs

Application Services
  Recipes, Meal Plans, Products, Stores, Carts, Routes, Gallery, Users

AI Orchestration
  Provider abstraction, prompt templates, agent chain, safety review, output validation

Data Layer
  PostgreSQL, object storage for generated images, cache for search/provider responses

External Integrations
  Gemini/Copilot or other LLM providers
  Open Food Facts
  OpenStreetMap
  Retailer inventory APIs
  Maps/routing provider

Observability
  Logs, metrics, traces, fallback-rate monitoring, safety-warning monitoring
```

### Key Architectural Decisions

#### Decision 1 — FastAPI Backend

FastAPI gives the project strong API contracts, automatic validation, async support, and a clean Python backend foundation.

#### Decision 2 — Static MVP UI

A static UI allows fast prototyping and deployment while still proving the product flow.

#### Decision 3 — Multi-Agent Recipe Orchestration

The recipe workflow is split into planner, recipe, nutrition, safety, and reviewer roles so the AI behavior can be explained, tested, and improved.

#### Decision 4 — Fallback Local Generation

The app remains useful even when AI providers fail or are not configured.

#### Decision 5 — Health-Aware Safety Schema

Safety review is part of the response contract instead of a hidden note.

#### Decision 6 — Open Data Integrations First

OpenStreetMap and Open Food Facts let the MVP demonstrate grocery/store workflows before paid retailer integrations are added.

#### Decision 7 — File-Backed Storage First

File-backed storage is acceptable for MVP speed but should be replaced with PostgreSQL for production.

#### Decision 8 — Agent Memory for Developer Workflow

The app demonstrates not only product AI, but also AI-assisted engineering infrastructure through memory, redaction, and backlog concepts.

---

## 9. Data and API Contracts

### Recipe Generation

```http
POST /api/recipes/generate?use_ai=true
```

Request:

```json
{
  "goal": "quick Dominican-style dinner",
  "servings": 2,
  "max_carbs_per_serving": 45,
  "preferences": ["high protein", "simple ingredients"],
  "avoid_ingredients": ["sugar"],
  "culture": "Dominican"
}
```

Response:

```json
{
  "title": "...",
  "summary": "...",
  "ingredients": ["..."],
  "steps": ["..."],
  "nutrition_estimate": {
    "calories": 0,
    "protein_g": 0,
    "carbs_g": 0,
    "fiber_g": 0,
    "sugar_g": 0,
    "fat_g": 0,
    "sodium_mg": 0
  },
  "substitutions": ["..."],
  "safety_review": {
    "approved": true,
    "warnings": [],
    "disclaimer": "..."
  },
  "ai_provider": "google-gemini | github-copilot-sdk-agent-chain | local-fallback"
}
```

### Store Search

```http
POST /api/stores/search
```

Request:

```json
{
  "latitude": 43.0481,
  "longitude": -76.1474,
  "radius_meters": 5000,
  "query": "grocery"
}
```

Response:

```json
[
  {
    "id": "...",
    "name": "...",
    "latitude": 0,
    "longitude": 0,
    "address": "...",
    "store_type": "supermarket",
    "website": "...",
    "phone": "...",
    "opening_hours": "...",
    "source": "openstreetmap"
  }
]
```

### Product Search

```http
POST /api/products/search
```

Request:

```json
{
  "ingredient": "brown rice",
  "store_id": null,
  "latitude": null,
  "longitude": null
}
```

Response:

```json
[
  {
    "ingredient": "brown rice",
    "product_name": "...",
    "brand": "...",
    "barcode": "...",
    "image_url": "...",
    "price": null,
    "currency": null,
    "availability": "unknown",
    "store_name": null,
    "source": "openfoodfacts",
    "notes": ["..."]
  }
]
```

---

## 10. Branding the Full Picture

### Brand Name

**GlucoPlate AI**

The name combines glucose awareness with the everyday action of building a plate. It feels more practical than clinical and supports the product's balance between food, planning, and health-conscious guidance.

### Tagline Options

1. **Smarter meals. Safer choices. Better planning.**
2. **AI meal planning with carb-aware guardrails.**
3. **From recipe idea to grocery cart — with safety in mind.**
4. **Culturally aware meal planning for healthier plates.**

### Recommended Primary Tagline

**From recipe idea to grocery cart — with safety in mind.**

Why: it captures the full journey: recipe generation, shopping, and safety.

### Visual Story

The visual system should feel like a clean health-tech product, but warmer and more food-centered than a medical dashboard.

Visual cues:

- plate/leaf/salad iconography
- green-teal primary color
- amber highlights for warmth
- clear cards for recipe and nutrition
- warning boxes only when needed
- map/store visuals for real-world planning
- AI/fallback badges for transparency

### UX Story

The experience should answer five questions quickly:

1. What can I cook?
2. Does it fit my constraints?
3. What should I buy?
4. Where can I find it?
5. What should I be careful about?

### Engineering Story

The engineering brand is architecture-first:

- clear contracts
- service boundaries
- AI orchestration
- safety review
- fallback resilience
- integration adapters
- developer-agent memory
- future production path

This makes GlucoPlate AI more than an app. It becomes a case study in AI system architecture.

---

## 11. Feature Roadmap

### Phase 1 — Stabilize MVP

- clean route imports
- normalize response/error shapes
- add endpoint tests
- document local setup and environment variables
- add screenshot/demo assets
- improve static UI organization

### Phase 2 — Production Data Foundation

- add PostgreSQL models
- replace file-backed stores
- add migrations
- add user accounts
- save user preferences
- version generated recipes

### Phase 3 — Nutrition and Safety Upgrade

- integrate structured nutrition data
- add stronger carb/fiber checks
- add sodium and sugar warnings
- add prompt-injection safety tests
- add clinician/dietitian disclaimer standardization

### Phase 4 — Grocery Intelligence

- add retailer-specific product APIs
- add price tracking
- add inventory confidence labels
- add store preference ranking
- add cart export

### Phase 5 — Design System Productization

- split CSS into tokens/components/layout files
- create reusable frontend components
- add accessibility checks
- add mobile-first polish
- add empty/loading/error state standards

### Phase 6 — AI Systems Portfolio Expansion

- add architecture diagrams
- add ADRs
- add prompt contracts
- add agent role specs
- add evaluation test cases
- add CI/CD pipeline
- add deployment runbook

---

## 12. Success Metrics

### Product Metrics

- recipe generation success rate
- fallback rate
- save recipe conversion
- ingredient lookup usage
- cart creation rate
- store search usage
- route planning usage
- gallery generation usage

### Safety Metrics

- safety warning rate
- blocked/flagged output rate
- missing disclaimer rate
- nutrition estimate completeness
- external API uncertainty messages shown

### Engineering Metrics

- test coverage by service
- endpoint error rate
- provider latency
- external API failure rate
- deployment success rate
- time to add a new AI provider
- time to add a new retailer adapter

---

## 13. Final Architecture Narrative

GlucoPlate AI begins with a human problem: people do not just need recipes; they need meals that fit their health constraints, culture, budget, shopping reality, and daily routine.

The product answers that with a guided flow: describe the meal, generate a recipe, review nutrition, check safety, save the result, look up ingredients, find stores, build a cart, and plan the route.

The engineering answers with a layered architecture: FastAPI routes define the boundary, services own capabilities, schemas enforce contracts, AI agents split responsibilities, safety review protects the health-adjacent use case, fallback services keep the app resilient, and integrations connect the recipe idea to real-world grocery data.

The design system answers with trust: fresh colors, readable cards, clear nutrition numbers, visible safety messaging, source badges, and practical shopping workflows.

The full picture is a portfolio-grade AI system: not only a recipe generator, but a blueprint for building useful AI products with architecture, guardrails, product thinking, and engineering discipline.
