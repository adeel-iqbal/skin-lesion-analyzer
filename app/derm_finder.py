import os
import httpx
from dotenv import load_dotenv

load_dotenv()
PLACES_KEY = os.getenv("GOOGLE_PLACES_API_KEY")


async def find_dermatologists(lat: float, lng: float, radius: int = 5000) -> list[dict]:
    if not PLACES_KEY:
        return []

    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lng}",
        "radius": radius,
        "keyword": "dermatologist",
        "type": "doctor",
        "key": PLACES_KEY,
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params, timeout=10)
        data = resp.json()

    results = []
    for place in data.get("results", [])[:5]:
        results.append({
            "name": place.get("name", ""),
            "address": place.get("vicinity", ""),
            "rating": place.get("rating", "N/A"),
            "open_now": place.get("opening_hours", {}).get("open_now", None),
            "place_id": place.get("place_id", ""),
            "maps_url": f"https://www.google.com/maps/place/?q=place_id:{place.get('place_id', '')}",
        })

    return results
