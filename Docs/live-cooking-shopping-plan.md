# GlucoPlate Live Cooking, Shopping, and Substitution Plan

## 1. Purpose

Connect GlucoPlate recipes, live cooking rooms, ingredient substitutions, local shopping information, prices, and shopping lists into one collaborative experience.

A user should be able to:

- Start a live cooking room from a recipe.
- Invite participants to collaborate through video, audio, chat, votes, and challenges.
- See each recipe ingredient as a purchasable or substitutable item.
- Find nearby stores that may carry an ingredient.
- See a last-known price with its source and observation date.
- Add ingredients to a GlucoPlate shopping list.
- Open a retailer product page or connected cart.
- Replace an ingredient because it is unavailable, unsuitable, or associated with an allergy.
- Preserve the decisions and substitutions in the cooking-session history and replay.

## 2. Product principles

1. **The recipe is the source of truth.** Shopping and substitutions remain attached to the specific recipe ingredient.
2. **Open data first, retailer integrations second.** Use open sources for normalization, product metadata, nutrition, stores, and price history. Add retailer APIs through adapters.
3. **Last-known price is not live price.** Every displayed price must show its source, location, observation time, and confidence.
4. **Allergy handling is stricter than ordinary substitution.** AI may suggest candidates, but it must not guarantee that a substitute is allergy-safe.
5. **Backend-authoritative decisions.** Points, votes, substitutions, shopping events, and permissions are validated by FastAPI.
6. **User-controlled purchasing.** GlucoPlate starts with shopping lists and retailer links. True cart/checkout support requires a retailer or commerce partner integration.
7. **Privacy by default.** Shopping lists, allergy profiles, live-room membership, and replays require authenticated access.

## 3. Recommended data sources

| Need | Source | Role | Limitation |
|---|---|---|---|
| Packaged ingredients, allergens, product attributes | [Open Food Facts](https://openfoodfacts.github.io/openfoodfacts-server/api/) | Product metadata, barcode lookup, ingredient and allergen signals | Community-contributed data can be incomplete or inaccurate; cache locally and display verification warnings |
| Standard food and nutrition data | [USDA FoodData Central](https://fdc.nal.usda.gov/api-guide) | Canonical foods, nutrients, serving data, nutrition calculations | Not a local inventory or retail-price API |
| Community price observations | [Open Prices](https://github.com/openfoodfacts/open-prices) | Last-known price history and price observations | Not guaranteed current price or inventory |
| Nearby stores | [OpenStreetMap/Overpass](https://dev.overpass-api.de/overpass-doc/en/preface/preface.html) | Grocery-store locations, names, addresses, and possible hours | Does not provide product availability or price |
| Retailer products and carts | Retailer or commerce partner APIs | Current products, availability, product URLs, carts, checkout | Terms, coverage, authentication, and partner approval vary |

No single open-source API reliably provides every retailer's live inventory, local pricing, and cart functionality. GlucoPlate should expose a provider-neutral adapter layer.

## 4. User experience

### Recipe detail

Each ingredient row should support:

- View normalized ingredient.
- View allergen flags.
- Show pantry status.
- Find nearby stores.
- Show last-known price.
- Add to shopping list.
- Choose a substitute.
- Open a retailer product link.
- Add to a connected retailer cart when supported.

Example:

> 2 tablespoons soy sauce  
> Pantry: Missing  
> Last known local price: $3.49 at Wegmans  
> Observed: July 15, 2026  
> Actions: Add to list · Find substitutes · View stores

### Live cooking room

During a live session:

1. The current cooking step is visible to everyone.
2. Participants can mark ingredients as available or missing.
3. A missing ingredient can start a substitution challenge.
4. Participants suggest or vote on alternatives.
5. The host confirms the selected replacement.
6. The recipe state, shopping list, points, feed, and replay timeline are updated.
7. The selected substitution is shown in the final session history.

Example challenge:

> We are missing soy sauce. Choose the best available substitute.

Possible candidates:

- Tamari
- Coconut aminos
- Fish sauce
- Worcestershire sauce
- Salt plus mushroom broth

The backend records the vote and host confirmation. It does not let the browser award points or finalize a substitution by itself.

## 5. Allergy and substitution rules

### Ordinary substitution

Used when an ingredient cannot be found or the user simply prefers another option.

Examples:

- Parsley → cilantro, chervil, or celery leaves.
- Heavy cream → milk plus butter, Greek yogurt, or coconut milk.
- Soy sauce → tamari or coconut aminos.

The system should explain the cooking impact:

- Flavor
- Texture
- Salt level
- Cooking temperature
- Required quantity adjustment

### Allergy substitution

Used when a user has selected or reported an allergy.

Required behavior:

1. Match the recipe ingredient to canonical allergen tags.
2. Match candidate products against available ingredient and allergen data.
3. Remove known conflicting candidates.
4. Display missing or uncertain allergen information.
5. Warn about cross-contact and label verification.
6. Require user confirmation before applying the replacement.
7. Preserve the reason for the change in the recipe/session history.

Do not display “allergy-safe” as an absolute claim. Use language such as:

> This candidate may avoid the selected allergen based on available data. Verify the package label and manufacturer information.

Open Food Facts explicitly notes that its data is contributed by users and is not guaranteed to be complete or reliable. The app must treat it as a signal, not a medical guarantee.

## 6. Price and availability model

Every price observation must include:

```text
price
currency
store
location
source
observed_at
availability
confidence
product_id
```

Display one of:

- Live price
- Recently checked
- Last known price
- Community-submitted price
- Price unavailable
- Store link only

Never display an undated price.

Suggested confidence rules:

- **High:** current retailer response for the selected store.
- **Medium:** recent product or price observation for the same location.
- **Low:** older, community-submitted, nearby, or category-level estimate.
- **Unknown:** no reliable product-price match.

## 7. Shopping behavior

### Phase 1: GlucoPlate shopping list

The first release should support:

- Add ingredient from a recipe.
- Add all missing ingredients.
- Group items by store.
- Track quantity, unit, recipe, and substitution.
- Share a list with participants.
- Mark purchased, skipped, or unavailable.
- Notify participants when the list changes.

### Phase 2: Retailer product links

For matched products, provide:

- Product name.
- Package size.
- Brand.
- Price observation.
- Availability status.
- Retailer URL.
- Last checked timestamp.

The user completes the purchase on the retailer site or app.

### Phase 3: Connected carts

Support true “Add to cart” only when a retailer or commerce partner provides:

- OAuth/account connection.
- Store or delivery location.
- External product ID.
- Product availability.
- Cart mutation endpoint.
- Substitution preferences.
- Checkout redirect.

Until then, call the action **Add to shopping list** or **Shop at retailer**.

## 8. Technical architecture

```text
Recipe ingredient
  -> Ingredient normalization
  -> Product/allergen matching
  -> Store and price lookup
  -> Shopping list
  -> Retailer link or connected cart

Live cooking room
  -> Missing-ingredient event
  -> Substitution challenge
  -> Participant votes
  -> Backend validation
  -> Host confirmation
  -> Recipe/session/list/feed/replay updates
```

Existing GlucoPlate responsibilities:

- **FastAPI:** authentication checks, recipes, business logic, normalization, provider adapters, shopping lists, substitutions, events.
- **Firebase:** authentication/session linkage, user-scoped data, push notifications.
- **PostgreSQL:** canonical ingredients, recipe ingredients, stores, price observations, shopping lists, live-session events, replay metadata.
- **Redis:** live room presence, WebSocket fan-out, short-lived search/cache results, challenge timers.
- **Video provider:** Daily for the first live-room implementation, with provider-neutral room records.
- **Replay storage:** private Cloudflare R2 objects or provider recording storage, accessed through authenticated short-lived URLs.
- **Gemini:** explanation and ranking assistance for substitutions, never final allergy authorization.

## 9. Service modules

```text
app/services/
  ingredient_normalizer.py
  food_data_service.py
  product_match_service.py
  allergen_service.py
  substitution_service.py
  store_locator_service.py
  price_observation_service.py
  shopping_list_service.py
  retailer_adapters/
    base.py
    open_food_facts.py
    open_prices.py
    usda.py
    openstreetmap.py
```

Retailer adapters should expose a consistent interface:

```text
search_products(ingredient, location)
get_product(product_id)
get_availability(product_id, store_id)
get_price(product_id, store_id)
get_product_url(product_id)
create_cart(user, store_id)
add_to_cart(cart_id, product_id, quantity)
get_checkout_url(cart_id)
```

## 10. Database model

### CanonicalIngredient

- id
- name
- aliases
- category
- allergen_tags
- substitution_group
- created_at
- updated_at

### RecipeIngredient

- id
- recipe_id
- canonical_ingredient_id
- quantity
- unit
- preparation_note
- optional
- sort_order

### IngredientProduct

- id
- canonical_ingredient_id
- source
- external_product_id
- barcode
- product_name
- brand
- package_size
- ingredient_text
- allergen_data
- product_url
- updated_at

### Store

- id
- source
- external_store_id
- name
- address
- latitude
- longitude
- opening_hours
- updated_at

### IngredientPriceObservation

- id
- ingredient_product_id
- store_id
- price
- currency
- availability
- source
- observed_at
- confidence

### ShoppingList

- id
- user_id
- recipe_id
- cooking_session_id
- name
- status
- created_at
- updated_at

### ShoppingListItem

- id
- shopping_list_id
- recipe_ingredient_id
- selected_product_id
- quantity
- unit
- status
- substitution_used
- purchased_at

### CookingSession

- id
- recipe_id
- host_user_id
- provider
- provider_room_id
- visibility
- status
- replay_status
- replay_object_key
- started_at
- ended_at

### CookingEvent

- id
- session_id
- actor_user_id
- event_type
- payload_json
- created_at

The `cooking_session_id` on a shopping list connects live decisions, substitutions, purchases, activity-feed events, and replay history.

## 11. API outline

```text
GET    /api/ingredients/{id}
GET    /api/ingredients/{id}/products
GET    /api/ingredients/{id}/stores
GET    /api/ingredients/{id}/prices
GET    /api/ingredients/{id}/substitutions

POST   /api/recipes/{recipe_id}/shopping-list
POST   /api/shopping-lists
GET    /api/shopping-lists
PATCH  /api/shopping-lists/{list_id}/items/{item_id}
DELETE /api/shopping-lists/{list_id}/items/{item_id}

POST   /api/cooking/sessions/{session_id}/ingredient-events
POST   /api/cooking/sessions/{session_id}/challenges
POST   /api/cooking/challenges/{challenge_id}/votes
POST   /api/cooking/sessions/{session_id}/substitutions
POST   /api/cooking/sessions/{session_id}/shopping-list/sync

POST   /api/retailers/{retailer}/cart
POST   /api/retailers/{retailer}/cart/items
GET    /api/retailers/{retailer}/checkout
```

## 12. Delivery phases

### Phase 1 — Ingredient foundation

- [ ] Define canonical ingredient schema.
- [ ] Normalize existing recipe ingredients.
- [ ] Add aliases, units, categories, and substitution groups.
- [ ] Add recipe-ingredient IDs.
- [ ] Add allergy-profile data model.
- [ ] Add data-source attribution fields.

### Phase 2 — Open food data

- [ ] Add Open Food Facts adapter.
- [ ] Add USDA FoodData Central adapter.
- [ ] Add local caching and rate-limit protection.
- [ ] Store product and allergen snapshots.
- [ ] Add product barcode support.
- [ ] Add source-quality and verification labels.

### Phase 3 — Stores and prices

- [ ] Add OpenStreetMap store lookup.
- [ ] Add Open Prices observations.
- [ ] Add location-based search.
- [ ] Show price date, source, and confidence.
- [ ] Add stale-price handling.
- [ ] Add user price correction/reporting.

### Phase 4 — Shopping lists

- [ ] Add recipe shopping list generation.
- [ ] Add pantry-aware missing-item filtering.
- [ ] Add shared lists for cooking-room participants.
- [ ] Add purchased, skipped, and unavailable statuses.
- [ ] Add Firebase push updates for list changes.

### Phase 5 — Substitution engine

- [ ] Implement deterministic substitution rules.
- [ ] Add allergy filtering.
- [ ] Add cooking-impact explanations.
- [ ] Add AI ranking with structured output.
- [ ] Require confirmation for allergy-related changes.
- [ ] Log every applied substitution.

### Phase 6 — Live-room integration

- [ ] Connect ingredient events to the video room.
- [ ] Add missing-ingredient challenges.
- [ ] Add voting and host confirmation.
- [ ] Award backend-controlled points.
- [ ] Publish activity-feed events.
- [ ] Include substitutions in replay timeline.

### Phase 7 — Retailer links and carts

- [ ] Add product links.
- [ ] Add retailer adapter interface.
- [ ] Select first retailer/commerce partner.
- [ ] Add OAuth account connection if needed.
- [ ] Add cart creation and product insertion.
- [ ] Add checkout redirect.
- [ ] Display final retailer price and substitution terms.

## 13. Acceptance criteria

### Recipe integration

- Every recipe ingredient has a stable internal identifier.
- A shopping-list item points back to the recipe ingredient.
- A substitution updates the cooking session without destroying the original recipe.

### Price quality

- Every price displays source and observation time.
- Stale prices are visibly labeled.
- Missing prices do not produce fabricated estimates.
- Store-specific availability is never inferred solely from a generic product record.

### Allergy safety

- Allergy-related candidates are filtered before display.
- Unknown allergen data is visible to the user.
- The system never guarantees allergy safety.
- Applied allergy substitutions require confirmation and are logged.

### Live collaboration

- Participants can suggest and vote on substitutions.
- The host confirms the selected option.
- The final choice updates the recipe, shopping list, activity feed, and history.
- Points are calculated and awarded by the backend.

### Privacy

- Shopping lists require authentication.
- Allergy profiles are private.
- Replay access is authorized for the host and permitted participants.
- Retailer tokens and cart credentials are never exposed to the frontend.

## 14. Initial implementation decision

Build the first version with:

- Open Food Facts
- USDA FoodData Central
- OpenStreetMap
- Open Prices
- FastAPI shopping-list and substitution services
- PostgreSQL canonical ingredient and price tables
- Redis live-room state
- Firebase notifications
- Retailer product links before true carts

This delivers useful local shopping and collaboration without making GlucoPlate dependent on a single retailer. True cart support can be added through an adapter after the recipe, ingredient, substitution, and shopping-list foundations are stable.
