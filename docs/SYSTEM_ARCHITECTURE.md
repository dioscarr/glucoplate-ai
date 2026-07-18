# System Architecture

This document provides a system-level view of GlucoPlate AI. It reflects the current repository structure and the major runtime integrations.

```mermaid
flowchart LR
  User["Home cooks and collaborators"]

  subgraph Client["Client and device layer"]
    PWA["Responsive PWA"]
    Native["Device capabilities<br/>camera, notifications, offline, timers"]
    SW["Service worker and local cache"]
  end

  subgraph API["Application layer — FastAPI"]
    Gateway["HTTP API and static asset delivery"]
    Identity["Authentication and user data"]
    RecipeAPI["Recipes, recommendations, pantry"]
    CommerceAPI["Shopping, products, prices, receipts, routes"]
    LiveAPI["Live cook rooms, media, sessions, shared state"]
    PushAPI["Push notifications"]
    AdminAPI["Enterprise administration"]
  end

  subgraph Domain["Domain services"]
    RecipeSvc["Recipe generation and storage"]
    PantrySvc["Pantry and ingredient normalization"]
    ShopSvc["Shopping list, cart, receipt, price and store services"]
    LiveSvc["Collaborative cooking services"]
    ProfileSvc["Profiles, personalization and history"]
    NotificationSvc["Notification service"]
  end

  subgraph AI["AI orchestration"]
    Selector{"Provider selector"}
    Gemini["Gemini"]
    Groq["Groq"]
    Local["Deterministic local fallback"]
    Safety["Structured validation and safety review"]
  end

  subgraph Data["Data and platform services"]
    DB[("SQLite local / PostgreSQL production")]
    Firebase["Firebase Auth and Cloud Messaging"]
    External["External store, product and metadata sources"]
    Media["Recipe gallery and live media jobs"]
  end

  User --> PWA
  PWA --> Native
  PWA <--> SW
  PWA --> Gateway

  Gateway --> Identity
  Gateway --> RecipeAPI
  Gateway --> CommerceAPI
  Gateway --> LiveAPI
  Gateway --> PushAPI
  Gateway --> AdminAPI

  RecipeAPI --> RecipeSvc
  RecipeAPI --> PantrySvc
  CommerceAPI --> ShopSvc
  LiveAPI --> LiveSvc
  Identity --> ProfileSvc
  PushAPI --> NotificationSvc
  AdminAPI --> ProfileSvc

  RecipeSvc --> Selector
  Selector --> Gemini
  Selector --> Groq
  Selector --> Local
  Gemini --> Safety
  Groq --> Safety
  Local --> Safety
  Safety --> RecipeSvc

  RecipeSvc --> DB
  PantrySvc --> DB
  ShopSvc --> DB
  LiveSvc --> DB
  ProfileSvc --> DB
  ShopSvc --> External
  RecipeSvc --> Media
  LiveSvc --> Media
  Identity --> Firebase
  NotificationSvc --> Firebase
  Firebase --> Native
```

## Architectural responsibilities

- **Client and device layer:** Delivers the responsive cooking experience, offline behavior, timers, camera-assisted flows, and notification handling.
- **FastAPI application layer:** Serves the PWA and exposes bounded API surfaces for identity, recipes, commerce, live cooking, notifications, and administration.
- **Domain services:** Encapsulate recipe, pantry, shopping, collaboration, profile, and notification workflows.
- **AI orchestration:** Selects a configured model provider, validates structured recipe output, and falls back to deterministic local generation when needed.
- **Data and platform services:** Persist application state and integrate authentication, messaging, media jobs, and product/store metadata.

## Primary request flow

1. A user acts through the PWA.
2. FastAPI routes the request to the appropriate domain API and service.
3. Recipe requests enter AI provider selection and always retain a local fallback path.
4. Services persist state or call external platform integrations.
5. The API returns structured data to the PWA; Firebase handles asynchronous push delivery.
