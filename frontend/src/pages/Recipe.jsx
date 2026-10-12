import { useState, useEffect } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {
  ArrowLeft,
  Sparkles,
  Clock,
  Flame,
  Users,
  ChefHat,
  Utensils,
  CheckSquare,
  Square,
  Printer,
  RotateCcw,
  Copy,
  Check,
  AlertCircle,
  BookOpen,
  ShoppingBag,
  Heart,
} from 'lucide-react'
import { INGREDIENT_EMOJIS, formatIngredientName } from '../services/api'
import {
  getRecipeById,
  toggleFavorite,
  HISTORY_UPDATE_EVENT,
} from '../services/storage'
import Toast from '../components/Toast'

export default function Recipe() {
  const location = useLocation()
  const navigate = useNavigate()

  // Retrieve passed state, with sessionStorage fallback to survive browser refresh
  const [recipePayload, setRecipePayload] = useState(() => {
    // If opened directly from History or Favorites via saved recipeRecord
    if (location.state?.recipeRecord) {
      const rec = location.state.recipeRecord
      const payload = {
        recipeData: {
          recipe: {
            name: rec.name,
            description: rec.description,
            ingredients: rec.ingredients,
            instructions: rec.instructions,
            substitutions: rec.substitutions,
            shopping_list: rec.shopping_list,
          },
          raw_text: rec.raw_text,
        },
        preferences: rec.preferences,
        confirmedIngredients: rec.confirmedIngredients,
        savedId: rec.id,
        isFavorite: rec.isFavorite,
      }
      sessionStorage.setItem('dishgenie_recipe_data', JSON.stringify(payload))
      return payload
    }

    // If navigated from Detect
    if (location.state?.recipeData) {
      const payload = {
        recipeData: location.state.recipeData,
        preferences: location.state.preferences,
        confirmedIngredients: location.state.confirmedIngredients,
        savedId: location.state.savedRecord?.id,
        isFavorite: location.state.savedRecord?.isFavorite || false,
      }
      sessionStorage.setItem('dishgenie_recipe_data', JSON.stringify(payload))
      return payload
    }

    const cached = sessionStorage.getItem('dishgenie_recipe_data')
    if (cached) {
      try {
        return JSON.parse(cached)
      } catch {
        return null
      }
    }
    return null
  })

  // Favorite status state with real-time synchronization
  const [isFavorite, setIsFavorite] = useState(() => {
    if (recipePayload?.savedId) {
      const record = getRecipeById(recipePayload.savedId)
      if (record) return record.isFavorite
    }
    return recipePayload?.isFavorite || false
  })

  // Checked state for interactive shopping list
  const [checkedItems, setCheckedItems] = useState({})
  const [copied, setCopied] = useState(false)
  const [toast, setToast] = useState(null)

  // Synchronize favorite status on external updates (e.g. cross-tab or history page)
  useEffect(() => {
    if (!recipePayload?.savedId) return

    const handleSync = () => {
      const record = getRecipeById(recipePayload.savedId)
      if (record) {
        setIsFavorite(record.isFavorite)
      }
    }

    window.addEventListener(HISTORY_UPDATE_EVENT, handleSync)
    window.addEventListener('storage', handleSync)

    return () => {
      window.removeEventListener(HISTORY_UPDATE_EVENT, handleSync)
      window.removeEventListener('storage', handleSync)
    }
  }, [recipePayload?.savedId])

  // Scroll to top on page load
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [])

  // Handle toggling favorite
  const handleToggleFavorite = () => {
    if (recipePayload?.savedId) {
      const newStatus = toggleFavorite(recipePayload.savedId)
      setIsFavorite(newStatus)
      const updated = { ...recipePayload, isFavorite: newStatus }
      setRecipePayload(updated)
      sessionStorage.setItem('dishgenie_recipe_data', JSON.stringify(updated))
      setToast({
        text: newStatus ? 'Recipe favorited' : 'Removed from favorites',
        type: newStatus ? 'favorite' : 'success',
      })
    }
  }

  // If no recipe data is found (Direct /recipe access without generating)
  if (!recipePayload || !recipePayload.recipeData) {
    return (
      <div className="min-h-[75vh] flex items-center justify-center px-4 py-16 animate-in fade-in duration-200">
        <div className="max-w-md w-full bg-white rounded-3xl p-8 sm:p-10 border border-stone-200 shadow-xl shadow-stone-900/5 text-center space-y-6">
          <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
            <div className="absolute inset-0 rounded-3xl bg-amber-100/60 blur-lg animate-pulse"></div>
            <div className="relative w-20 h-20 rounded-3xl bg-amber-50 border border-amber-200 flex items-center justify-center text-orange-600 shadow-inner">
              <ChefHat className="w-10 h-10" />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
              No recipe available yet.
            </h2>
            <p className="text-sm text-stone-600 leading-relaxed max-w-sm mx-auto">
              Generate a recipe using your ingredients and preferences.
            </p>
          </div>

          <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
            <button
              type="button"
              onClick={() => navigate('/detect')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/25 hover:shadow-orange-500/35 transition-all hover:-translate-y-0.5 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              <span>Start Cooking</span>
            </button>

            <button
              type="button"
              onClick={() => navigate('/')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-sm font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Home</span>
            </button>
          </div>
        </div>
      </div>
    )
  }

  const { recipeData, preferences, confirmedIngredients = [] } = recipePayload
  const { recipe, raw_text } = recipeData

  // Interactive shopping list toggle
  const toggleShoppingItem = (index) => {
    setCheckedItems((prev) => ({
      ...prev,
      [index]: !prev[index],
    }))
  }

  // Clear all checked items
  const handleClearCompleted = () => {
    setCheckedItems({})
  }

  // Copy recipe to clipboard
  const handleCopyRecipe = () => {
    let fullText = ''
    if (recipe) {
      fullText = `🍲 ${recipe.name}\n${recipe.description || ''}\n\n` +
        `⏱ Time: ${preferences?.cookingTime || 30} min | 👥 Servings: ${preferences?.servings || 2} | 🥗 Diet: ${preferences?.diet || 'Custom'} | 🍽 Cuisine: ${preferences?.cuisine || 'Custom'}\n\n` +
        `INGREDIENTS:\n${(recipe.ingredients || []).map((i) => `• ${i}`).join('\n')}\n\n` +
        `INSTRUCTIONS:\n${(recipe.instructions || []).map((step, idx) => `${idx + 1}. ${step}`).join('\n')}`
    } else {
      fullText = raw_text || 'No recipe content available.'
    }
    navigator.clipboard.writeText(fullText)
    setCopied(true)
    setToast({ text: 'Recipe copied to clipboard', type: 'success' })
    setTimeout(() => setCopied(false), 2200)
  }

  // Print recipe
  const handlePrint = () => {
    window.print()
  }

  // Generate another recipe (go to preferences with ingredients retained)
  const handleGenerateAnother = () => {
    navigate('/detect', {
      state: {
        confirmedIngredients,
        preferences,
        step: 2,
      },
    })
  }

  // Modify ingredients (go back to ingredients scanner with ingredients retained)
  const handleModifyIngredients = () => {
    navigate('/detect', {
      state: {
        confirmedIngredients,
        preferences,
        step: 1,
      },
    })
  }

  return (
    <div className="print-page min-h-[85vh] py-8 sm:py-12 px-4 sm:px-6 lg:px-8 max-w-5xl mx-auto space-y-8">
      
      {/* 1. TOP HEADER & NAVIGATION */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-stone-200">
        <button
          onClick={handleModifyIngredients}
          className="inline-flex items-center gap-2 text-sm font-semibold text-stone-600 hover:text-orange-600 transition-colors cursor-pointer self-start"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>← Back to Ingredients</span>
        </button>

        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
            <span>AI Generated Recipe</span>
          </span>
          <span className="text-xs text-stone-400 font-mono hidden md:inline">
            Local FLAN-T5 Model
          </span>
        </div>
      </div>

      {/* Page Title Label */}
      <div className="no-print flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
            Your DishGenie Recipe
          </h1>
          <p className="text-xs sm:text-sm text-stone-500 mt-1">
            Synthesized locally using verified ingredients and your culinary preferences.
          </p>
        </div>

        {/* Header Action Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Favorite Toggle Button */}
          {recipePayload.savedId && (
            <button
              type="button"
              onClick={handleToggleFavorite}
              className={`inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold transition-all shadow-2xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500 ${
                isFavorite
                  ? 'bg-rose-50 text-rose-600 border border-rose-200 hover:bg-rose-100'
                  : 'bg-white text-stone-700 border border-stone-300 hover:bg-stone-50 hover:border-stone-400'
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
          )}

          <button
            type="button"
            onClick={handleCopyRecipe}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-stone-700 bg-white border border-stone-300 hover:bg-stone-50 hover:border-stone-400 transition-colors shadow-2xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-1"
          >
            {copied ? (
              <>
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700">Copied!</span>
              </>
            ) : (
              <>
                <Copy className="w-3.5 h-3.5 text-stone-500" />
                <span>Copy</span>
              </>
            )}
          </button>

          <button
            type="button"
            onClick={handlePrint}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-bold text-stone-700 bg-white border border-stone-300 hover:bg-stone-50 hover:border-stone-400 transition-colors shadow-2xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-1"
          >
            <Printer className="w-3.5 h-3.5 text-stone-500" />
            <span>Print Recipe</span>
          </button>
        </div>
      </div>

      {/* PRINT-ONLY BRAND & DOCUMENT HEADER */}
      <div className="print-only pb-4 mb-6 border-b-2 border-stone-900">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-black tracking-tight text-stone-900">
              Dish<span className="text-orange-600">Genie</span>
            </h1>
            <span className="text-xs text-stone-500 font-medium">| Smart Recipe Assistant</span>
          </div>
          <div className="text-right text-xs text-stone-500">
            <p>Printed: {new Date().toLocaleDateString()}</p>
          </div>
        </div>
      </div>

      {/* 2. DETECTED & CONFIRMED INGREDIENTS */}
      {confirmedIngredients && confirmedIngredients.length > 0 && (
        <div className="bg-white rounded-3xl p-5 sm:p-6 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-3">
          <div className="flex items-center justify-between pb-3 border-b border-stone-100">
            <h3 className="text-xs font-bold uppercase tracking-wider text-stone-900 flex items-center gap-2">
              <Check className="w-4 h-4 text-emerald-600" />
              <span>Detected & Confirmed Ingredients</span>
            </h3>
            <span className="text-xs text-stone-500 font-mono">
              {confirmedIngredients.length} item{confirmedIngredients.length !== 1 ? 's' : ''}
            </span>
          </div>

          <div className="flex flex-wrap items-center gap-2 pt-1">
            {confirmedIngredients.map((ing) => (
              <span
                key={ing}
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-50/70 border border-emerald-200 text-xs font-bold text-emerald-950 shadow-2xs"
              >
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-base">{INGREDIENT_EMOJIS[ing] || '🥗'}</span>
                <span>{formatIngredientName(ing)}</span>
              </span>
            ))}
            {preferences?.additionalIngredients && preferences.additionalIngredients.trim() && (
              <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-50 border border-stone-200 text-xs font-medium text-stone-700">
                <span>+ Pantry: {preferences.additionalIngredients}</span>
              </span>
            )}
          </div>
        </div>
      )}

      {/* 3. STRUCTURED RECIPE VIEW OR FALLBACK */}
      {recipe ? (
        <div className="space-y-8">
          
          {/* RECIPE HERO CARD */}
          <div className="bg-white rounded-3xl border border-stone-200 shadow-xl shadow-stone-900/5 overflow-hidden">
            <div className="bg-gradient-to-r from-orange-500 via-amber-500 to-orange-600 p-6 sm:p-10 text-white relative">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-xs text-white text-xs font-bold uppercase tracking-wider">
                  🍽 {preferences?.cuisine || 'Custom'} Cuisine
                </span>
                <span className="px-3 py-1 rounded-full bg-white/20 backdrop-blur-xs text-white text-xs font-bold uppercase tracking-wider">
                  🥗 {preferences?.diet || 'Vegetarian'}
                </span>
              </div>

              <h2 className="text-2xl sm:text-4xl lg:text-5xl font-black tracking-tight text-white drop-shadow-xs flex items-center gap-2 sm:gap-3 break-words">
                <span>🍲</span>
                <span>{recipe.name}</span>
              </h2>

              {recipe.description && recipe.description.trim() && (
                <p className="mt-3 text-base sm:text-lg text-orange-50 max-w-3xl leading-relaxed">
                  {recipe.description}
                </p>
              )}

              {/* 5 METADATA CARDS */}
              <div className="mt-8 grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {/* 1. Cooking Time */}
                <div className="bg-white/15 backdrop-blur-md rounded-2xl p-3 text-white border border-white/20">
                  <div className="flex items-center gap-1.5 text-xs text-orange-100 font-semibold mb-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>Cooking Time</span>
                  </div>
                  <p className="text-lg font-black">{preferences?.cookingTime || 30} min</p>
                </div>

                {/* 2. Difficulty */}
                <div className="bg-white/15 backdrop-blur-md rounded-2xl p-3 text-white border border-white/20">
                  <div className="flex items-center gap-1.5 text-xs text-orange-100 font-semibold mb-1">
                    <Flame className="w-3.5 h-3.5" />
                    <span>Difficulty</span>
                  </div>
                  <p className="text-lg font-black">{preferences?.difficulty || 'Easy'}</p>
                </div>

                {/* 3. Servings */}
                <div className="bg-white/15 backdrop-blur-md rounded-2xl p-3 text-white border border-white/20">
                  <div className="flex items-center gap-1.5 text-xs text-orange-100 font-semibold mb-1">
                    <Users className="w-3.5 h-3.5" />
                    <span>Servings</span>
                  </div>
                  <p className="text-lg font-black">{preferences?.servings || 2}</p>
                </div>

                {/* 4. Cuisine */}
                <div className="bg-white/15 backdrop-blur-md rounded-2xl p-3 text-white border border-white/20">
                  <div className="flex items-center gap-1.5 text-xs text-orange-100 font-semibold mb-1">
                    <Utensils className="w-3.5 h-3.5" />
                    <span>Cuisine</span>
                  </div>
                  <p className="text-lg font-black truncate">{preferences?.cuisine || 'Indian'}</p>
                </div>

                {/* 5. Diet */}
                <div className="col-span-2 sm:col-span-1 bg-white/15 backdrop-blur-md rounded-2xl p-3 text-white border border-white/20">
                  <div className="flex items-center gap-1.5 text-xs text-orange-100 font-semibold mb-1">
                    <ChefHat className="w-3.5 h-3.5" />
                    <span>Diet</span>
                  </div>
                  <p className="text-lg font-black truncate">{preferences?.diet || 'Vegetarian'}</p>
                </div>
              </div>
            </div>
          </div>

          {/* DYNAMIC TWO-COLUMN OR SINGLE-COLUMN LAYOUT */}
          {(() => {
            const hasSubstitutions = recipe.substitutions && recipe.substitutions.length > 0
            const hasShoppingList = recipe.shopping_list && recipe.shopping_list.length > 0
            const hasRightColumn = hasSubstitutions || hasShoppingList

            return (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
                
                {/* LEFT COLUMN: INGREDIENTS & INSTRUCTIONS */}
                <div className={`${hasRightColumn ? 'lg:col-span-7' : 'lg:col-span-12'} space-y-8`}>
                  
                  {/* INGREDIENTS SECTION */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-5">
                    <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-orange-100 text-orange-600 flex items-center justify-center font-bold">
                          <ChefHat className="w-4 h-4" />
                        </div>
                        <h3 className="text-lg font-extrabold text-stone-900">
                          Ingredients
                        </h3>
                      </div>
                      <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-stone-100 text-stone-600">
                        {recipe.ingredients ? recipe.ingredients.length : 0} items
                      </span>
                    </div>

                    {recipe.ingredients && recipe.ingredients.length > 0 ? (
                      <div className={`grid grid-cols-1 ${hasRightColumn ? 'sm:grid-cols-2' : 'sm:grid-cols-3'} gap-3`}>
                        {recipe.ingredients.map((item, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-3 p-3.5 rounded-2xl bg-stone-50 border border-stone-200/80 hover:border-orange-200 transition-colors"
                          >
                            <span className="w-2.5 h-2.5 rounded-full bg-orange-500 shrink-0"></span>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-bold text-stone-800 break-words">
                                {item}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-stone-500 italic">No ingredients specified.</p>
                    )}
                  </div>

                  {/* COOKING INSTRUCTIONS SECTION */}
                  <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-6">
                    <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                      <div className="flex items-center gap-2.5">
                        <div className="w-8 h-8 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center font-bold">
                          <BookOpen className="w-4 h-4" />
                        </div>
                        <h3 className="text-lg font-extrabold text-stone-900">
                          Cooking Instructions
                        </h3>
                      </div>
                      <span className="text-xs text-stone-400 font-mono">
                        Step-by-step
                      </span>
                    </div>

                    {recipe.instructions && recipe.instructions.length > 0 ? (
                      <div className="space-y-4">
                        {recipe.instructions.map((step, idx) => (
                          <div
                            key={idx}
                            className="flex items-start gap-4 p-4 rounded-2xl bg-stone-50 border border-stone-200/80 hover:bg-stone-50/90 transition-colors"
                          >
                            <span className="w-9 h-9 rounded-xl bg-gradient-to-br from-orange-500 to-amber-600 text-white font-mono text-sm font-black flex items-center justify-center shrink-0 shadow-xs">
                              {String(idx + 1).padStart(2, '0')}
                            </span>
                            <div className="flex-1 pt-1">
                              <p className="text-sm sm:text-base text-stone-800 leading-relaxed font-normal">
                                {step}
                              </p>
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-stone-500 italic">No cooking instructions provided.</p>
                    )}
                  </div>

                </div>

                {/* RIGHT COLUMN: SUBSTITUTIONS & SHOPPING LIST (Hidden if neither is present) */}
                {hasRightColumn && (
                  <div className="lg:col-span-5 space-y-8">
                    
                    {/* POSSIBLE SUBSTITUTIONS SECTION (Hidden if empty) */}
                    {hasSubstitutions && (
                      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-5">
                        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-xl bg-amber-50 text-amber-600 border border-amber-200 flex items-center justify-center font-bold">
                              <Sparkles className="w-4 h-4" />
                            </div>
                            <h3 className="text-base font-extrabold text-stone-900">
                              Possible Substitutions
                            </h3>
                          </div>
                        </div>

                        <div className="space-y-3">
                          {recipe.substitutions.map((sub, idx) => (
                            <div
                              key={idx}
                              className="p-3.5 rounded-2xl bg-amber-50/70 border border-amber-200/80 text-xs text-amber-950 space-y-1.5"
                            >
                              <div className="flex items-center justify-between font-bold text-amber-900">
                                <span>{sub.ingredient}</span>
                                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded-md bg-amber-100 text-amber-800">
                                  Swap
                                </span>
                              </div>
                              <div className="flex items-center gap-1.5 text-stone-700">
                                <span className="text-amber-500 font-bold">↓</span>
                                <span className="font-semibold text-stone-900">{sub.replacement}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* SHOPPING LIST SECTION (Hidden if empty) */}
                    {hasShoppingList && (
                      <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-5">
                        <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                          <div className="flex items-center gap-2.5">
                            <div className="w-8 h-8 rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center font-bold">
                              <ShoppingBag className="w-4 h-4" />
                            </div>
                            <h3 className="text-base font-extrabold text-stone-900">
                              Shopping List
                            </h3>
                          </div>

                          {/* Clear completed button */}
                          {Object.values(checkedItems).some(Boolean) && (
                            <button
                              type="button"
                              onClick={handleClearCompleted}
                              className="no-print text-xs font-semibold text-stone-500 hover:text-stone-800 transition-colors underline underline-offset-2 cursor-pointer"
                            >
                              Clear completed
                            </button>
                          )}
                        </div>

                        <div className="space-y-2">
                          {recipe.shopping_list.map((item, idx) => {
                            const isChecked = !!checkedItems[idx]
                            return (
                              <div
                                key={idx}
                                onClick={() => toggleShoppingItem(idx)}
                                className={`flex items-center gap-3 p-3 rounded-2xl border transition-all cursor-pointer ${
                                  isChecked
                                    ? 'bg-emerald-50/50 border-emerald-200 text-stone-400'
                                    : 'bg-stone-50 border-stone-200 hover:border-emerald-300 text-stone-800'
                                }`}
                              >
                                <button
                                  type="button"
                                  className="text-emerald-600 shrink-0"
                                  aria-label={isChecked ? 'Uncheck item' : 'Check item'}
                                >
                                  {isChecked ? (
                                    <CheckSquare className="w-5 h-5 text-emerald-600" />
                                  ) : (
                                    <Square className="w-5 h-5 text-stone-300" />
                                  )}
                                </button>
                                <span
                                  className={`text-xs sm:text-sm font-medium select-none ${
                                    isChecked ? 'line-through text-stone-400' : 'text-stone-800'
                                  }`}
                                >
                                  {item}
                                </span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )}

                  </div>
                )}

              </div>
            )
          })()}
        </div>
      ) : (
        /* RAW MODEL FALLBACK (If recipe == null but raw_text exists) */
        <div className="bg-white rounded-3xl p-6 sm:p-10 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-6">
          <div className="flex items-center gap-3 pb-4 border-b border-stone-100">
            <div className="w-10 h-10 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-extrabold text-stone-900">
                Generated Recipe
              </h2>
              <p className="text-xs text-stone-500">
                Direct narrative output from the local FLAN-T5 model
              </p>
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-stone-50 border border-stone-200 font-sans text-sm sm:text-base text-stone-800 leading-relaxed whitespace-pre-wrap">
            {raw_text || 'No recipe text generated.'}
          </div>
        </div>
      )}

      {/* 4. BOTTOM ACTION BUTTONS */}
      <div className="no-print pt-6 border-t border-stone-200 flex flex-col sm:flex-row items-center justify-between gap-4">
        <button
          type="button"
          onClick={handleModifyIngredients}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-bold text-stone-700 bg-white border border-stone-300 hover:bg-stone-50 hover:border-stone-400 transition-all shadow-xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>← Modify Ingredients</span>
        </button>

        <div className="w-full sm:w-auto flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={handlePrint}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-2xl text-xs sm:text-sm font-bold text-stone-700 bg-white border border-stone-300 hover:bg-stone-50 transition-all shadow-xs cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2"
          >
            <Printer className="w-4 h-4" />
            <span>Print Recipe</span>
          </button>

          <button
            type="button"
            onClick={handleGenerateAnother}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-full text-xs sm:text-sm font-extrabold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/25 hover:shadow-orange-500/35 transition-all hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>↻ Generate Another Recipe</span>
          </button>
        </div>
      </div>

      {toast && (
        <Toast
          message={toast.text}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  )
}
