"""
Robust Recipe Parser and Serialization Service for DishGenieAI.
Handles:
1. JSON extraction with bounded repair for common LLM syntax issues.
2. Section-based fallback parser for legacy or narrative text outputs.
3. Grounded database candidate fallback with authentic source data.
4. Comprehensive recipe quality validation & ingredient-instruction reconciliation.
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from app.schemas.recipe import Recipe, Substitution
from app.services.recipe_validator import (
    clean_instruction_step,
    strip_markdown_formatting,
    validate_and_refine_recipe,
)

logger = logging.getLogger(__name__)


def repair_json_string(json_str: str) -> str:
    """
    Performs deterministic, bounded repair of common LLM JSON syntax issues:
    - Removes trailing commas before } or ]
    - Replaces smart quotes
    - Balances unclosed brackets/braces if truncated
    """
    s = json_str.strip()

    # Normalize smart quotes to standard double quotes
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")

    # Remove trailing commas before closing braces/brackets
    s = re.sub(r",\s*([\]}])", r"\1", s)

    # Balance unclosed brackets if truncated
    open_curly = s.count("{") - s.count("}")
    open_square = s.count("[") - s.count("]")

    if open_square > 0:
        s += "]" * open_square
    if open_curly > 0:
        s += "}" * open_curly

    return s


def parse_json_recipe(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Attempts to extract and parse a JSON recipe object from model text.
    Handles raw JSON, fenced code blocks, and embedded JSON objects.
    """
    if not raw_text or not raw_text.strip():
        return None

    text = raw_text.strip()

    # 1. Check for fenced code block: ```json ... ``` or ``` ... ```
    match = re.search(r"```(?:json)?\s*(\{[\s\S]*?\})\s*```", text, re.IGNORECASE)
    if match:
        candidate_json = match.group(1).strip()
    else:
        # 2. Check for outer curly braces
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            candidate_json = text[start : end + 1].strip()
        else:
            return None

    # Attempt direct parse
    try:
        return json.loads(candidate_json)
    except json.JSONDecodeError:
        pass

    # Attempt repaired parse
    try:
        repaired = repair_json_string(candidate_json)
        return json.loads(repaired)
    except Exception as e:
        logger.debug(f"[RecipeParser] JSON repair failed: {e}")
        return None


def sanitize_text_field(text: Any, field_name: str = "") -> str:
    """
    Sanitizes title and description fields by stripping:
    - stray JSON key fragments (e.g. '{"name":', 'name":', '":')
    - leading and trailing colons, commas, escaped quotes, or bracket/brace wrappers
    - outer matching quotes
    """
    if not text:
        return ""
    s = str(text).strip()
    if not s:
        return ""

    # Check if s itself is a full JSON object string e.g. '{"name": "Spiced Beetroot Juice"}'
    if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
        try:
            parsed = json.loads(s)
            if isinstance(parsed, dict):
                if field_name and field_name in parsed and parsed[field_name]:
                    s = str(parsed[field_name]).strip()
                elif "name" in parsed and parsed["name"]:
                    s = str(parsed["name"]).strip()
                elif "title" in parsed and parsed["title"]:
                    s = str(parsed["title"]).strip()
                elif "description" in parsed and parsed["description"]:
                    s = str(parsed["description"]).strip()
                elif len(parsed) == 1:
                    s = str(list(parsed.values())[0]).strip()
            elif isinstance(parsed, list) and len(parsed) == 1:
                s = str(parsed[0]).strip()
        except Exception:
            pass

    # Strip JSON key wrappers like {"name": or "name": or name": or { "description":
    s = re.sub(
        r'^\s*\{?\s*"?(?:name|title|description|recipe_name|summary|about)?"?\s*:\s*',
        "",
        s,
        flags=re.IGNORECASE,
    )

    # Strip leading stray colons, brackets, braces, quotes, backslashes, whitespace
    s = re.sub(r'^(?:[:\s,"\'\\\{\}\[\]]+)', "", s)

    # Strip trailing closing braces, brackets, quotes, commas, colons
    s = re.sub(r'(?:[,\s:;"\'\\\{\}\[\]]+)$', "", s)

    # Normalize escaped quotes \" or \'
    s = s.replace('\\"', '"').replace("\\'", "'")

    # If wrapped in matching quotes, unwrap
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()

    # Re-check for any stray leading colon or quote after unwrapping
    s = re.sub(r'^[:\s,"\'\\\{\}\[\]]+', "", s).strip()
    s = re.sub(r'[:\s,"\'\\\{\}\[\]]+$', "", s).strip()

    return strip_markdown_formatting(s)


def clean_ingredient_entry(entry: str) -> str:
    """
    Cleans an individual ingredient string, removing stray JSON syntax,
    escaped quotes, or outer brackets/braces.
    """
    s = str(entry).strip()
    # Strip leading/trailing JSON bracket/brace fragments
    s = re.sub(r'^\s*\[\s*', '', s)
    s = re.sub(r'\s*\]\s*$', '', s)
    # Strip JSON key wrappers like "ingredient": or {"name":
    s = re.sub(r'^\s*\{?\s*"?(?:ingredient|name|item)?"?\s*:\s*', '', s, flags=re.IGNORECASE)
    # Strip leading/trailing punctuation and quotes
    s = re.sub(r'^(?:[:\s,"\'\\\{\}\[\]]+)', '', s)
    s = re.sub(r'(?:[,\s"\'\\\{\}\[\]]+)$', '', s)
    s = s.replace('\\"', '"').replace("\\'", "'")
    if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
        s = s[1:-1].strip()
    return strip_markdown_formatting(s).strip()


def parse_and_flatten_ingredients(raw_ingredients: Any) -> List[str]:
    """
    Extracts and flattens ingredient entries.
    If an ingredient entry or raw_ingredients starts with a raw JSON array string
    (e.g., '["Item 1", "Item 2"]'), automatically parses it and flattens it into
    individual clean ingredient strings.
    """
    if not raw_ingredients:
        return []

    # If raw_ingredients is a single string
    if isinstance(raw_ingredients, str):
        s = raw_ingredients.strip()
        if s.startswith("[") and "]" in s:
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    raw_ingredients = parsed
                else:
                    raw_ingredients = [s]
            except Exception:
                try:
                    repaired = repair_json_string(s)
                    parsed = json.loads(repaired)
                    if isinstance(parsed, list):
                        raw_ingredients = parsed
                    else:
                        raw_ingredients = [s]
                except Exception:
                    items = re.findall(r'"([^"\n]+)"|\'([^\'\n]+)\'', s)
                    extracted = [g[0] or g[1] for g in items if (g[0] or g[1])]
                    if extracted:
                        raw_ingredients = extracted
                    else:
                        raw_ingredients = s.split("\n")
        else:
            raw_ingredients = s.split("\n")

    flattened: List[str] = []

    def process_item(item: Any):
        if not item:
            return
        if isinstance(item, list):
            for sub in item:
                process_item(sub)
            return
        if isinstance(item, dict):
            amt = item.get("amount") or item.get("quantity") or ""
            ing = item.get("ingredient") or item.get("name") or item.get("item") or ""
            combined = f"{amt} {ing}".strip() if amt else str(ing).strip()
            if not combined and item:
                combined = str(list(item.values())[0]).strip()
            if combined:
                cleaned = clean_ingredient_entry(combined)
                if cleaned and len(cleaned) > 1 and not cleaned.lower().startswith(("ingredient", "instruction")):
                    flattened.append(cleaned)
            return

        item_str = str(item).strip()
        if not item_str:
            return

        # Check if the string itself starts with a raw JSON array: e.g. '["Item 1", "Item 2"]'
        if item_str.startswith("[") and "]" in item_str:
            parsed = None
            try:
                parsed = json.loads(item_str)
            except Exception:
                try:
                    repaired = repair_json_string(item_str)
                    parsed = json.loads(repaired)
                except Exception:
                    items = re.findall(r'"([^"\n]+)"|\'([^\'\n]+)\'', item_str)
                    extracted = [g[0] or g[1] for g in items if (g[0] or g[1])]
                    if extracted:
                        parsed = extracted
            if isinstance(parsed, list):
                for sub in parsed:
                    process_item(sub)
                return

        # Check if item_str is a single JSON object string e.g. '{"ingredient": "1 tsp cumin"}'
        if item_str.startswith("{") and "}" in item_str:
            try:
                parsed = json.loads(item_str)
                if isinstance(parsed, dict):
                    process_item(parsed)
                    return
            except Exception:
                pass

        cleaned = clean_ingredient_entry(item_str)
        if cleaned and len(cleaned) > 1 and not cleaned.lower().startswith(("ingredient", "instruction")):
            flattened.append(cleaned)

    if isinstance(raw_ingredients, (list, tuple)):
        for elem in raw_ingredients:
            process_item(elem)

    return flattened


def parse_section_based_text(text: str) -> Dict[str, Any]:
    """
    Fallback section parser for plain text or markdown-headed model outputs.
    Recognizes:
      - NAME / TITLE
      - DESCRIPTION
      - INGREDIENTS
      - INSTRUCTIONS
      - SUBSTITUTIONS
      - SHOPPING LIST
    """
    patterns = {
        "name": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:RECIPE\s+NAME|NAME|TITLE)(?:\*{0,2}):?\s*(.*?)(?=(?:#{1,4}\s*)?(?:\*{0,2})(?:DESCRIPTION|INGREDIENTS|INSTRUCTIONS|SUBSTITUTIONS|SHOPPING|$))",
        "description": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:DESCRIPTION|ABOUT|SUMMARY)(?:\*{0,2}):?\s*(.*?)(?=(?:#{1,4}\s*)?(?:\*{0,2})(?:INGREDIENTS|INSTRUCTIONS|SUBSTITUTIONS|SHOPPING|$))",
        "ingredients": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:INGREDIENTS|INGREDIENT\s+LIST)(?:\*{0,2}):?\s*(.*?)(?=(?:#{1,4}\s*)?(?:\*{0,2})(?:INSTRUCTIONS|DIRECTIONS|STEPS|METHOD|SUBSTITUTIONS|SHOPPING|$))",
        "instructions": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:INSTRUCTIONS|DIRECTIONS|STEPS|METHOD|PREPARATION)(?:\*{0,2}):?\s*(.*?)(?=(?:#{1,4}\s*)?(?:\*{0,2})(?:SUBSTITUTIONS|SUBSTITUTES|SHOPPING\s+LIST|SHOPPING|$))",
        "substitutions": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:SUBSTITUTIONS|SUBSTITUTES)(?:\*{0,2}):?\s*(.*?)(?=(?:#{1,4}\s*)?(?:\*{0,2})(?:SHOPPING\s+LIST|SHOPPING|$))",
        "shopping_list": r"(?:#{1,4}\s*)?(?:\*{0,2})(?:SHOPPING\s+LIST|SHOPPING)(?:\*{0,2}):?\s*(.*?)(?=$)",
    }

    extracted: Dict[str, Any] = {}
    for key, pat in patterns.items():
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            extracted[key] = m.group(1).strip()

    # Process Name
    name = sanitize_text_field(extracted.get("name", ""), field_name="name")
    if not name:
        for line in text.split("\n"):
            line = strip_markdown_formatting(line)
            if line and len(line) < 70 and not any(kw in line.lower() for kw in ["ingredient", "instruction", "step", "diet", "here is"]):
                cleaned_line = re.sub(r"^(?:RECIPE(?:\s+NAME)?:\s*)", "", line, flags=re.IGNORECASE).strip()
                name = sanitize_text_field(cleaned_line, field_name="name")
                if name:
                    break

    # Process Description
    description = sanitize_text_field(extracted.get("description", ""), field_name="description")

    # Process Ingredients
    ings_raw = extracted.get("ingredients", "")
    ingredients = parse_and_flatten_ingredients(ings_raw)

    # Process Instructions
    insts_raw = extracted.get("instructions", "")
    instructions: List[str] = []
    if insts_raw:
        for line in insts_raw.split("\n"):
            step = clean_instruction_step(line)
            if step:
                instructions.append(step)

    # Process Substitutions
    subs_raw = extracted.get("substitutions", "")
    substitutions: List[Dict[str, str]] = []
    if subs_raw:
        for line in subs_raw.split("\n"):
            line = strip_markdown_formatting(line)
            if ":" in line:
                p1, p2 = line.split(":", 1)
                substitutions.append({"ingredient": sanitize_text_field(p1), "replacement": sanitize_text_field(p2)})
            elif "->" in line:
                p1, p2 = line.split("->", 1)
                substitutions.append({"ingredient": sanitize_text_field(p1), "replacement": sanitize_text_field(p2)})

    # Process Shopping List
    shop_raw = extracted.get("shopping_list", "")
    shopping_list = parse_and_flatten_ingredients(shop_raw)

    return {
        "name": name,
        "description": description,
        "ingredients": ingredients,
        "instructions": instructions,
        "substitutions": substitutions,
        "shopping_list": shopping_list,
    }


def create_recipe_from_database_candidate(
    candidate: Dict[str, Any],
    confirmed_ingredients: Optional[List[str]] = None,
    diet: str = "Vegetarian",
    cuisine: Optional[str] = None,
) -> Recipe:
    """
    Requirement 8: Build authentic database fallback recipe.
    Uses REAL instructions (TranslatedInstructions) and REAL ingredients (TranslatedIngredients).
    Does NOT invent fake instructions. Applies full validation and reconciliation.
    """
    name = sanitize_text_field(candidate.get("name", "Regional Specialty"), field_name="name")

    # Extract real ingredients from database record
    raw_ings = candidate.get("ingredients_raw", "")
    ingredients: List[str] = parse_and_flatten_ingredients(raw_ings.split(",") if raw_ings else [])
    if not ingredients and confirmed_ingredients:
        ingredients = [c.replace("_", " ").title() for c in confirmed_ingredients]

    # Extract real instructions from database record
    raw_insts = candidate.get("instructions", "")
    instructions: List[str] = []
    if raw_insts:
        # Split by newlines or full stops
        lines = raw_insts.split("\n") if "\n" in raw_insts else raw_insts.split(". ")
        for line in lines:
            step = clean_instruction_step(line)
            if step:
                instructions.append(step)

    cand_cuisine = candidate.get("cuisine", cuisine or "Indian")
    description = f"Authentic {cand_cuisine} specialty grounded in traditional preparation methods."

    raw_recipe = Recipe(
        name=name,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        substitutions=[],
        shopping_list=[],
    )

    # Run full quality pass & reconciliation
    validated_recipe, _ = validate_and_refine_recipe(
        raw_recipe,
        confirmed_ingredients=confirmed_ingredients,
        diet=diet,
        cuisine=cand_cuisine,
    )
    return validated_recipe


def parse_recipe_text(
    raw_text: str,
    fallback_ingredients: Optional[List[str]] = None,
    cuisine: Optional[str] = None,
    diet: Optional[str] = None,
    additional_ingredients: Optional[str] = None,
    candidate_recipe: Optional[Dict[str, Any]] = None,
) -> Optional[Recipe]:
    """
    Master parsing and reconciliation entry point.
    1. Attempts JSON extraction and parsing.
    2. Falls back to section-based extraction if JSON is unavailable.
    3. Falls back to authentic database candidate if text output fails.
    4. Validates and refines instructions, ingredients, substitutions, and shopping list.
    """
    user_diet = diet or "Vegetarian"

    # If raw_text is empty, use authentic database candidate fallback
    if not raw_text or not raw_text.strip():
        if candidate_recipe:
            return create_recipe_from_database_candidate(
                candidate_recipe,
                confirmed_ingredients=fallback_ingredients,
                diet=user_diet,
                cuisine=cuisine,
            )
        return None

    # Step 1: Try JSON Parsing
    json_data = parse_json_recipe(raw_text)

    # Step 2: Try Section-based Parsing if JSON is not available
    if not json_data:
        json_data = parse_section_based_text(raw_text)

    # Extract fields with thorough JSON sanitization
    name = sanitize_text_field(json_data.get("name") or "", field_name="name")
    description = sanitize_text_field(json_data.get("description") or "", field_name="description")
    ingredients_raw = json_data.get("ingredients") or []
    instructions_raw = json_data.get("instructions") or []
    subs_raw = json_data.get("substitutions") or []
    shop_raw = json_data.get("shopping_list") or []

    # Format substitutions list
    substitutions: List[Substitution] = []
    if isinstance(subs_raw, str):
        s_subs = subs_raw.strip()
        if s_subs.startswith("[") and "]" in s_subs:
            try:
                parsed_subs = json.loads(s_subs)
                if isinstance(parsed_subs, list):
                    subs_raw = parsed_subs
            except Exception:
                pass
    if isinstance(subs_raw, list):
        for s in subs_raw:
            if isinstance(s, dict) and s.get("ingredient") and s.get("replacement"):
                substitutions.append(Substitution(
                    ingredient=sanitize_text_field(str(s["ingredient"])),
                    replacement=sanitize_text_field(str(s["replacement"])),
                ))
            elif isinstance(s, str) and ":" in s:
                p1, p2 = s.split(":", 1)
                substitutions.append(Substitution(
                    ingredient=sanitize_text_field(p1),
                    replacement=sanitize_text_field(p2),
                ))
            elif isinstance(s, str) and "->" in s:
                p1, p2 = s.split("->", 1)
                substitutions.append(Substitution(
                    ingredient=sanitize_text_field(p1),
                    replacement=sanitize_text_field(p2),
                ))

    # Format ingredients list - auto-flatten raw JSON arrays and entries
    ingredients = parse_and_flatten_ingredients(ingredients_raw)
    if not ingredients and candidate_recipe and candidate_recipe.get("ingredients_raw"):
        ingredients = parse_and_flatten_ingredients(candidate_recipe["ingredients_raw"].split(","))
    elif not ingredients and fallback_ingredients:
        ingredients = [c.replace("_", " ").title() for c in fallback_ingredients]

    # Format instructions list - flatten nested array strings if present
    instructions: List[str] = []
    if isinstance(instructions_raw, str):
        s_inst = instructions_raw.strip()
        if s_inst.startswith("[") and "]" in s_inst:
            try:
                parsed_inst = json.loads(s_inst)
                if isinstance(parsed_inst, list):
                    instructions_raw = parsed_inst
            except Exception:
                try:
                    repaired = repair_json_string(s_inst)
                    parsed_inst = json.loads(repaired)
                    if isinstance(parsed_inst, list):
                        instructions_raw = parsed_inst
                except Exception:
                    pass
        if isinstance(instructions_raw, str):
            instructions_raw = instructions_raw.split("\n")

    for step in instructions_raw:
        step_str = str(step).strip()
        if step_str.startswith("[") and "]" in step_str:
            try:
                sub_steps = json.loads(step_str)
                if isinstance(sub_steps, list):
                    for ss in sub_steps:
                        cleaned = clean_instruction_step(str(ss))
                        if cleaned:
                            instructions.append(cleaned)
                    continue
            except Exception:
                pass
        cleaned = clean_instruction_step(step_str)
        if cleaned:
            instructions.append(cleaned)

    # Format shopping list - auto-flatten array strings
    shopping_items = parse_and_flatten_ingredients(shop_raw)

    # If parsing produced no valid instructions or ingredients, fall back to candidate
    if (not instructions or not ingredients) and candidate_recipe:
        logger.warning("[RecipeParser] Parsed output incomplete, falling back to database candidate recipe.")
        return create_recipe_from_database_candidate(
            candidate_recipe,
            confirmed_ingredients=fallback_ingredients,
            diet=user_diet,
            cuisine=cuisine,
        )

    # Fallback name and description if missing
    if not name:
        name = sanitize_text_field(candidate_recipe.get("name") if candidate_recipe else "Chef's Pantry Special", field_name="name")
    if not description:
        description = f"A flavorful {cuisine or 'gourmet'} dish thoughtfully balanced for a {user_diet.lower()} diet."

    # Initial Recipe object
    recipe_candidate = Recipe(
        name=name,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        substitutions=substitutions,
        shopping_list=shopping_items,
    )

    # Step 3: Run comprehensive validation and reconciliation pass
    final_recipe, warnings = validate_and_refine_recipe(
        recipe_candidate,
        confirmed_ingredients=fallback_ingredients,
        diet=user_diet,
        cuisine=cuisine,
    )

    if warnings:
        logger.info(f"[RecipeParser] Validation pass generated {len(warnings)} quality adjustments: {warnings[:3]}")

    return final_recipe
