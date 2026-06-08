from __future__ import annotations

import json
from urllib.parse import urlencode


ALLOWED_PRICE_AREAS = {"DK1", "DK2"}
ALLOWED_DATASETS = {
    "DayAheadPrices",
    "ElectricityProdex5MinRealtime",
}
BASE_URL = "https://api.energidataservice.dk/dataset"
MIN_LIMIT = 1
MAX_LIMIT = 10_000


def build_eds_url(dataset: str, price_area: str | None = None, limit: int = 100) -> str:
    """Build a read-only Energi Data Service dataset request URL."""
    if dataset not in ALLOWED_DATASETS:
        raise ValueError(f"Unsupported Energi Data Service dataset: {dataset}")

    if not isinstance(limit, int) or isinstance(limit, bool):
        raise ValueError("Limit must be an integer")

    if limit < MIN_LIMIT or limit > MAX_LIMIT:
        raise ValueError(f"Limit must be between {MIN_LIMIT} and {MAX_LIMIT}")

    query_params: dict[str, str | int] = {"limit": limit}

    if price_area is not None:
        if price_area not in ALLOWED_PRICE_AREAS:
            raise ValueError(f"Unsupported Energi Data Service price area: {price_area}")

        query_params["filter"] = json.dumps(
            {"PriceArea": [price_area]},
            separators=(",", ":"),
        )

    return f"{BASE_URL}/{dataset}?{urlencode(query_params)}"


def extract_records(payload: dict) -> list[dict]:
    """Extract the records list from an Energi Data Service response payload."""
    records = payload.get("records")

    if not isinstance(records, list):
        raise ValueError("Energi Data Service payload must include a records list")

    return records
