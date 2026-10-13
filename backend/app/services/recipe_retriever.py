import json
import logging
from typing import Any, Dict, List, Optional, Set

from app.schemas.recipe import RecipePreferences
from app.services.ingredient_normalizer import (
    clean_text,
    normalize_input_ingredient,
)
from app.services.recipe_database import RecipeDatabase, get_recipe_database

logger = logging.getLogger(__name__)


class RecipeRetriever:
    """
    Retrieves and ranks candidate recipes from SQLite based on:
      1. Ingredient overlap (primary signal)
      2. Dietary compatibility (strict constraint)
      3. Cuisine preference (ranking booster)
      4. Cooking time constraints (ranking booster / penalty)
    """

    def __init__(self, db: Optional[RecipeDatabase] = None):
        self.db = db or get_recipe_database()

    def retrieve_candidates(
        self,
        ingredients: List[str],
        preferences: Optional[RecipePreferences] = None,
        limit: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Executes candidate retrieval and ranking.
        Returns the top `limit` relevant recipes.
        """
        if not preferences:
            preferences = RecipePreferences()

        # 1. Normalize user ingredients
        user_tokens: Set[str] = set()
        for ing in ingredients:
            norm = normalize_input_ingredient(ing)
            if norm and len(norm) > 1:
                user_tokens.add(norm)

        # Include additional ingredients if specified
        if preferences.additionalIngredients:
            for extra in preferences.additionalIngredients.split(","):
                norm = normalize_input_ingredient(extra)
                if norm and len(norm) > 1:
                    user_tokens.add(norm)

        search_tokens = sorted(list(user_tokens))
        logger.info(f"[RecipeRetriever] Extracted search tokens: {search_tokens}")

        # 2. Build diet filter clause
        diet_filter = preferences.diet.strip().lower()
        diet_clause = ""
        diet_params: List[Any] = []

        if diet_filter == "vegan":
            diet_clause = "AND r.diet = 'Vegan'"
        elif diet_filter == "vegetarian":
            diet_clause = "AND r.diet IN ('Vegetarian', 'Vegan')"
        # "non-vegetarian" or "no preference" imposes no restriction

        candidates: List[Dict[str, Any]] = []

        # 3. Step A: Relational query on recipe_ingredients by tokens
        if search_tokens:
            placeholders = ",".join(["?"] * len(search_tokens))
            query = f"""
                SELECT
                    r.id,
                    r.name,
                    r.ingredients_raw,
                    r.ingredients_cleaned,
                    r.ingredients_tokens,
                    r.instructions,
                    r.cuisine,
                    r.cuisine_category,
                    r.diet,
                    r.cooking_time,
                    r.ingredient_count,
                    r.url,
                    r.image_url,
                    COUNT(DISTINCT ri.token) AS matched_token_count
                FROM recipes r
                JOIN recipe_ingredients ri ON r.id = ri.recipe_id
                WHERE ri.token IN ({placeholders})
                  {diet_clause}
                GROUP BY r.id
                ORDER BY matched_token_count DESC
                LIMIT 80;
            """
            params = search_tokens + diet_params

            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()
                candidates = [dict(row) for row in rows]

        # 4. Step B: Fallback if no token matches (e.g. brand new ingredient or FTS)
        if not candidates and search_tokens:
            fts_query_str = " OR ".join([f'"{tok}"' for tok in search_tokens])
            query_fts = f"""
                SELECT
                    r.*,
                    1 AS matched_token_count
                FROM recipes_fts fts
                JOIN recipes r ON fts.rowid = r.id
                WHERE recipes_fts MATCH ?
                  {diet_clause}
                LIMIT 40;
            """
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(query_fts, [fts_query_str] + diet_params)
                    rows = cursor.fetchall()
                    candidates = [dict(row) for row in rows]
            except Exception as fts_err:
                logger.warning(f"[RecipeRetriever] FTS fallback failed: {fts_err}")

        # 5. Step C: General fallback if still empty (match by cuisine / diet)
        if not candidates:
            query_fallback = f"""
                SELECT
                    r.*,
                    0 AS matched_token_count
                FROM recipes r
                WHERE 1=1
                  {diet_clause}
                ORDER BY r.id ASC
                LIMIT 20;
            """
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query_fallback, diet_params)
                rows = cursor.fetchall()
                candidates = [dict(row) for row in rows]

        # 6. Rank candidate recipes
        scored_candidates = []
        user_cuisine = preferences.cuisine.strip().lower()
        target_time = preferences.cookingTime

        for cand in candidates:
            # Parse tokens in recipe
            try:
                recipe_tokens = set(json.loads(cand.get("ingredients_tokens", "[]")))
            except Exception:
                recipe_tokens = set()

            # Overlap calculation
            overlap = len(recipe_tokens.intersection(set(search_tokens))) if search_tokens else 0
            overlap_score = overlap * 4.0

            # Coverage ratio (what % of user's requested ingredients are used)
            coverage_ratio = (overlap / len(search_tokens)) if search_tokens else 0.0
            coverage_score = coverage_ratio * 3.0

            # Cuisine preference matching
            cuisine_score = 0.0
            cand_cuisine_cat = cand.get("cuisine_category", "").lower()
            cand_cuisine_raw = cand.get("cuisine", "").lower()

            if user_cuisine and user_cuisine != "any cuisine":
                if user_cuisine == cand_cuisine_cat:
                    cuisine_score = 3.0
                elif user_cuisine in cand_cuisine_raw:
                    cuisine_score = 2.0
                else:
                    cuisine_score = -0.5
            else:
                cuisine_score = 1.0

            # Cooking time score
            cand_time = cand.get("cooking_time", 30)
            if cand_time <= target_time:
                time_score = 2.0
            elif cand_time <= target_time + 15:
                time_score = 0.5
            else:
                diff = cand_time - target_time
                time_score = max(-3.0, -0.05 * diff)

            total_score = overlap_score + coverage_score + cuisine_score + time_score

            cand["retrieval_score"] = round(total_score, 2)
            cand["overlap_count"] = overlap
            cand["matched_user_tokens"] = sorted(list(recipe_tokens.intersection(set(search_tokens))))
            scored_candidates.append((total_score, cand))

        # Sort descending by score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)

        ranked_results = [item[1] for item in scored_candidates[:limit]]
        logger.info(
            f"[RecipeRetriever] Retrieved top {len(ranked_results)} recipes for {search_tokens}"
        )
        return ranked_results


# Singleton global instance
_retriever_instance: Optional[RecipeRetriever] = None


def get_recipe_retriever() -> RecipeRetriever:
    """Returns the shared RecipeRetriever instance."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = RecipeRetriever()
    return _retriever_instance
