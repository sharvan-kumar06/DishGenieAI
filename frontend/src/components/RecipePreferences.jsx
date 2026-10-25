import { Sliders, Sparkles, PlusCircle, Loader2 } from 'lucide-react'
import PreferenceSelect from './PreferenceSelect'

export default function RecipePreferences({
  preferences,
  onChange,
  onSubmit,
  ingredientsCount = 0,
  isGenerating = false,
  errors = {},
}) {
  const dietOptions = ['Vegetarian', 'Vegan', 'Non-Vegetarian', 'No Preference']
  const cuisineOptions = ['Indian', 'Italian', 'Chinese', 'Mexican', 'American', 'Any Cuisine']
  const timeOptions = [
    { label: '⏱ 15 min', value: 15 },
    { label: '⏱ 30 min', value: 30 },
    { label: '⏱ 45 min', value: 45 },
    { label: '⏱ 60+ min', value: 60 },
  ]
  const difficultyOptions = ['Easy', 'Medium', 'Hard']
  const servingsOptions = [
    { label: '1 serving', value: 1 },
    { label: '2 servings', value: 2 },
    { label: '3 servings', value: 3 },
    { label: '4 servings', value: 4 },
    { label: '5+ servings', value: 5 },
  ]

  const updateField = (field, val) => {
    onChange({
      ...preferences,
      [field]: val,
    })
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!isGenerating) {
      onSubmit()
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-8 animate-in fade-in duration-300"
    >
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-stone-100">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-2xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600 shadow-xs">
            <Sliders className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-xl sm:text-2xl font-extrabold text-stone-900">
              Customize Your Recipe
            </h2>
            <p className="text-xs sm:text-sm text-stone-500 mt-0.5">
              Fine-tune dietary rules, cuisine style, and kitchen constraints
            </p>
          </div>
        </div>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-stone-100 text-stone-700 text-xs font-semibold self-start sm:self-auto">
          <span>{ingredientsCount} ingredient{ingredientsCount !== 1 ? 's' : ''} confirmed</span>
        </div>
      </div>

      {/* Grid of Preferences Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
        
        {/* 1. Diet */}
        <PreferenceSelect
          label="1. Diet Type"
          value={preferences.diet}
          options={dietOptions}
          onChange={(val) => updateField('diet', val)}
          hint="Required"
          error={errors.diet}
        />

        {/* 2. Cuisine */}
        <PreferenceSelect
          label="2. Cuisine Style"
          value={preferences.cuisine}
          options={cuisineOptions}
          onChange={(val) => updateField('cuisine', val)}
          hint="Required"
          error={errors.cuisine}
        />

        {/* 3. Cooking Time */}
        <PreferenceSelect
          label="3. Cooking Time"
          value={preferences.cookingTime}
          options={timeOptions}
          onChange={(val) => updateField('cookingTime', val)}
          hint="Target duration"
          error={errors.cookingTime}
        />

        {/* 4. Difficulty */}
        <PreferenceSelect
          label="4. Cooking Skill / Difficulty"
          value={preferences.difficulty}
          options={difficultyOptions}
          onChange={(val) => updateField('difficulty', val)}
          hint="Recipe complexity"
          error={errors.difficulty}
        />

        {/* 5. Servings */}
        <div className="md:col-span-2">
          <PreferenceSelect
            label="5. Portion Size / Servings"
            value={preferences.servings}
            options={servingsOptions}
            onChange={(val) => updateField('servings', val)}
            hint="Meal count"
            error={errors.servings}
          />
        </div>

        {/* 6. Additional Ingredients (Optional text input) */}
        <div className="md:col-span-2 space-y-2">
          <div className="flex items-center justify-between">
            <label htmlFor="additional-ingredients" className="text-xs font-bold uppercase tracking-wider text-stone-700">
              6. Any Additional Ingredients?
            </label>
            <span className="text-[11px] text-stone-400 font-medium">
              Optional pantry additions
            </span>
          </div>
          <div className="relative">
            <PlusCircle className="w-5 h-5 text-stone-400 absolute left-3.5 top-1/2 -translate-y-1/2" aria-hidden="true" />
            <input
              id="additional-ingredients"
              type="text"
              value={preferences.additionalIngredients}
              onChange={(e) => updateField('additionalIngredients', e.target.value)}
              placeholder="e.g. onion, garlic, cheese, olive oil, spices..."
              className="w-full pl-11 pr-4 py-3 bg-stone-50 border border-stone-200 rounded-2xl text-sm text-stone-800 placeholder-stone-400 focus:outline-hidden focus:ring-2 focus:ring-orange-500 focus:bg-white transition-all shadow-xs"
            />
          </div>
          <p className="text-[11px] text-stone-500">
            Comma-separated ingredients you already have on hand to complement your detected items.
          </p>
        </div>

      </div>

      {/* Action CTA Button */}
      <div className="pt-6 border-t border-stone-100 flex flex-col sm:flex-row items-center justify-between gap-4">
        <p className="text-xs text-stone-500 text-center sm:text-left">
          DishGenie will craft your recipe using your confirmed pantry items and preferences.
        </p>

        <button
          type="submit"
          disabled={ingredientsCount === 0 || isGenerating}
          className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-8 py-4 rounded-full text-base font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-lg shadow-orange-500/25 hover:shadow-orange-500/35 transition-all duration-200 hover:-translate-y-0.5 disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:translate-y-0 cursor-pointer"
        >
          {isGenerating ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" aria-hidden="true" />
              <span>Generating...</span>
            </>
          ) : (
            <>
              <Sparkles className="w-5 h-5" aria-hidden="true" />
              <span>Choose Dish Style & Generate</span>
            </>
          )}
        </button>
      </div>
    </form>
  )
}
