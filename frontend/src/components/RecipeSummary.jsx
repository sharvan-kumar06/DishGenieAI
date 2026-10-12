import { Sparkles, Edit3, CheckCircle2, Loader2, PlusCircle } from 'lucide-react'
import { INGREDIENT_EMOJIS, formatIngredientName } from '../services/api'

export default function RecipeSummary({
  ingredients = [],
  preferences = {},
  onGenerate,
  onEditPreferences,
  isGenerating = false,
}) {
  const {
    diet = 'Vegetarian',
    cuisine = 'Indian',
    cookingTime = 30,
    difficulty = 'Easy',
    servings = 2,
    additionalIngredients = '',
  } = preferences

  const hasIngredients = ingredients && ingredients.length > 0

  return (
    <div
      id="recipe-summary"
      className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-6 animate-in fade-in duration-300"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-stone-100">
        <div>
          <span className="text-[11px] font-bold uppercase tracking-wider text-orange-600 bg-orange-50 px-2.5 py-1 rounded-full border border-orange-200">
            Step 3: Review & Generate
          </span>
          <h3 className="text-xl sm:text-2xl font-extrabold text-stone-900 mt-2">
            YOUR RECIPE SUMMARY
          </h3>
          <p className="text-xs sm:text-sm text-stone-500 mt-0.5">
            Confirm your ingredients and preferences before local AI synthesis.
          </p>
        </div>

        <button
          type="button"
          onClick={onEditPreferences}
          disabled={isGenerating}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors self-start sm:self-auto cursor-pointer disabled:opacity-50"
        >
          <Edit3 className="w-3.5 h-3.5 text-stone-500" />
          <span>Edit Preferences</span>
        </button>
      </div>

      {/* Summary Content Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* Ingredients Block */}
        <div className="p-4 sm:p-5 rounded-2xl bg-amber-50/60 border border-amber-200/80 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold uppercase tracking-wider text-amber-900 flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Confirmed Ingredients</span>
            </span>
            <span className="text-xs font-mono text-amber-800 font-semibold">
              {ingredients.length} item{ingredients.length !== 1 ? 's' : ''}
            </span>
          </div>

          {hasIngredients ? (
            <div className="flex flex-wrap gap-2 pt-1">
              {ingredients.map((ing) => (
                <span
                  key={ing}
                  className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-white border border-amber-200 text-xs font-bold text-stone-800 shadow-2xs"
                >
                  <span className="text-sm">{INGREDIENT_EMOJIS[ing] || '🥗'}</span>
                  <span>{formatIngredientName(ing)}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-rose-600 font-semibold italic">
              Please add at least one ingredient to generate a recipe.
            </p>
          )}

          {additionalIngredients && (
            <div className="pt-2 border-t border-amber-200/60 flex items-start gap-1.5 text-xs text-amber-950">
              <PlusCircle className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Additional Ingredients: </span>
                <span className="text-stone-700">{additionalIngredients}</span>
              </div>
            </div>
          )}
        </div>

        {/* Preferences Parameters Block */}
        <div className="p-4 sm:p-5 rounded-2xl bg-stone-50 border border-stone-200 space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-stone-700 block">
            Selected Preferences
          </span>

          <div className="grid grid-cols-2 gap-3 text-xs">
            <div className="p-2.5 rounded-xl bg-white border border-stone-200 shadow-2xs">
              <span className="text-stone-400 font-medium block text-[10px] uppercase">Diet</span>
              <span className="font-bold text-stone-900">{diet}</span>
            </div>

            <div className="p-2.5 rounded-xl bg-white border border-stone-200 shadow-2xs">
              <span className="text-stone-400 font-medium block text-[10px] uppercase">Cuisine</span>
              <span className="font-bold text-stone-900">{cuisine}</span>
            </div>

            <div className="p-2.5 rounded-xl bg-white border border-stone-200 shadow-2xs">
              <span className="text-stone-400 font-medium block text-[10px] uppercase">Cooking Time</span>
              <span className="font-bold text-stone-900">{cookingTime} minutes</span>
            </div>

            <div className="p-2.5 rounded-xl bg-white border border-stone-200 shadow-2xs">
              <span className="text-stone-400 font-medium block text-[10px] uppercase">Difficulty</span>
              <span className="font-bold text-stone-900">{difficulty}</span>
            </div>

            <div className="col-span-2 p-2.5 rounded-xl bg-white border border-stone-200 shadow-2xs flex items-center justify-between">
              <span className="text-stone-400 font-medium text-[10px] uppercase">Servings</span>
              <span className="font-bold text-stone-900">{servings} serving{servings !== 1 ? 's' : ''}</span>
            </div>
          </div>
        </div>

      </div>

      {/* Action Footer */}
      <div className="pt-4 border-t border-stone-100 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-xs text-stone-500 text-center sm:text-left">
          Ready to synthesize? Click below to send your parameters to the local AI service.
        </p>

        <div className="w-full sm:w-auto flex flex-col sm:flex-row items-center gap-3">
          <button
            type="button"
            onClick={onEditPreferences}
            disabled={isGenerating}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-3.5 rounded-full text-xs font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer disabled:opacity-50"
          >
            <Edit3 className="w-3.5 h-3.5" />
            <span>Edit Preferences</span>
          </button>

          <button
            type="button"
            onClick={onGenerate}
            disabled={!hasIngredients || isGenerating}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-3.5 rounded-full text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-lg shadow-orange-500/25 hover:shadow-orange-500/35 transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
          >
            {isGenerating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                <span>Generating...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" aria-hidden="true" />
                <span>Generate My Recipe</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
