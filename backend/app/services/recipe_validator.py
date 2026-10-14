"""
Recipe Validator and Quality Reconciliation Engine for DishGenieAI.
Ensures:
1. Markdown and formatting cleanup.
2. Complete, actionable cooking instructions without heading artifacts or cut-off sentences.
3. Ingredient consistency between instruction text and ingredients list.
4. Intelligent, diet-aware culinary substitutions.
5. Dynamic, recipe-specific shopping list generation.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.schemas.recipe import Recipe, Substitution
from app.services.ingredient_normalizer import clean_text, normalize_token

logger = logging.getLogger(__name__)

# Common culinary items, aromatics, spices, and pantry essentials
# mapped to sensible quantity/preparation format when added to the ingredients list.
KNOWN_CULINARY_ITEMS: Dict[str, Dict[str, Any]] = {
    "fennel seeds": {"canonical": "Fennel seeds (saunf)", "default_qty": "1 tsp", "category": "spice"},
    "fennel": {"canonical": "Fennel seeds (saunf)", "default_qty": "1 tsp", "category": "spice"},
    "saunf": {"canonical": "Fennel seeds (saunf)", "default_qty": "1 tsp", "category": "spice"},
    "cumin seeds": {"canonical": "Cumin seeds (jeera)", "default_qty": "1 tsp", "category": "spice"},
    "cumin": {"canonical": "Cumin seeds (jeera)", "default_qty": "1 tsp", "category": "spice"},
    "jeera": {"canonical": "Cumin seeds (jeera)", "default_qty": "1 tsp", "category": "spice"},
    "mustard seeds": {"canonical": "Mustard seeds (rai)", "default_qty": "1 tsp", "category": "spice"},
    "mustard": {"canonical": "Mustard seeds (rai)", "default_qty": "1 tsp", "category": "spice"},
    "rai": {"canonical": "Mustard seeds (rai)", "default_qty": "1 tsp", "category": "spice"},
    "garlic": {"canonical": "Garlic, minced or crushed", "default_qty": "3-4 cloves", "category": "aromatic"},
    "cloves garlic": {"canonical": "Garlic, minced or crushed", "default_qty": "3-4 cloves", "category": "aromatic"},
    "ginger": {"canonical": "Fresh ginger, grated or minced", "default_qty": "1 inch", "category": "aromatic"},
    "adrak": {"canonical": "Fresh ginger, grated or minced", "default_qty": "1 inch", "category": "aromatic"},
    "onion": {"canonical": "Onion, finely chopped", "default_qty": "1 medium", "category": "produce"},
    "onions": {"canonical": "Onions, sliced", "default_qty": "2 medium", "category": "produce"},
    "tomato": {"canonical": "Tomatoes, chopped or pureed", "default_qty": "2 medium", "category": "produce"},
    "tomatoes": {"canonical": "Tomatoes, chopped or pureed", "default_qty": "2 medium", "category": "produce"},
    "papaya": {"canonical": "Raw/Green Papaya, peeled and cubed", "default_qty": "2 cups", "category": "produce"},
    "green chillies": {"canonical": "Green chillies, slit or chopped", "default_qty": "2-3", "category": "spice"},
    "green chilli": {"canonical": "Green chillies, slit", "default_qty": "2", "category": "spice"},
    "red chilli powder": {"canonical": "Red chilli powder", "default_qty": "1 tsp", "category": "spice"},
    "chilli powder": {"canonical": "Red chilli powder", "default_qty": "1 tsp", "category": "spice"},
    "dry red chillies": {"canonical": "Dry red chillies", "default_qty": "2-3", "category": "spice"},
    "turmeric powder": {"canonical": "Turmeric powder (haldi)", "default_qty": "1/2 tsp", "category": "spice"},
    "turmeric": {"canonical": "Turmeric powder (haldi)", "default_qty": "1/2 tsp", "category": "spice"},
    "coriander powder": {"canonical": "Coriander powder (dhania)", "default_qty": "1 tsp", "category": "spice"},
    "fresh coriander": {"canonical": "Fresh coriander leaves, chopped for garnish", "default_qty": "2 tbsp", "category": "herb"},
    "coriander leaves": {"canonical": "Fresh coriander leaves, chopped", "default_qty": "2 tbsp", "category": "herb"},
    "cilantro": {"canonical": "Fresh cilantro leaves, chopped", "default_qty": "2 tbsp", "category": "herb"},
    "curry leaves": {"canonical": "Fresh curry leaves", "default_qty": "1 sprig (8-10 leaves)", "category": "herb"},
    "kadi patta": {"canonical": "Fresh curry leaves", "default_qty": "1 sprig", "category": "herb"},
    "garam masala": {"canonical": "Garam masala powder", "default_qty": "1/2 tsp", "category": "spice"},
    "asafoetida": {"canonical": "Asafoetida (hing)", "default_qty": "1/4 tsp", "category": "spice"},
    "hing": {"canonical": "Asafoetida (hing)", "default_qty": "1/4 tsp", "category": "spice"},
    "fenugreek seeds": {"canonical": "Fenugreek seeds (methi)", "default_qty": "1/2 tsp", "category": "spice"},
    "methi seeds": {"canonical": "Fenugreek seeds (methi)", "default_qty": "1/2 tsp", "category": "spice"},
    "kasuri methi": {"canonical": "Kasuri methi (dried fenugreek leaves)", "default_qty": "1 tbsp", "category": "herb"},
    "cinnamon": {"canonical": "Cinnamon stick (dalchini)", "default_qty": "1 inch piece", "category": "spice"},
    "cloves": {"canonical": "Whole cloves (laung)", "default_qty": "3-4", "category": "spice"},
    "cardamom": {"canonical": "Green cardamom pods (elaichi)", "default_qty": "2 pods", "category": "spice"},
    "black pepper": {"canonical": "Black pepper, freshly crushed", "default_qty": "1/2 tsp", "category": "spice"},
    "mustard oil": {"canonical": "Mustard oil", "default_qty": "2 tbsp", "category": "oil"},
    "cooking oil": {"canonical": "Cooking oil", "default_qty": "2 tbsp", "category": "oil"},
    "oil": {"canonical": "Cooking oil", "default_qty": "2 tbsp", "category": "oil"},
    "ghee": {"canonical": "Ghee (clarified butter)", "default_qty": "1-2 tbsp", "category": "dairy"},
    "butter": {"canonical": "Butter", "default_qty": "1 tbsp", "category": "dairy"},
    "paneer": {"canonical": "Paneer cubes", "default_qty": "200g", "category": "dairy"},
    "curd": {"canonical": "Plain yogurt / curd, whisked", "default_qty": "1/2 cup", "category": "dairy"},
    "yogurt": {"canonical": "Plain yogurt / curd, whisked", "default_qty": "1/2 cup", "category": "dairy"},
    "salt": {"canonical": "Salt", "default_qty": "to taste", "category": "seasoning"},
    "amchur": {"canonical": "Amchur (dry mango powder)", "default_qty": "1/2 tsp", "category": "spice"},
    "dry mango powder": {"canonical": "Amchur (dry mango powder)", "default_qty": "1/2 tsp", "category": "spice"},
    "lemon juice": {"canonical": "Fresh lemon juice", "default_qty": "1 tsp", "category": "seasoning"},
    "lemon": {"canonical": "Lemon juice", "default_qty": "1/2 lemon", "category": "seasoning"},
    "water": {"canonical": "Water", "default_qty": "1 cup", "category": "liquid"},
    "sugar": {"canonical": "Sugar or jaggery", "default_qty": "1/2 tsp (optional)", "category": "seasoning"},
    "jaggery": {"canonical": "Jaggery (gud)", "default_qty": "1 tsp", "category": "seasoning"},
    "coconut milk": {"canonical": "Coconut milk", "default_qty": "1/2 cup", "category": "liquid"},
}

# Culinary Substitution Rules: mapping ingredient patterns to appropriate replacements with flavor/texture notes
CULINARY_SUBSTITUTIONS_KB: List[Dict[str, Any]] = [
    {
        "patterns": ["papaya", "green papaya", "raw papaya"],
        "ingredient": "Raw Papaya",
        "replacement": "Chayote squash or raw green mango - provides a similar firm, crisp bite in spiced curries (green mango adds slight pleasant tartness).",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["karela", "bitter gourd"],
        "ingredient": "Bitter Gourd (Karela)",
        "replacement": "Fenugreek greens (methi) or raw plantain/banana - gives earthy, mildly astringent flavor with gentler bitterness.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["fennel seeds", "fennel", "saunf"],
        "ingredient": "Fennel Seeds",
        "replacement": "Cumin seeds or a pinch of ground anise - gives warm aromatic sweetness without changing the spice backbone.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["garlic", "cloves garlic"],
        "ingredient": "Garlic",
        "replacement": "Asafoetida (hing) - a small pinch bloomed in hot oil provides rich allium depth without pungent garlic bite (Jain-diet friendly).",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["ginger", "fresh ginger"],
        "ingredient": "Fresh Ginger",
        "replacement": "Dry ginger powder (sonth) - use 1/4 tsp powder per inch of fresh ginger; flavor is slightly more concentrated and warming.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["paneer"],
        "ingredient": "Paneer",
        "replacement": "Extra-firm tofu, pressed and cubed - absorbs marinades and spices identically while remaining 100% plant-based and dairy-free.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["ghee"],
        "ingredient": "Ghee",
        "replacement": "Cold-pressed mustard oil or unrefined coconut oil - delivers aromatic richness and high heat tolerance while keeping the dish vegan.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["curd", "yogurt"],
        "ingredient": "Yogurt / Curd",
        "replacement": "Whisked coconut yogurt or cashew cream with a dash of lemon - provides creamy sour tang without dairy.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["fresh coriander", "cilantro", "coriander leaves"],
        "ingredient": "Fresh Coriander (Cilantro)",
        "replacement": "Fresh mint leaves or microgreens - mint imparts a brighter, cool finish compared to citrusy coriander.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["curry leaves", "kadi patta"],
        "ingredient": "Curry Leaves",
        "replacement": "Kaffir lime leaves or pinch of lime zest - offers citrus-herbal fragrance if fresh curry leaves are not available.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["tomato", "tomatoes"],
        "ingredient": "Tomatoes",
        "replacement": "Tamarind paste (1/2 tsp) or amchur (dry mango powder) mixed in water - adds fruity acidity for gravy balance.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["amchur", "dry mango powder"],
        "ingredient": "Amchur (Dry Mango Powder)",
        "replacement": "Fresh lemon or lime juice added at the end of cooking - brings bright acidity without darkening the gravy.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["capsicum", "bell pepper"],
        "ingredient": "Capsicum / Bell Pepper",
        "replacement": "Poblano pepper or tender zucchini - zucchini maintains gentle sweetness, while poblano adds smoky warmth.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["mustard oil"],
        "ingredient": "Mustard Oil",
        "replacement": "Groundnut (peanut) oil or sesame oil - retains earthy undertones if pungent mustard oil is unavailable.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
    {
        "patterns": ["coconut milk"],
        "ingredient": "Coconut Milk",
        "replacement": "Blended cashew cream (soaked cashews pureed with water) - provides luxurious body without altering spice profiles.",
        "diet_safe": ["Vegetarian", "Vegan", "Non-Vegetarian"],
    },
]

# Common action verbs that signify an actionable cooking instruction
ACTION_VERBS: Set[str] = {
    "heat", "add", "stir", "saute", "cook", "boil", "simmer", "mix", "combine",
    "temper", "season", "garnish", "roast", "grind", "blend", "chop", "slice",
    "dice", "whisk", "fold", "cover", "uncover", "drain", "rinse", "marinate",
    "bake", "fry", "deep-fry", "shallow-fry", "steam", "pressure", "serve", "pour",
    "turn", "reduce", "let", "toss", "crush", "splutter", "crackle", "warm", "spread",
}

# Regex to detect heading-only labels (e.g. "For the Papaya Curry:**", "Add Spices:**")
HEADING_LABEL_PATTERN = re.compile(
    r"^(?:(?:for\s+the|to\s+prepare|to\s+make|step\s+\d+|method|preparation|tempering|garnishing|for\s+tempering)\b.*[:\*]*|.*[:\*]{2,}$)",
    re.IGNORECASE,
)

# Regex to detect incomplete, hanging sentences
INCOMPLETE_SENTENCE_PATTERN = re.compile(
    r"\b(?:over\s+the|over\s+a|in\s+the|in\s+a|with\s+the|with\s+a|into\s+the|into\s+a|and\s+the|and\s+a|to\s+the|to\s+a|for\s+the|for\s+a|the|a|an|of|at|on|by|from|with|and|or|but|then|while|fresh|warm|hot|cold|some|few|pinch\s+of|sprinkle\s+of)\s*$",
    re.IGNORECASE,
)


def strip_markdown_formatting(text: str) -> str:
    """Removes stray markdown bold (**), italics (* or _), backticks, and section headers."""
    if not text:
        return ""
    # Remove code fences
    cleaned = re.sub(r"```[a-zA-Z]*", "", text)
    # Remove bold and italic markers
    cleaned = cleaned.replace("**", "").replace("__", "")
    # Remove leading markdown headers (###, ##, #)
    cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
    # Remove leading bullets or list numbering
    cleaned = re.sub(r"^[\s*•\-–—\d\.\)]+\s*", "", cleaned)
    # Normalize spaces
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def is_heading_or_label(text: str) -> bool:
    """
    Detects if a string is merely a section heading or sub-label rather than an actionable cooking step.
    Examples:
      - 'For the Papaya Curry:**' -> True
      - 'Prepare the Papaya and Tomato:**' -> True
      - 'Add Spices:**' -> True
      - 'Heat 2 tbsp oil in a pan and add cumin seeds.' -> False
    """
    raw = text.strip()
    clean = strip_markdown_formatting(raw).lower()

    if not clean:
        return True

    # If line ends with colon or double asterisks with colon
    if raw.endswith(":") or raw.endswith(":**") or raw.endswith(":*"):
        words = clean.split()
        if len(words) <= 6:
            # Check if it has an actionable sentence structure
            if not any(v in words for v in ["heat", "stir", "boil", "simmer", "cook", "fry"]):
                return True

    # Matches heading regex
    if HEADING_LABEL_PATTERN.match(raw) and len(clean.split()) <= 6:
        return True

    # Section markers
    if clean in {"ingredients", "instructions", "method", "steps", "preparation", "substitutions", "shopping list"}:
        return True

    return False


def is_incomplete_sentence(text: str) -> bool:
    """
    Detects if a string is an incomplete sentence cut off prematurely.
    Example: 'Sprinkle salt over the' -> True
    """
    clean = strip_markdown_formatting(text).strip()
    if not clean:
        return True

    # Check for cut-off prepositions or conjunctions
    if INCOMPLETE_SENTENCE_PATTERN.search(clean):
        return True

    # Ends with trailing comma or hyphen
    if clean.endswith(",") or clean.endswith("-") or clean.endswith("–"):
        return True

    # Suspiciously short and does not contain a verb or terminal punctuation
    words = clean.split()
    if len(words) <= 3 and not any(w.lower() in ACTION_VERBS for w in words):
        return True

    return False


def clean_instruction_step(step: str) -> Optional[str]:
    """
    Cleans an instruction step:
    - Strips markdown symbols
    - Rejects heading-only lines
    - Rejects cut-off sentences
    - Ensures proper sentence casing and terminal period
    """
    if not step:
        return None

    raw = step.strip()

    # Reject headings
    if is_heading_or_label(raw):
        return None

    # Reject incomplete fragments
    if is_incomplete_sentence(raw):
        # Check if it can be easily completed if it is common (e.g. "Sprinkle salt over the dish to taste.")
        if re.match(r"^sprinkle\s+salt\s+over\s+the\s*$", raw, re.IGNORECASE):
            return "Sprinkle salt over the dish to taste and stir well."
        return None

    cleaned = strip_markdown_formatting(raw)

    # Remove inline heading prefixes: e.g. "Step 1: Heat oil..." -> "Heat oil..."
    cleaned = re.sub(r"^(?:step\s*\d+\s*[:\-–.]\s*|method\s*[:\-–.]\s*)", "", cleaned, flags=re.IGNORECASE)

    if not cleaned or len(cleaned) < 5:
        return None

    # Ensure capitalized start
    cleaned = cleaned[0].upper() + cleaned[1:]

    # Ensure ending punctuation
    if not cleaned.endswith((".", "!", "?")):
        cleaned += "."

    return cleaned


def extract_culinary_mentions(text: str) -> Set[str]:
    """
    Scans recipe instructions to detect culinary ingredients, spices, aromatics,
    and garnishes mentioned in the text.
    """
    lower_text = " " + text.lower() + " "
    # Normalize punctuation for matching
    lower_text = re.sub(r"[^\w\s]", " ", lower_text)
    lower_text = re.sub(r"\s+", " ", lower_text)

    found_keys: Set[str] = set()

    # Sort known items by length descending so multi-word matches take precedence
    sorted_items = sorted(KNOWN_CULINARY_ITEMS.keys(), key=len, reverse=True)

    for item in sorted_items:
        # Match whole word boundary
        pattern = rf"\b{re.escape(item)}\b"
        if re.search(pattern, lower_text):
            found_keys.add(item)

    return found_keys


def is_ingredient_covered(mention: str, ingredient_list: List[str]) -> bool:
    """
    Checks if a detected culinary mention is already accounted for in the ingredient list.
    Handles partial matches, plurals, and canonical forms.
    """
    mention_clean = normalize_token(mention).lower()
    canonical_info = KNOWN_CULINARY_ITEMS.get(mention, {})
    canonical_clean = normalize_token(canonical_info.get("canonical", "")).lower()

    for item in ingredient_list:
        item_clean = normalize_token(item).lower()

        # Direct token match
        if mention_clean in item_clean or item_clean in mention_clean:
            return True

        if canonical_clean and (canonical_clean in item_clean or item_clean in canonical_clean):
            return True

        # Check key word overlap
        words_m = set(re.findall(r"\b[a-z]{3,}\b", mention_clean))
        words_i = set(re.findall(r"\b[a-z]{3,}\b", item_clean))
        if words_m and words_m.issubset(words_i):
            return True

    return False


def deduplicate_and_consolidate_ingredients(ingredients: List[str]) -> List[str]:
    """
    Consolidates duplicate ingredients, including equivalent names (e.g. Cumin seeds & Cumin seeds (jeera)).
    Keeps the more descriptive entry and avoids redundant duplicate lines.
    """
    consolidated: List[str] = []
    seen_tokens: Dict[str, int] = {}  # token -> index in consolidated

    unit_words = {"tsp", "tbsp", "cup", "cups", "medium", "large", "small", "chopped", "pureed", "diced", "sliced", "fresh", "pinch"}

    for item in ingredients:
        clean = strip_markdown_formatting(item).strip()
        if not clean:
            continue

        token = normalize_token(clean).lower()
        matched_idx = None
        p_words = set(token.split()) - unit_words

        for prev_token, idx in seen_tokens.items():
            if prev_token == token:
                matched_idx = idx
                break
            prev_core = set(prev_token.split()) - unit_words
            if p_words and prev_core and (p_words == prev_core or p_words.issubset(prev_core) or prev_core.issubset(p_words)):
                matched_idx = idx
                break

        if matched_idx is not None:
            existing = consolidated[matched_idx]
            if len(clean) > len(existing):
                consolidated[matched_idx] = clean
        else:
            seen_tokens[token] = len(consolidated)
            consolidated.append(clean)

    return consolidated


def reconcile_ingredients_with_instructions(
    ingredients: List[str],
    instructions: List[str],
    diet: str = "Vegetarian",
) -> Tuple[List[str], List[str]]:
    """
    Requirement 3: Fix ingredient consistency.
    Ensures every ingredient mentioned in instructions (e.g. fennel seeds, garlic, oil, cumin)
    is accounted for in the ingredients list. Consolidates duplicate ingredients.
    Returns:
        Tuple[List[str], List[str]]: (reconciled_ingredients, added_ingredient_names)
    """
    clean_ingredients = deduplicate_and_consolidate_ingredients(
        [strip_markdown_formatting(i) for i in ingredients if strip_markdown_formatting(i)]
    )
    instructions_text = " ".join(instructions)

    mentions = extract_culinary_mentions(instructions_text)
    added_names: List[str] = []

    is_vegan = diet.strip().lower() == "vegan"

    for mention in sorted(list(mentions)):
        # Skip water/air or generic cookware
        if mention in {"water"}:
            continue

        item_info = KNOWN_CULINARY_ITEMS.get(mention)
        if not item_info:
            continue

        # Respect vegan restrictions: do not reconcile dairy if recipe is vegan
        if is_vegan and item_info.get("category") == "dairy":
            continue

        if not is_ingredient_covered(mention, clean_ingredients):
            canonical = item_info["canonical"]
            default_qty = item_info["default_qty"]
            entry = f"{default_qty} {canonical}" if default_qty != "to taste" else f"{canonical} to taste"
            clean_ingredients.append(entry)
            added_names.append(canonical)
            logger.info(f"[RecipeValidator] Reconciled missing instruction ingredient: '{canonical}' -> '{entry}'")

    final_ingredients = deduplicate_and_consolidate_ingredients(clean_ingredients)
    return final_ingredients, added_names


def generate_culinary_substitutions(
    ingredients: List[str],
    diet: str = "Vegetarian",
    max_subs: int = 3,
) -> List[Substitution]:
    """
    Requirement 5: Fix possible substitutions.
    Generates intelligent culinary substitutions tailored to the actual ingredients present in the recipe.
    Respects dietary rules (e.g., no dairy for Vegan).
    """
    subs: List[Substitution] = []
    used_ingredients: Set[str] = set()
    user_diet = diet.strip().capitalize() if diet else "Vegetarian"

    ingredients_text = " ".join(ingredients).lower()

    for rule in CULINARY_SUBSTITUTIONS_KB:
        # Check dietary safety
        if user_diet not in rule.get("diet_safe", []):
            continue

        for pattern in rule["patterns"]:
            if re.search(rf"\b{re.escape(pattern)}\b", ingredients_text):
                ing_name = rule["ingredient"]
                if ing_name not in used_ingredients:
                    subs.append(Substitution(
                        ingredient=ing_name,
                        replacement=rule["replacement"],
                    ))
                    used_ingredients.add(ing_name)
                    break

        if len(subs) >= max_subs:
            break

    return subs


def generate_recipe_shopping_list(
    ingredients: List[str],
    confirmed_pantry: Optional[List[str]] = None,
) -> List[str]:
    """
    Requirement 6: Fix the shopping list.
    Derives the shopping list dynamically from the final validated recipe ingredients.
    Excludes ingredients confirmed as present in the user's pantry.
    """
    pantry_tokens: Set[str] = set()
    if confirmed_pantry:
        for p in confirmed_pantry:
            t = normalize_token(p).lower()
            if t:
                pantry_tokens.add(t)

    shopping_items: List[str] = []
    seen: Set[str] = set()

    for ing in ingredients:
        clean_ing = strip_markdown_formatting(ing).strip()
        if not clean_ing:
            continue

        # Skip water
        if clean_ing.lower() == "water" or clean_ing.lower().startswith("water "):
            continue

        # Check if present in confirmed pantry
        ing_token = normalize_token(clean_ing).lower()
        is_in_pantry = False
        if pantry_tokens:
            for p_tok in pantry_tokens:
                if p_tok in ing_token or ing_token in p_tok:
                    is_in_pantry = True
                    break

        if not is_in_pantry:
            norm_key = re.sub(r"[^\w]", "", clean_ing.lower())
            if norm_key not in seen:
                seen.add(norm_key)
                shopping_items.append(clean_ing)

    # If user provided no pantry or everything was matched, return all non-salt items
    if not shopping_items and ingredients:
        shopping_items = [strip_markdown_formatting(i) for i in ingredients if "salt" not in i.lower()]

    return shopping_items


def validate_and_refine_recipe(
    recipe: Recipe,
    confirmed_ingredients: Optional[List[str]] = None,
    diet: str = "Vegetarian",
    cuisine: Optional[str] = None,
) -> Tuple[Recipe, List[str]]:
    """
    Master recipe validation and refinement function.
    Performs full data quality pass:
      1. Strips all markdown artifacts from name, description, ingredients, and instructions.
      2. Validates instructions: removes headings, filters incomplete steps, deduplicates.
      3. Reconciles ingredients: ensures all instruction ingredients are in the ingredient list.
      4. Builds smart, diet-aware culinary substitutions if missing or generic.
      5. Generates recipe-specific shopping list derived from final ingredients.
    """
    warnings: List[str] = []

    # 1. Clean Recipe Name & Description
    clean_name = strip_markdown_formatting(recipe.name)
    clean_name = re.sub(r"^(?:recipe\s+name|name|title)[:\s\-–]+", "", clean_name, flags=re.IGNORECASE).strip()
    if not clean_name:
        clean_name = "Authentic Homemade Specialty"
        warnings.append("Missing recipe name; assigned default.")

    clean_desc = strip_markdown_formatting(recipe.description)
    if not clean_desc:
        clean_desc = f"A wholesome {cuisine or 'culinary'} dish prepared with fresh ingredients and fragrant spices."
        warnings.append("Missing description; generated default description.")

    # 2. Clean and Filter Instructions
    refined_instructions: List[str] = []
    seen_steps: Set[str] = set()

    for raw_step in recipe.instructions:
        cleaned_step = clean_instruction_step(raw_step)
        if cleaned_step:
            step_key = re.sub(r"[^\w]", "", cleaned_step.lower())
            if step_key not in seen_steps:
                seen_steps.add(step_key)
                refined_instructions.append(cleaned_step)
        else:
            warnings.append(f"Filtered invalid instruction step/heading: '{raw_step}'")

    if not refined_instructions:
        warnings.append("No valid cooking instructions remained after cleaning.")
        # Minimal safe fallback
        refined_instructions = [
            f"Prepare and wash all fresh vegetables thoroughly before cutting.",
            "Heat cooking oil in a pan, add whole spices, and sauté until aromatic.",
            "Add the main ingredients and seasonings, simmering until cooked through.",
            "Serve hot with your favorite accompaniment.",
        ]

    # 3. Clean and Reconcile Ingredients
    clean_ingredients = [strip_markdown_formatting(i) for i in recipe.ingredients if strip_markdown_formatting(i)]
    reconciled_ingredients, added_from_instructions = reconcile_ingredients_with_instructions(
        clean_ingredients, refined_instructions, diet=diet
    )
    if added_from_instructions:
        warnings.append(f"Reconciled missing ingredients from instructions: {added_from_instructions}")

    # Ensure confirmed user ingredients are reflected
    if confirmed_ingredients:
        for conf in confirmed_ingredients:
            if not is_ingredient_covered(conf, reconciled_ingredients):
                conf_clean = conf.replace("_", " ").title()
                reconciled_ingredients.insert(0, f"1-2 {conf_clean}")
                warnings.append(f"Added confirmed pantry ingredient: {conf_clean}")

    # 4. Refine Substitutions
    existing_subs = recipe.substitutions or []
    # Check if substitutions are generic defaults
    is_generic_sub = any(
        "seasonal squash" in s.replacement.lower() or "bell pepper, or zucchini" in s.replacement.lower()
        for s in existing_subs
    )

    if not existing_subs or is_generic_sub:
        refined_substitutions = generate_culinary_substitutions(reconciled_ingredients, diet=diet)
    else:
        # Validate existing substitutions
        refined_substitutions = []
        for s in existing_subs:
            clean_ing = strip_markdown_formatting(s.ingredient)
            clean_rep = strip_markdown_formatting(s.replacement)
            if clean_ing and clean_rep:
                refined_substitutions.append(Substitution(ingredient=clean_ing, replacement=clean_rep))

    # 5. Refine Shopping List
    existing_shop = recipe.shopping_list or []
    is_generic_shop = any(
        "cold-pressed oil" in s.lower() or "aromatic herbs / spices" in s.lower() or "pantry spices (" in s.lower()
        for s in existing_shop
    )

    if not existing_shop or is_generic_shop:
        refined_shopping_list = generate_recipe_shopping_list(reconciled_ingredients, confirmed_pantry=confirmed_ingredients)
    else:
        refined_shopping_list = [strip_markdown_formatting(i) for i in existing_shop if strip_markdown_formatting(i)]

    final_recipe = Recipe(
        name=clean_name,
        description=clean_desc,
        ingredients=reconciled_ingredients,
        instructions=refined_instructions,
        substitutions=refined_substitutions,
        shopping_list=refined_shopping_list,
    )

    return final_recipe, warnings
