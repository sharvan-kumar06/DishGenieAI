import re
from typing import List, Set

# Common culinary aliases and synonyms mapping
# Maps variant terms / botanic names / regional names to canonical ingredient keys
INGREDIENT_SYNONYMS = {
    # Fungi / Mushrooms
    "agaricus_bisporus": "mushroom",
    "agaricus bisporus": "mushroom",
    "agaricus_blazei_murill": "mushroom",
    "agaricus blazei murill": "mushroom",
    "agrocybe_aegerita": "mushroom",
    "agrocybe aegerita": "mushroom",
    "button mushroom": "mushroom",
    "mushrooms": "mushroom",
    # Capsicum / Peppers
    "bell_pepper": "capsicum",
    "bell pepper": "capsicum",
    "sweet pepper": "capsicum",
    "green bell pepper": "capsicum",
    "red bell pepper": "capsicum",
    "yellow bell pepper": "capsicum",
    "shimla mirch": "capsicum",
    # Chillies
    "green_chilli": "green chilli",
    "green chili": "green chilli",
    "green chillies": "green chilli",
    "green chilies": "green chilli",
    "red_chilli": "red chilli",
    "red chili": "red chilli",
    "red chillies": "red chilli",
    "dry red chillies": "red chilli",
    # Eggplant / Brinjal
    "eggplant": "brinjal",
    "aubergine": "brinjal",
    "baingan": "brinjal",
    # Peas
    "green_peas": "peas",
    "green peas": "peas",
    "green pea": "peas",
    "matar": "peas",
    # Gourd
    "bitter_gourd": "karela",
    "bitter gourd": "karela",
    "pavakkai": "karela",
    "bottle_gourd": "bottle gourd",
    "bottle gourd": "bottle gourd",
    "lauki": "bottle gourd",
    "ridge_gourd": "ridge gourd",
    "ridge gourd": "ridge gourd",
    "turai": "ridge gourd",
    # Okra
    "ladyfinger": "okra",
    "lady finger": "okra",
    "ladies finger": "okra",
    "bhindi": "okra",
    # Aromatics & Herbs
    "coriander": "coriander",
    "coriander leaves": "coriander",
    "cilantro": "coriander",
    "dhania": "coriander",
    "dhania leaves": "coriander",
    "coriander seeds": "coriander seeds",
    "cumin": "cumin",
    "cumin seeds": "cumin",
    "jeera": "cumin",
    "fenugreek": "methi",
    "fenugreek leaves": "methi",
    "curry leaf": "curry leaves",
    "garlic cloves": "garlic",
    "cloves garlic": "garlic",
    "ginger": "ginger",
    "adrak": "ginger",
    # Brassicas
    "cauliflower": "cauliflower",
    "gobi": "cauliflower",
    "cabbage": "cabbage",
    "patta gobi": "cabbage",
    # Root veggies
    "potato": "potato",
    "potatoes": "potato",
    "aloo": "potato",
    "batata": "potato",
    "sweet potato": "sweet potato",
    "shakarkandi": "sweet potato",
    "carrot": "carrot",
    "carrots": "carrot",
    "gajar": "carrot",
    "onion": "onion",
    "onions": "onion",
    "pyaz": "onion",
    "shallot": "shallot",
    "shallots": "shallot",
    "tomato": "tomato",
    "tomatoes": "tomato",
    "tamatar": "tomato",
    "spinach": "spinach",
    "palak": "spinach",
}

# Non-vegetarian detection keywords
NON_VEG_KEYWORDS = [
    "chicken", "egg", "eggs", "fish", "mutton", "prawn", "prawns", "shrimp",
    "shrimps", "meat", "pork", "beef", "crab", "crabs", "lamb", "seafood",
    "bacon", "ham", "sausage", "sausages", "duck", "turkey", "keema", "gosht",
    "rohu", "pomfret", "hilsa", "salmon", "tuna", "anchovy", "anchovies"
]

# Dairy keywords (distinguishing Vegetarian from strict Vegan)
DAIRY_KEYWORDS = [
    "ghee", "milk", "paneer", "butter", "curd", "curds", "yogurt", "yoghurt",
    "cheese", "cream", "khoya", "mawa", "malai", "whey", "honey", "buttermilk",
    "chhena", "condensed milk"
]


def clean_text(text: str) -> str:
    """Removes BOM, special symbols, and extra whitespace."""
    if not text:
        return ""
    text = text.replace("\ufeff", " ")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_token(token: str) -> str:
    """
    Normalizes a single ingredient token into lowercase singular form,
    resolving known culinary synonyms.
    """
    t = clean_text(token).lower()
    t = t.replace("_", " ").replace("-", " ")
    # Remove parentheses notes: e.g. "coriander (dhania) leaves" -> "coriander leaves"
    t = re.sub(r"\(.*?\)", "", t)
    # Remove measurements or qualifiers if present
    t = re.sub(r"\b(chopped|sliced|diced|grated|crushed|minced|fresh|dry|dried|powder|ground|seeds?|leaves?|paste|refined|sunflower|extra virgin|olive|mustard)\b", "", t)
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()

    # Simple singularization
    if t.endswith("ies") and len(t) > 4:
        t = t[:-3] + "y"
    elif t.endswith("es") and len(t) > 3 and not t.endswith(("bes", "ses", "res")):
        t = t[:-2]
    elif t.endswith("s") and len(t) > 2 and not t.endswith(("ss", "us", "is")):
        t = t[:-1]

    # Map to canonical synonym if available
    return INGREDIENT_SYNONYMS.get(t, t)


def extract_ingredient_tokens(cleaned_ingredients_str: str) -> List[str]:
    """
    Takes comma-separated ingredient text and extracts unique, normalized
    search tokens. Preserves meaningful culinary terms.
    """
    if not cleaned_ingredients_str:
        return []

    tokens: Set[str] = set()
    # Split by comma
    parts = cleaned_ingredients_str.split(",")
    for part in parts:
        raw_part = clean_text(part).lower()
        if not raw_part:
            continue

        # 1. Full normalized phrase (e.g. "green chilli", "red chilli powder")
        norm = normalize_token(raw_part)
        if norm and len(norm) > 1:
            tokens.add(norm)

        # 2. Check for synonym key matches inside the raw part
        for key, canonical in INGREDIENT_SYNONYMS.items():
            if re.search(rf"\b{re.escape(key)}\b", raw_part):
                tokens.add(canonical)

        # 3. Individual meaningful words
        words = re.findall(r"\b[a-zA-Z]{3,}\b", raw_part)
        for w in words:
            w_norm = normalize_token(w)
            # Skip generic stop-words
            if w_norm not in {"oil", "salt", "water", "sugar", "taste", "cup", "teaspoon", "tablespoon", "piece", "gram", "pinch"}:
                if len(w_norm) > 2:
                    tokens.add(w_norm)

    return sorted(list(tokens))


def normalize_input_ingredient(ingredient: str) -> str:
    """
    Normalizes an ingredient input string (from CNN or user manual input)
    into a standardized token for database matching.
    """
    cleaned = clean_text(ingredient).lower()
    cleaned = cleaned.replace("_", " ").replace("-", " ")
    # Direct synonym lookup
    if cleaned in INGREDIENT_SYNONYMS:
        return INGREDIENT_SYNONYMS[cleaned]
    return normalize_token(cleaned)


def classify_recipe_diet(cleaned_ingredients: str, title: str) -> str:
    """
    Classifies a recipe as Vegan, Vegetarian, or Non-Vegetarian
    based on ingredients and recipe title.
    """
    search_text = (clean_text(cleaned_ingredients) + " " + clean_text(title)).lower()

    # 1. Check for non-vegetarian keywords
    for kw in NON_VEG_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", search_text):
            return "Non-Vegetarian"

    # 2. Check for dairy / honey
    for kw in DAIRY_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", search_text):
            return "Vegetarian"

    # 3. Completely plant-based
    return "Vegan"


def normalize_cuisine(cuisine_raw: str) -> str:
    """
    Normalizes raw cuisine text from dataset to a primary category.
    Examples:
      'North Indian Recipes' -> 'Indian'
      'Italian Recipes' -> 'Italian'
      'Continental' -> 'Continental'
    """
    c = clean_text(cuisine_raw).strip()
    if not c:
        return "Indian"

    c_lower = c.lower()

    if "italian" in c_lower:
        return "Italian"
    if "chinese" in c_lower:
        return "Chinese"
    if "mexican" in c_lower:
        return "Mexican"
    if "american" in c_lower:
        return "American"
    if "continental" in c_lower:
        return "Continental"
    if "thai" in c_lower:
        return "Thai"
    if "mediterranean" in c_lower:
        return "Mediterranean"
    if any(k in c_lower for k in [
        "indian", "punjabi", "south indian", "north indian", "bengali",
        "kerala", "tamil nadu", "andhra", "karnataka", "maharashtrian",
        "gujarati", "rajasthani", "goan", "kashmiri", "chettinad",
        "hyderabadi", "awadhi", "mughlai", "oriya", "bihari", "sindhi",
        "assamese", "udupi", "konkan", "parsi"
    ]):
        return "Indian"

    return c
