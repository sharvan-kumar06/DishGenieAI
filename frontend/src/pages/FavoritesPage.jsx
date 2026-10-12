import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import {
  Heart,
  Sparkles,
  ArrowRight,
  BookOpen,
} from 'lucide-react'
import RecipeCard from '../components/RecipeCard'
import {
  getFavoriteRecipes,
  toggleFavorite,
  HISTORY_UPDATE_EVENT,
} from '../services/storage'

export default function FavoritesPage() {
  const [favorites, setFavorites] = useState([])
  const [recipeToDelete, setRecipeToDelete] = useState(null)

  // Load favorite recipes from localStorage
  const loadFavorites = () => {
    setFavorites(getFavoriteRecipes())
  }

  useEffect(() => {
    loadFavorites()

    const handleUpdate = () => loadFavorites()
    window.addEventListener(HISTORY_UPDATE_EVENT, handleUpdate)
    window.addEventListener('storage', handleUpdate)

    return () => {
      window.removeEventListener(HISTORY_UPDATE_EVENT, handleUpdate)
      window.removeEventListener('storage', handleUpdate)
    }
  }, [])

  // Favorite toggle (removes immediately from Favorites view)
  const handleToggleFavorite = (id) => {
    toggleFavorite(id)
    loadFavorites()
  }

  // Remove recipe from favorites (keeps in history)
  const handleConfirmRemoveFavorite = () => {
    if (recipeToDelete) {
      toggleFavorite(recipeToDelete.id)
      setRecipeToDelete(null)
      loadFavorites()
    }
  }

  return (
    <div className="min-h-[85vh] py-10 md:py-16 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-10 animate-in fade-in duration-300">
      
      {/* Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-stone-200">
        <div className="space-y-1">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-rose-100/80 border border-rose-200 text-rose-800 text-xs font-bold uppercase tracking-wider shadow-2xs">
            <Heart className="w-3.5 h-3.5 fill-rose-600 text-rose-600" />
            <span>Saved Favorites</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
            Favorite Recipes
          </h1>
          <p className="text-xs sm:text-sm text-stone-500">
            Quickly access dishes you have bookmarked for easy kitchen reference.
          </p>
        </div>

        {favorites.length > 0 && (
          <div className="text-xs font-semibold px-3.5 py-1.5 rounded-full bg-rose-50 text-rose-800 border border-rose-200 self-start sm:self-auto">
            {favorites.length} bookmarked recipe{favorites.length !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Content Area */}
      {favorites.length > 0 ? (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {favorites.map((recipe) => (
              <RecipeCard
                key={recipe.id}
                recipe={recipe}
                onToggleFavorite={handleToggleFavorite}
                onDelete={(r) => setRecipeToDelete(r)}
                isFavoritePage={true}
              />
            ))}
          </div>
        </div>
      ) : (
        /* Empty State */
        <div className="bg-white rounded-3xl p-10 sm:p-16 border border-stone-200 shadow-xl shadow-stone-900/5 text-center space-y-6 max-w-lg mx-auto">
          <div className="w-20 h-20 mx-auto rounded-3xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-500 shadow-inner">
            <Heart className="w-10 h-10" />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-extrabold text-stone-900">
              No favorite recipes yet.
            </h2>
            <p className="text-sm text-stone-500 max-w-xs mx-auto leading-relaxed">
              Favorite recipes you love and find them here later.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              to="/history"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-xs sm:text-sm font-bold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2"
            >
              <BookOpen className="w-4 h-4" />
              <span>View Recipe History</span>
            </Link>

            <Link
              to="/detect"
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-xs sm:text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/25 transition-all hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
            >
              <Sparkles className="w-4 h-4" />
              <span>Generate Recipe</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      )}

      {/* Confirmation Modal: Remove from favorites */}
      {recipeToDelete && (
        <div className="fixed inset-0 z-50 bg-stone-900/50 backdrop-blur-xs flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-md w-full border border-stone-200 shadow-2xl space-y-5">
            <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center text-rose-600">
              <Heart className="w-6 h-6" />
            </div>

            <div className="space-y-1">
              <h3 className="text-lg font-extrabold text-stone-900">
                Remove from Favorites?
              </h3>
              <p className="text-xs text-stone-500 leading-relaxed">
                "{recipeToDelete.name}" will be removed from your favorites list.
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
                onClick={handleConfirmRemoveFavorite}
                className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-rose-600 hover:bg-rose-700 shadow-sm transition-colors cursor-pointer text-center"
              >
                Remove from Favorites
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}
