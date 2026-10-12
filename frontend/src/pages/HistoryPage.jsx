import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  History,
  Trash2,
  Sparkles,
  ArrowRight,
  AlertTriangle,
  BookOpen,
} from 'lucide-react'
import RecipeCard from '../components/RecipeCard'
import {
  getRecipeHistory,
  toggleFavorite,
  deleteRecipeFromHistory,
  clearRecipeHistory,
  HISTORY_UPDATE_EVENT,
} from '../services/storage'

export default function HistoryPage() {
  const [recipes, setRecipes] = useState([])
  const [recipeToDelete, setRecipeToDelete] = useState(null)
  const [showClearConfirm, setShowClearConfirm] = useState(false)

  // Load history from localStorage
  const loadHistory = () => {
    setRecipes(getRecipeHistory())
  }

  useEffect(() => {
    loadHistory()

    // Listen for custom history update events and cross-tab storage events
    const handleUpdate = () => loadHistory()
    window.addEventListener(HISTORY_UPDATE_EVENT, handleUpdate)
    window.addEventListener('storage', handleUpdate)

    return () => {
      window.removeEventListener(HISTORY_UPDATE_EVENT, handleUpdate)
      window.removeEventListener('storage', handleUpdate)
    }
  }, [])

  // Favorite toggle handler
  const handleToggleFavorite = (id) => {
    toggleFavorite(id)
    loadHistory()
  }

  // Delete individual recipe
  const handleConfirmDelete = () => {
    if (recipeToDelete) {
      deleteRecipeFromHistory(recipeToDelete.id)
      setRecipeToDelete(null)
      loadHistory()
    }
  }

  // Clear all history
  const handleConfirmClearAll = () => {
    clearRecipeHistory()
    setShowClearConfirm(false)
    loadHistory()
  }

  return (
    <div className="min-h-[85vh] py-10 md:py-16 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-10 animate-in fade-in duration-300">
      
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-stone-200">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-100/80 border border-orange-200 text-orange-800 text-xs font-bold uppercase tracking-wider shadow-2xs">
            <History className="w-3.5 h-3.5 text-orange-600" />
            <span>Recipe Archive</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
            Recipe History
          </h1>
          <p className="text-xs sm:text-sm text-stone-500">
            Browse and manage recipes you have previously generated on DishGenie.
          </p>
        </div>

        {/* Clear History Button (Only shown when recipes exist) */}
        {recipes.length > 0 && (
          <button
            type="button"
            onClick={() => setShowClearConfirm(true)}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs font-bold text-rose-600 bg-rose-50/80 hover:bg-rose-100 border border-rose-200 transition-colors self-start sm:self-auto cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
          >
            <Trash2 className="w-4 h-4" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* Content Area */}
      {recipes.length > 0 ? (
        <div className="space-y-6">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>
              Showing {recipes.length} saved recipe{recipes.length !== 1 ? 's' : ''} (up to 50 kept)
            </span>
          </div>

          {/* Recipe Cards Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recipes.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onToggleFavorite={handleToggleFavorite}
                onDelete={(r) => setRecipeToDelete(r)}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-3xl p-10 sm:p-16 border border-stone-200 shadow-xl shadow-stone-900/5 text-center space-y-6 max-w-lg mx-auto">
          <div className="w-20 h-20 mx-auto rounded-3xl bg-orange-50 border border-orange-200 flex items-center justify-center text-orange-600 shadow-inner">
            <BookOpen className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-stone-900">
              No recipes yet.
            </h2>
            <p className="text-sm text-stone-500 max-w-xs mx-auto leading-relaxed">
              Your generated recipes will appear here.
            </p>
          </div>

          <div className="pt-2">
            <Link
              to="/detect"
              className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/25 transition-all hover:-translate-y-0.5 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Create a Recipe</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Confirmation Modal: Delete Individual Recipe */}
      {recipeToDelete && (
        <div className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full border border-stone-200 shadow-2xl space-y-5">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <Trash2 className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-lg font-extrabold text-stone-900">
                Remove this recipe from your history?
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed">
                "{recipeToDelete.name}" will be removed from your history and favorites.
              </p>
            </div>

            <div className="pt-2 flex flex-col-reverse sm:flex-row items-center justify-end gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setRecipeToDelete(null)}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer text-center"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmDelete}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-sm transition-colors cursor-pointer text-center"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Confirmation Modal: Clear All History */}
      {showClearConfirm && (
        <div className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full border border-stone-200 shadow-2xl space-y-5">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <AlertTriangle className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-lg font-extrabold text-stone-900">
                Clear all recipe history?
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed">
                All saved recipes will be removed from this browser. This cannot be undone.
              </p>
            </div>

            <div className="pt-2 flex flex-col-reverse sm:flex-row items-center justify-end gap-2 sm:gap-3">
              <button
                type="button"
                onClick={() => setShowClearConfirm(false)}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer text-center"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmClearAll}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-sm transition-colors cursor-pointer text-center"
              >
                Clear History
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
