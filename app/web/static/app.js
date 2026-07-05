const state = {
  latitude: 43.0481,
  longitude: -76.1474,
  stores: [],
  markers: [],
  recipe: null,
};

const map = L.map("map").setView([state.latitude, state.longitude], 12);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
  maxZoom: 19,
  attribution: "&copy; OpenStreetMap contributors",
}).addTo(map);

let userMarker = L.marker([state.latitude, state.longitude]).addTo(map).bindPopup("Default search area");

const recipeGoal = document.getElementById("recipeGoal");
const generateRecipeBtn = document.getElementById("generateRecipeBtn");
const useLocationBtn = document.getElementById("useLocationBtn");
const recipeResult = document.getElementById("recipeResult");
const aiProvider = document.getElementById("aiProvider");
const storeList = document.getElementById("storeList");
const productList = document.getElementById("productList");
const locationStatus = document.getElementById("locationStatus");

generateRecipeBtn.addEventListener("click", generateRecipe);
useLocationBtn.addEventListener("click", useCurrentLocation);

async function generateRecipe() {
  setLoading(recipeResult, "Generating recipe...");

  const response = await fetch("/api/recipes/generate?use_ai=true", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      goal: recipeGoal.value || "balanced dinner",
      servings: 2,
      max_carbs_per_serving: 45,
      preferences: ["easy", "balanced"],
      avoid_ingredients: [],
      culture: inferCulture(recipeGoal.value),
    }),
  });

  const recipe = await response.json();
  state.recipe = recipe;
  aiProvider.textContent = recipe.ai_provider || "unknown";
  renderRecipe(recipe);
}

function renderRecipe(recipe) {
  const ingredients = recipe.ingredients || [];
  recipeResult.classList.remove("muted");
  recipeResult.innerHTML = `
    <h3>${escapeHtml(recipe.title)}</h3>
    <p>${escapeHtml(recipe.summary)}</p>
    <div class="ingredients">
      ${ingredients
        .map(
          (ingredient) =>
            `<button class="ingredient-btn" onclick="lookupIngredient('${escapeAttribute(ingredient)}')">${escapeHtml(ingredient)}</button>`
        )
        .join("")}
    </div>
    <p><strong>Estimated carbs:</strong> ${recipe.nutrition_estimate?.carbs_g ?? "?"}g</p>
    <p class="warning">${escapeHtml(recipe.safety_review?.disclaimer || "Nutrition estimates are approximate.")}</p>
  `;
}

async function useCurrentLocation() {
  locationStatus.textContent = "requesting location";

  if (!navigator.geolocation) {
    locationStatus.textContent = "not supported";
    await searchStores();
    return;
  }

  navigator.geolocation.getCurrentPosition(
    async (position) => {
      state.latitude = position.coords.latitude;
      state.longitude = position.coords.longitude;
      locationStatus.textContent = "location set";
      map.setView([state.latitude, state.longitude], 13);
      userMarker.setLatLng([state.latitude, state.longitude]).bindPopup("Your location").openPopup();
      await searchStores();
    },
    async () => {
      locationStatus.textContent = "using default";
      await searchStores();
    }
  );
}

async function searchStores() {
  setLoading(storeList, "Searching nearby stores...");

  const response = await fetch("/api/stores/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      latitude: state.latitude,
      longitude: state.longitude,
      radius_meters: 6000,
      query: "grocery",
    }),
  });

  state.stores = await response.json();
  renderStores(state.stores);
  renderStoreMarkers(state.stores);
}

function renderStores(stores) {
  if (!stores.length) {
    storeList.innerHTML = "No stores found.";
    return;
  }

  storeList.classList.remove("muted");
  storeList.innerHTML = stores
    .map(
      (store, index) => `
        <div class="item-card" onclick="focusStore(${index})">
          <h3>${escapeHtml(store.name)}</h3>
          <p>${escapeHtml(store.address || "Address unavailable")}</p>
          <p><strong>Type:</strong> ${escapeHtml(store.store_type || "food store")}</p>
        </div>
      `
    )
    .join("");
}

function renderStoreMarkers(stores) {
  state.markers.forEach((marker) => marker.remove());
  state.markers = [];

  stores.forEach((store, index) => {
    const marker = L.marker([store.latitude, store.longitude])
      .addTo(map)
      .bindPopup(`<strong>${escapeHtml(store.name)}</strong><br>${escapeHtml(store.address || "")}`);
    marker.on("click", () => focusStore(index));
    state.markers.push(marker);
  });
}

function focusStore(index) {
  const store = state.stores[index];
  if (!store) return;
  map.setView([store.latitude, store.longitude], 15);
  state.markers[index]?.openPopup();
}

async function lookupIngredient(ingredient) {
  setLoading(productList, `Searching products for ${ingredient}...`);

  const response = await fetch("/api/products/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      ingredient,
      latitude: state.latitude,
      longitude: state.longitude,
    }),
  });

  const products = await response.json();
  renderProducts(products);
}

function renderProducts(products) {
  productList.classList.remove("muted");
  productList.innerHTML = products
    .map((product) => {
      const image = product.image_url || "";
      const price = product.price ? `${product.currency || "$"}${product.price}` : "Price unknown";
      const availability = product.availability || "unknown";
      return `
        <div class="item-card product-row">
          <img src="${escapeAttribute(image)}" alt="" onerror="this.style.display='none'" />
          <div>
            <h3>${escapeHtml(product.product_name || product.ingredient)}</h3>
            <p>${escapeHtml(product.brand || "Brand unavailable")}</p>
            <p><strong>${escapeHtml(price)}</strong> · Availability: ${escapeHtml(availability)}</p>
            <p>${escapeHtml((product.notes || [])[0] || "")}</p>
          </div>
        </div>
      `;
    })
    .join("");
}

function inferCulture(value) {
  const text = (value || "").toLowerCase();
  if (text.includes("dominican") || text.includes("latin")) return "Dominican";
  return null;
}

function setLoading(element, message) {
  element.classList.add("muted");
  element.textContent = message;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("`", "&#096;");
}

searchStores();
