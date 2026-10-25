from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class RecipePreferences(BaseModel):
    diet: str = Field("Vegetarian", description="Dietary preference, e.g. Vegetarian, Vegan")
    cuisine: str = Field("Indian", description="Cuisine style, e.g. Indian, Italian")
    cookingTime: int = Field(30, description="Target cooking time in minutes")
    difficulty: str = Field("Easy", description="Recipe difficulty, e.g. Easy, Medium, Hard")
    servings: int = Field(2, description="Target number of servings")
    additionalIngredients: Optional[str] = Field("", description="Optional user-provided additional ingredients")


class InventoryItem(BaseModel):
    ingredient: str = Field(..., description="Ingredient name")
    count: int = Field(1, ge=1, description="Quantity/count of items detected")
    min_expiry_days: Optional[int] = Field(None, description="Estimated days until expiration")
    status: Optional[str] = Field("Fresh", description="Freshness status: Fresh, Medium, or Use First")


class CandidateDishOption(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., description="Candidate recipe dish title")
    description: Optional[str] = Field(None, description="Overview or preview of the candidate dish")
    cuisine: Optional[str] = Field("Indian", description="Cuisine category")
    cooking_time: Optional[int] = Field(30, description="Estimated cooking time in minutes")
    diet: Optional[str] = Field("Vegetarian", description="Dietary classification")
    image_url: Optional[str] = Field(None, description="Optional representative photo URL")
    matched_ingredients: List[str] = Field(default_factory=list, description="Pantry ingredients matched in this dish")


class CandidateOptionsResponse(BaseModel):
    success: bool = Field(True, description="Whether candidate retrieval succeeded")
    options: List[CandidateDishOption] = Field(default_factory=list, description="Top matching dish style options")


class RecipeRequest(BaseModel):
    ingredients: List[str] = Field(..., description="List of confirmed detected ingredients")
    inventory: Optional[List[InventoryItem]] = Field(default_factory=list, description="Structured produce inventory")
    preferences: RecipePreferences = Field(default_factory=RecipePreferences)
    selected_dish: Optional[str] = Field(None, description="Optional chosen dish title from candidate options")

    @field_validator("ingredients")
    @classmethod
    def validate_ingredients(cls, v: List[str]) -> List[str]:
        cleaned = [item.strip() for item in v if item and item.strip()]
        if not cleaned:
            raise ValueError("Ingredients list must contain at least one valid item.")
        return cleaned


class Substitution(BaseModel):
    ingredient: str = Field(..., description="Original ingredient")
    replacement: str = Field(..., description="Suggested replacement or substitute")


class Recipe(BaseModel):
    name: str = Field(..., description="Recipe title")
    description: str = Field(..., description="Brief overview of the dish")
    ingredients: List[str] = Field(..., description="Itemized ingredients needed")
    instructions: List[str] = Field(..., description="Step-by-step cooking instructions")
    substitutions: List[Substitution] = Field(default_factory=list, description="Ingredient substitution options")
    shopping_list: List[str] = Field(default_factory=list, description="Items needed from the market")


class RecipeResponse(BaseModel):
    success: bool = Field(True, description="Whether generation succeeded")
    recipe: Optional[Recipe] = Field(None, description="Structured parsed recipe")
    raw_text: Optional[str] = Field(None, description="Raw model generated text if structured parsing is not possible")
