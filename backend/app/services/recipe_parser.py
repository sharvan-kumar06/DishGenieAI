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
    name = extracted.get("name", "")
    if not name:
        for line in text.split("\n"):
            line = strip_markdown_formatting(line)
            if line and len(line) < 70 and not any(kw in line.lower() for kw in ["ingredient", "instruction", "step", "diet", "here is"]):
                name = re.sub(r"^(?:RECIPE(?:\s+NAME)?:\s*)", "", line, flags=re.IGNORECASE).strip()
                break

    # Process Ingredients
    ings_raw = extracted.get("ingredients", "")
    ingredients: List[str] = []
    if ings_raw:
        for line in ings_raw.split("\n"):
            cleaned = strip_markdown_formatting(line)
            if cleaned and len(cleaned) > 1 and not cleaned.lower().startswith(("ingredient", "instruction")):
                ingredients.append(cleaned)

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
                substitutions.append({"ingredient": p1.strip(), "replacement": p2.strip()})
            elif "->" in line:
                p1, p2 = line.split("->", 1)
                substitutions.append({"ingredient": p1.strip(), "replacement": p2.strip()})

    # Process Shopping List
    shop_raw = extracted.get("shopping_list", "")
    shopping_list: List[str] = []
    if shop_raw:
        for line in shop_raw.split("\n"):
            cleaned = strip_markdown_formatting(line)
            if cleaned and len(cleaned) > 1:
                shopping_list.append(cleaned)

    return {
        "name": name,
        "description": extracted.get("description", ""),
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
    name = strip_markdown_formatting(candidate.get("name", "Regional Specialty"))

    # Extract real ingredients from database record
    raw_ings = candidate.get("ingredients_raw", "")
    ingredients: List[str] = []
    if raw_ings:
        for item in raw_ings.split(","):
            cleaned = strip_markdown_formatting(item)
            if cleaned:
                ingredients.append(cleaned)
    elif confirmed_ingredients:
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

    # Extract fields
    name = str(json_data.get("name") or "").strip()
    description = str(json_data.get("description") or "").strip()
    ingredients_raw = json_data.get("ingredients") or []
    instructions_raw = json_data.get("instructions") or []
    subs_raw = json_data.get("substitutions") or []
    shop_raw = json_data.get("shopping_list") or []

    # Format substitutions list
    substitutions: List[Substitution] = []
    if isinstance(subs_raw, list):
        for s in subs_raw:
            if isinstance(s, dict) and s.get("ingredient") and s.get("replacement"):
                substitutions.append(Substitution(
                    ingredient=strip_markdown_formatting(str(s["ingredient"])),
                    replacement=strip_markdown_formatting(str(s["replacement"])),
                ))
            elif isinstance(s, str) and ":" in s:
                p1, p2 = s.split(":", 1)
                substitutions.append(Substitution(
                    ingredient=strip_markdown_formatting(p1),
                    replacement=strip_markdown_formatting(p2),
                ))

    # Format ingredients list
    ingredients = [strip_markdown_formatting(str(i)) for i in ingredients_raw if strip_markdown_formatting(str(i))]
    if not ingredients and candidate_recipe and candidate_recipe.get("ingredients_raw"):
        ingredients = [strip_markdown_formatting(i) for i in candidate_recipe["ingredients_raw"].split(",") if strip_markdown_formatting(i)]
    elif not ingredients and fallback_ingredients:
        ingredients = [c.replace("_", " ").title() for c in fallback_ingredients]

    # Format instructions list
    instructions: List[str] = []
    for step in instructions_raw:
        cleaned = clean_instruction_step(str(step))
        if cleaned:
            instructions.append(cleaned)

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
        name = candidate_recipe.get("name") if candidate_recipe else "Chef's Pantry Special"
    if not description:
        description = f"A flavorful {cuisine or 'gourmet'} dish thoughtfully balanced for a {user_diet.lower()} diet."

    # Initial Recipe object
    recipe_candidate = Recipe(
        name=name,
        description=description,
        ingredients=ingredients,
        instructions=instructions,
        substitutions=substitutions,
        shopping_list=[strip_markdown_formatting(str(s)) for s in shop_raw if strip_markdown_formatting(str(s))],
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
