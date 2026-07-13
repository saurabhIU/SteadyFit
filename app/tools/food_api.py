"""USDA FoodData Central lookup — grounds macro math in real data."""
import requests
from app.config import settings

BASE = "https://api.nal.usda.gov/fdc/v1/foods/search"


def lookup_food(query: str, k: int = 2) -> list[str]:
    if not settings.usda_api_key:
        return ["[usda] no API key configured — using model estimate only"]
    try:
        r = requests.get(BASE, params={"query": query, "pageSize": k,
                                       "api_key": settings.usda_api_key}, timeout=10)
        foods = r.json().get("foods", [])
        out = []
        for f in foods:
            n = {x["nutrientName"]: x["value"] for x in f.get("foodNutrients", [])}
            out.append(f"[usda:{f['description']}] kcal={n.get('Energy')} "
                       f"protein={n.get('Protein')}g carbs={n.get('Carbohydrate, by difference')}g "
                       f"fat={n.get('Total lipid (fat)')}g (per 100g)")
        return out or ["[usda] no match"]
    except Exception:
        from app.security import safe_tool_error
        return [safe_tool_error("usda")]
