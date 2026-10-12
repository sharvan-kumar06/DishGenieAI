import { useNavigate } from 'react-router-dom'
import {
  Heart,
  Clock,
  Flame,
  ChefHat,
  Utensils,
  Trash2,
  ArrowRight,
  Calendar,
} from 'lucide-react'
import { INGREDIENT_EMOJIS, formatIngredientName } from '../services/api'

export default function RecipeCard({
  recipe,
  onToggleFavorite,
  onDelete,
  isFavoritePage = false,
}) {
  const navigate = useNavigate()

  if (!recipe) return null

  const {
    id,
    name = 'DishGenie Recipe',
    description = '',
    ingredients = [],
    confirmedIngredients = [],
    preferences = {},
    createdAt,
    isFavorite = false,
  } = recipe

  // Format creation date
  const formattedDate = createdAt
    ? new Date(createdAt).toLocaleDateString(undefined, {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      })
    : 'Recent'

  // Ingredients preview
  const displayIngredients =
    confirmedIngredients.length > 0
      ? confirmedIngredients
      : ingredients.slice(0, 4)

  const handleView = () => {
    navigate('/recipe', {
      state: {
        recipeRecord: recipe,
        fromSaved: true,
      },
    })
  }

  return (
    <div className="bg-white rounded-3xl p-6 border border-stone-200/90 shadow-xl shadow-stone-900/5 hover:border-orange-200 transition-all duration-300 flex flex-col justify-between space-y-5 hover:-translate-y-1">
      {/* Top Header: Date, Badges & Favorite Toggle */}
      <div className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 text-xs text-stone-600 font-medium">
            <Calendar className="w-3.5 h-3.5 text-stone-500" />
            <span>{formattedDate}</span>
          </div>

          {/* Favorite Toggle Button */}
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation()
              onToggleFavorite(id)
            }}
            className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-bold transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 ${
              isFavorite
                ? 'bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100 shadow-2xs'
                : 'bg-stone-100 text-stone-600 hover:text-stone-900 hover:bg-stone-200'
            }`}
            title={isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
            aria-label={isFavorite ? 'Remove from Favorites' : 'Add to Favorites'}
          >
            <Heart
              className={`w-3.5 h-3.5 ${
                isFavorite ? 'fill-rose-500 text-rose-500' : 'text-stone-500'
              }`}
            />
            <span>{isFavorite ? 'Favorited' : 'Favorite'}</span>
          </button>
        </div>

        {/* Recipe Title */}
        <div>
          <h3
            onClick={handleView}
            className="text-lg sm:text-xl font-extrabold text-stone-900 hover:text-orange-600 transition-colors cursor-pointer line-clamp-2 break-words"
          >
            {name}
          </h3>
          {description && (
            <p className="text-xs text-stone-500 mt-1 line-clamp-2 leading-relaxed">
              {description}
            </p>
          )}
        </div>
      </div>

      {/* Middle Section: Metadata Badges & Ingredients Preview */}
      <div className="space-y-3 pt-2 border-t border-stone-100">
        {/* Metadata Tags */}
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] font-semibold text-stone-600">
          {preferences.cuisine && (
            <span className="px-2.5 py-1 rounded-lg bg-orange-50 text-orange-800 border border-orange-200 flex items-center gap-1">
              <Utensils className="w-3 h-3 text-orange-600" />
              <span>{preferences.cuisine}</span>
            </span>
          )}
          {preferences.diet && (
            <span className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1">
              <ChefHat className="w-3 h-3 text-emerald-600" />
              <span>{preferences.diet}</span>
            </span>
          )}
          {preferences.cookingTime && (
            <span className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 flex items-center gap-1">
              <Clock className="w-3 h-3 text-stone-500" />
              <span>{preferences.cookingTime} min</span>
            </span>
          )}
          {preferences.difficulty && (
            <span className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 flex items-center gap-1">
              <Flame className="w-3 h-3 text-stone-500" />
              <span>{preferences.difficulty}</span>
            </span>
          )}
        </div>

        {/* Ingredients Chips */}
        {displayIngredients.length > 0 && (
          <div className="space-y-1">
            <span className="text-[10px] uppercase font-bold text-stone-600 tracking-wider">
              Main Ingredients
            </span>
            <div className="flex flex-wrap gap-1.5 pt-0.5">
              {displayIngredients.slice(0, 5).map((ing, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-lg bg-stone-50 border border-stone-200 text-xs font-semibold text-stone-800"
                >
                  <span className="text-xs">
                    {INGREDIENT_EMOJIS[ing] || '🥗'}
                  </span>
                  <span>{formatIngredientName(ing)}</span>
                </span>
              ))}
              {displayIngredients.length > 5 && (
                <span className="px-1.5 py-0.5 rounded-lg bg-stone-100 text-[10px] font-semibold text-stone-500 self-center">
                  +{displayIngredients.length - 5} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Bottom Actions: View Recipe & Delete / Remove */}
      <div className="pt-3 border-t border-stone-100 flex items-center justify-between gap-2">
        <button
          type="button"
          onClick={handleView}
          className="inline-flex items-center gap-2 px-4 py-2.5 min-h-[40px] rounded-xl text-xs font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-sm transition-all hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
        >
          <span>View Recipe</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>

        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation()
            onDelete(recipe)
          }}
          className="p-2.5 min-w-[40px] min-h-[40px] flex items-center justify-center rounded-xl text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500"
          title={isFavoritePage ? 'Remove from favorites' : 'Delete from history'}
          aria-label={isFavoritePage ? 'Remove from favorites' : 'Delete from history'}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  )
}
