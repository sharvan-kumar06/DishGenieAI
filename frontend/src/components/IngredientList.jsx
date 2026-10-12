import { Plus, CheckCircle2, ListPlus, Salad } from 'lucide-react'
import IngredientItem from './IngredientItem'

export default function IngredientList({
  ingredients = [],
  onRemove,
  onAddAnother,
  onQuickAdd,
}) {
  if (!ingredients || ingredients.length === 0) {
    return (
      <div className="bg-stone-50/60 rounded-3xl p-6 sm:p-8 border border-dashed border-stone-300 text-center space-y-4">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 border border-amber-200/80 flex items-center justify-center text-orange-600 shadow-2xs">
          <Salad className="w-7 h-7" aria-hidden="true" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-stone-900">
            No ingredients added yet.
          </h3>
          <p className="text-xs sm:text-sm text-stone-500 max-w-sm mx-auto leading-relaxed">
            Upload an ingredient image or add an ingredient manually.
          </p>
        </div>
        <div className="pt-1 flex flex-wrap items-center justify-center gap-3">
          {onQuickAdd && (
            <button
              type="button"
              onClick={onQuickAdd}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-orange-800 bg-orange-100/80 hover:bg-orange-200 border border-orange-200 transition-colors cursor-pointer shadow-2xs"
            >
              <Plus className="w-4 h-4" />
              <span>Add Ingredient Manually</span>
            </button>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="bg-stone-50/80 rounded-3xl p-6 border border-stone-200/90 shadow-xs space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="w-5 h-5 text-emerald-600" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-stone-700">
            Confirmed Ingredients ({ingredients.length})
          </h3>
        </div>
        <span className="text-xs text-stone-500 font-medium hidden sm:inline">
          Ready for recipe personalization
        </span>
      </div>

      {/* Grid of Confirmed Ingredient Badges */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {ingredients.map((ing) => (
          <IngredientItem
            key={ing}
            ingredient={ing}
            onRemove={onRemove}
          />
        ))}
      </div>

      {/* Add Another Actions */}
      <div className="pt-2 flex flex-wrap items-center gap-3">
        {onAddAnother && (
          <button
            type="button"
            onClick={onAddAnother}
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-bold text-orange-700 bg-orange-100/70 hover:bg-orange-200/80 border border-orange-200 transition-colors cursor-pointer"
          >
            <Plus className="w-4 h-4" />
            <span>+ Add another ingredient</span>
          </button>
        )}

        {onQuickAdd && (
          <button
            type="button"
            onClick={onQuickAdd}
            className="inline-flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-stone-600 hover:text-stone-900 bg-white hover:bg-stone-100 border border-stone-200 transition-colors cursor-pointer"
          >
            <ListPlus className="w-4 h-4 text-stone-400" />
            <span>Select from 247 categories</span>
          </button>
        )}
      </div>
    </div>
  )
}
