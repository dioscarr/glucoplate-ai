from pydantic import BaseModel, Field


class StoreSearchRequest(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int = Field(default=5000, ge=500, le=50000)
    query: str = Field(default="grocery")


class Store(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    address: str | None = None
    store_type: str | None = None
    website: str | None = None
    phone: str | None = None
    facebook: str | None = None
    opening_hours: str | None = None
    source: str = "openstreetmap"


class ProductSearchRequest(BaseModel):
    ingredient: str
    store_id: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ProductAvailability(BaseModel):
    ingredient: str
    product_name: str | None = None
    brand: str | None = None
    barcode: str | None = None
    image_url: str | None = None
    price: float | None = None
    currency: str | None = None
    availability: str = "unknown"
    store_name: str | None = None
    source: str
    notes: list[str] = Field(default_factory=list)
