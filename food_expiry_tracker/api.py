import re #for HTML
import threading 
import unicodedata #special characters
from concurrent.futures import ThreadPoolExecutor #multiple recipes

import requests
from models import Recipe

API_KEY = "26ad0ec9ea6642deaaeebd70858804aa"
_BASE_URL = "https://api.spoonacular.com/recipes/findByIngredients"
_INFO_URL  = "https://api.spoonacular.com/recipes/{}/information"


class APIError(Exception):
    pass


class OfflineError(APIError):
    pass


_HTML_TAG_RE = re.compile(r"<[^>]+>") #deletes weird HTML tags


def clean_ingredient(text): #cleans ingredients
    if not text:
        return ""
    text = str(text)
    text = re.sub(r'\\u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), text)
    text = text.replace('\\"', '"').replace("\\'", "'") #undo escaped quotes too
    text = unicodedata.normalize("NFC", text)
    text = text.strip().strip("[]").strip().strip("\"'").strip()
    text = text.replace("\\", "").strip()
    return text


def is_online(timeout: float = 3.0): #shorter timeout
    try:
        requests.get("https://api.spoonacular.com", timeout=timeout)
        return True
    except (requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            OSError):
        return False
    except Exception: #other issues
        return True


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

    entries = []
    for entry in data:
        try:
            used_names   = [ing["name"] for ing in entry.get("usedIngredients",   [])]
            missed_names = [ing["name"] for ing in entry.get("missedIngredients", [])]
            ingredients  = [clean_ingredient(n) for n in used_names + missed_names]
            entries.append({
                "recipe_id":   entry.get("id"), #important 
                "title":       entry["title"],
                "ingredients": [i for i in ingredients if i],
                "match_count": entry.get("usedIngredientCount", 0),
            })
        except Exception:
            continue

    if not entries:
        return []
    with ThreadPoolExecutor(max_workers=len(entries)) as executor:
        instructions_list = list(
            executor.map(lambda e: _fetch_instructions(e["recipe_id"]), entries)
        )

    return [
        Recipe(
            title=e["title"],
            ingredients=e["ingredients"],
            match_count=e["match_count"],
            is_cached=False,
            recipe_id=e["recipe_id"],
            instructions=instructions,
        )
        for e, instructions in zip(entries, instructions_list)
    ]


def _fetch_instructions(recipe_id):
    try:
        info_response = requests.get(
            _INFO_URL.format(recipe_id),
            params={"apiKey": API_KEY, "includeNutrition": "false"},
            timeout=10,
        )
        if info_response.status_code != 200:
            return None
        info_data = info_response.json()
        analyzed = info_data.get("analyzedInstructions", [])
        if analyzed and analyzed[0].get("steps"):
            steps = [step["step"] for step in analyzed[0]["steps"]]
            if steps:
                return "\n".join(steps)
        plain = _HTML_TAG_RE.sub("", info_data.get("instructions") or "").strip()
        return plain or None
    except Exception:
        return None
