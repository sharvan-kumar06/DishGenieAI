/**
 * DishGenie Local Storage Service for Recipe History and Favorites.
 * Persists up to 50 recipes in browser localStorage.
 */

export const STORAGE_KEY = 'dishgenie_recipe_history'
export const MAX_HISTORY_LIMIT = 50
export const HISTORY_UPDATE_EVENT = 'dishgenie_history_updated'

/**
 * Dispatches a custom window event so all components/pages update immediately.
 */
function notifyHistoryChange() {
  if (typeof window !== 'undefined') {
    window.dispatchEvent(new CustomEvent(HISTORY_UPDATE_EVENT))
  }
}

/**
 * Safely retrieves all recipe history from localStorage.
 * Handles missing data, invalid JSON, and corrupted structures gracefully.
 *
 * @returns {Array} List of saved recipe records, sorted newest first by createdAt.
 */
export function getRecipeHistory() {
  if (typeof window === 'undefined' || !window.localStorage) {
    return []
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []

    const parsed = JSON.parse(raw)
    if (!Array.isArray(parsed)) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify([]))
      return []
    }

    // Filter valid objects that have an ID and a recipe or name
    const valid = parsed.filter(
      (item) => item && typeof item === 'object' && item.id
    )

    // Sort newest first by createdAt
    return valid.sort((a, b) => {
      const timeA = new Date(a.createdAt || 0).getTime()
      const timeB = new Date(b.createdAt || 0).getTime()
      return timeB - timeA
    })
  } catch (error) {
    console.warn('Error reading dishgenie_recipe_history from localStorage:', error)
    return []
  }
}

/**
 * Saves a newly generated recipe to localStorage.
 * Enforces the 50-recipe maximum limit by removing the oldest record by timestamp.
 *
 * @param {Object} recipeData - Raw backend response ({ recipe, raw_text })
 * @param {Object} preferences - Dietary, cuisine, and cooking preferences
 * @param {Array<string>} confirmedIngredients - Detected and confirmed ingredients
 * @returns {Object} The saved recipe record.
 */
export function saveRecipeToHistory(recipeData, preferences, confirmedIngredients) {
  if (!recipeData) return null

  const history = getRecipeHistory()

  // Generate unique ID and timestamp
  const uniqueId = `recipe_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  const timestamp = new Date().toISOString()

  const recipe = recipeData.recipe || {}
  const raw_text = recipeData.raw_text || null

  const record = {
    id: uniqueId,
    name: recipe.name || 'Custom DishGenie Recipe',
    description: recipe.description || '',
    ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : [],
    instructions: Array.isArray(recipe.instructions) ? recipe.instructions : [],
    substitutions: Array.isArray(recipe.substitutions) ? recipe.substitutions : [],
    shopping_list: Array.isArray(recipe.shopping_list) ? recipe.shopping_list : [],
    raw_text: raw_text,
    confirmedIngredients: Array.isArray(confirmedIngredients) ? confirmedIngredients : [],
    preferences: preferences || {},
    createdAt: timestamp,
    isFavorite: false,
  }

  // Add new recipe to front
  let updated = [record, ...history]

  // If history exceeds 50 recipes, keep the 50 newest by timestamp
  if (updated.length > MAX_HISTORY_LIMIT) {
    // Sort descending by timestamp
    updated.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
    // Keep 50 items (oldest removed automatically)
    updated = updated.slice(0, MAX_HISTORY_LIMIT)
  }

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    notifyHistoryChange()
  } catch (error) {
    // If quota exceeded, try trimming history further (keep 25)
    try {
      const reduced = updated.slice(0, 25)
      localStorage.setItem(STORAGE_KEY, JSON.stringify(reduced))
      notifyHistoryChange()
    } catch (secondError) {
      console.warn('Unable to persist recipe to localStorage (storage unavailable or quota exceeded):', secondError)
    }
  }

  return record
}

/**
 * Retrieves a single saved recipe record by its unique ID.
 *
 * @param {string} id - Recipe ID
 * @returns {Object|null}
 */
export function getRecipeById(id) {
  if (!id) return null
  const history = getRecipeHistory()
  return history.find((item) => item.id === id) || null
}

/**
 * Toggles the favorite status of a recipe.
 *
 * @param {string} id - Recipe ID
 * @returns {boolean} New favorite status
 */
export function toggleFavorite(id) {
  if (!id) return false
  const history = getRecipeHistory()
  let newStatus = false

  const updated = history.map((item) => {
    if (item.id === id) {
      newStatus = !item.isFavorite
      return { ...item, isFavorite: newStatus }
    }
    return item
  })

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    notifyHistoryChange()
  } catch (error) {
    console.error('Failed to update favorite status in localStorage:', error)
  }

  return newStatus
}

/**
 * Returns all recipes marked as favorites.
 *
 * @returns {Array} List of favorite recipes.
 */
export function getFavoriteRecipes() {
  const history = getRecipeHistory()
  return history.filter((item) => item.isFavorite === true)
}

/**
 * Deletes an individual recipe from history by ID.
 *
 * @param {string} id - Recipe ID to delete
 * @returns {boolean} Success status
 */
export function deleteRecipeFromHistory(id) {
  if (!id) return false
  const history = getRecipeHistory()
  const updated = history.filter((item) => item.id !== id)

  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(updated))
    notifyHistoryChange()
    return true
  } catch (error) {
    console.error('Failed to delete recipe from localStorage:', error)
    return false
  }
}

/**
 * Clears all recipe history from localStorage.
 */
export function clearRecipeHistory() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify([]))
    notifyHistoryChange()
  } catch (error) {
    console.error('Failed to clear recipe history:', error)
  }
}
