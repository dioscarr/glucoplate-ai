import re
from typing import List, Dict

# Try to use Copilot SDK when available for better normalization; otherwise fallback.
try:
    import copilot  # type: ignore
    HAS_COPILOT = True
except Exception:
    HAS_COPILOT = False


def _rule_normalize(ingredient: str) -> Dict:
    # simple regex-based parsing: quantity, unit, name, descriptors
    m = re.match(r"^\s*(?:(\d+\/\d+|\d+\.?\d*)\s*)?(?:(cup|cups|tsp|tbsp|tablespoon|teaspoon|oz|ounce|g|kg|lb|pound)s?\s*)?(.*)$", ingredient.strip(), re.I)
    qty = m.group(1) if m else None
    unit = m.group(2) if m else None
    rest = m.group(3) if m else ingredient
    # split descriptors like "crushed red pepper flakes" into tokens
    tokens = re.split(r"[,()\-]\s*", rest)
    name = tokens[0]
    descriptors = [t for t in tokens[1:] if t]
    search_terms = [name] + descriptors
    return {
        'original': ingredient,
        'quantity': qty,
        'unit': unit,
        'name': name.strip(),
        'descriptors': descriptors,
        'search_terms': search_terms,
    }


def normalize_ingredients(ingredients: List[str]) -> List[Dict]:
    if HAS_COPILOT:
        # Attempt a lightweight Copilot prompt (best effort); fallback to rule parser on failure
        try:
            prompt = {
                'ingredients': ingredients,
                'instruction': 'Return a JSON array of normalized ingredient objects with fields: original, quantity, unit, name, descriptors, search_terms.'
            }
            # This is a placeholder for copilot usage; actual SDK invocation depends on runtime.
            out = copilot.run(prompt)  # type: ignore
            # Expect out to be JSON-like; try to extract
            if isinstance(out, list):
                return out
        except Exception:
            pass
    # Fallback
    return [_rule_normalize(i) for i in ingredients]
