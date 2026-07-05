# Store, Map, Price, and Availability Strategy

## Goal

Allow users to search for nearby grocery stores based on their browser location, view stores on a side-by-side map/list layout, and click recipe ingredients to check product matches, approximate pricing, and availability.

## MVP Free/Open API Strategy

### Store Discovery

Use OpenStreetMap through the Overpass API.

Capabilities:

- Find supermarkets, grocery stores, and convenience stores near latitude/longitude.
- Return store names, coordinates, and address tags when available.

Limitations:

- No live product inventory.
- No live prices.
- Data quality depends on OpenStreetMap contributors.

### Product Metadata

Use Open Food Facts.

Capabilities:

- Product names
- Brands
- Barcodes
- Images
- Ingredient and nutrition metadata when available

Limitations:

- Usually no store-specific price.
- Usually no live availability.

### Price and Availability

Real-time grocery pricing and availability usually requires retailer-specific APIs, partner access, affiliate APIs, or scraping, which should be avoided unless explicitly permitted.

MVP behavior:

- Return product matches.
- Mark price as `null`.
- Mark availability as `unknown`.
- Explain source limitations clearly.

Future adapters:

- Kroger API
- Retailer partner APIs
- Open Food Facts Open Prices
- User-submitted price observations
- Cached manually entered local prices

## UX Concept

```text
Top Search Bar
  - Search recipe, ingredient, or store
  - Use my location button

Main Layout
  Left Panel: Store List + Ingredient/Product Cards
  Right Panel: Map

Interactions
  - Click recipe ingredient
  - Search product metadata
  - Show product cards
  - Show price/availability status
  - Click store marker
  - Highlight store in list
```

## API Contracts

### POST /api/stores/search

Input:

```json
{
  "latitude": 43.0,
  "longitude": -76.0,
  "radius_meters": 5000,
  "query": "grocery"
}
```

Output:

```json
[
  {
    "id": "123",
    "name": "Example Grocery",
    "latitude": 43.0,
    "longitude": -76.0,
    "address": "123 Main St",
    "store_type": "supermarket",
    "source": "openstreetmap"
  }
]
```

### POST /api/products/search

Input:

```json
{
  "ingredient": "black beans",
  "store_id": "optional",
  "latitude": 43.0,
  "longitude": -76.0
}
```

Output:

```json
[
  {
    "ingredient": "black beans",
    "product_name": "Example Black Beans",
    "brand": "Example Brand",
    "barcode": "0000000000000",
    "image_url": "https://example.com/image.jpg",
    "price": null,
    "currency": null,
    "availability": "unknown",
    "store_name": null,
    "source": "openfoodfacts",
    "notes": ["Price and availability require a retailer-specific API."]
  }
]
```

## Copilot Web Search Option

The Copilot SDK can be used as an AI research assistant when the configured environment supports web/search tooling. For production-grade behavior, deterministic API adapters remain preferred for stores, maps, and product records because they return structured, repeatable data.
