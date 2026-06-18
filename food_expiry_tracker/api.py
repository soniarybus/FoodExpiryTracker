# Requires: pip install requests
import requests
from models import Recipe

API_KEY = "26ad0ec9ea6642deaaeebd70858804aa"
_BASE_URL = "https://api.spoonacular.com/recipes/findByIngredients"
_INFO_URL  = "https://api.spoonacular.com/recipes/{}/information"


class APIError(Exception):
    """Raised for non-network Spoonacular failures (bad key, rate limit, bad response)."""
    pass


class OfflineError(APIError):
    """Raised when the device cannot reach the Spoonacular endpoint.
    Callers should fall back to locally cached recipes when they catch this."""
    pass


def get_recipes(items: list):
    if not items:
        return []

    ingredient_names = ",".join(item.name for item in items)

    try:
        response = requests.get(
            _BASE_URL,
            params={
                "apiKey":      API_KEY,
                "ingredients": ingredient_names,
                "number":      5,
                "ranking":     1,   
            },
            timeout=10,
        )
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError) as exc:
        raise OfflineError("No internet connection") from exc
    except Exception as exc:
        raise APIError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise APIError(
            f"Spoonacular returned {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise APIError("Could not parse API response as JSON") from exc

    recipes = []
    for entry in data:
        used_names   = [ing["name"] for ing in entry.get("usedIngredients",   [])]
        missed_names = [ing["name"] for ing in entry.get("missedIngredients", [])]
        recipes.append(Recipe(
            title=entry["title"],
            ingredients=used_names + missed_names,
            match_count=entry.get("usedIngredientCount", 0),
            is_cached=False,
            id=entry.get("id"),
        ))

    return recipes


def get_recipe_details(recipe_id):
    try:
        response = requests.get(
            _INFO_URL.format(recipe_id),
            params={"apiKey": API_KEY, "includeNutrition": "false"},
            timeout=10,
        )
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError) as exc:
        raise OfflineError("No internet connection") from exc
    except Exception as exc:
        raise APIError(f"Request failed: {exc}") from exc

    if response.status_code != 200:
        raise APIError(
            f"Spoonacular returned {response.status_code}: {response.text[:200]}"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise APIError("Could not parse API response as JSON") from exc

    ingredients = [
        ing["original"]
        for ing in data.get("extendedIngredients", [])
    ]

    steps = []
    instructions = data.get("analyzedInstructions", [])
    if instructions:
        for step in instructions[0].get("steps", []):
            steps.append((step["number"], step["step"]))

    return {
        "title": data.get("title", "Unknown"),
        "ingredients": ingredients,
        "steps": steps,
    }
