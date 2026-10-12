import { Trash2 } from 'lucide-react'
import { INGREDIENT_EMOJIS, formatIngredientName } from '../services/api'

export default function IngredientItem({ ingredient, onRemove }) {
  const emoji = INGREDIENT_EMOJIS[ingredient] || '🥗'
  const displayName = formatIngredientName(ingredient)

  return (
    <div className="flex items-center justify-between gap-3 px-4 py-2.5 rounded-2xl bg-white border border-stone-200/90 shadow-xs hover:border-orange-300 transition-colors group">
      <div className="flex items-center gap-2.5">
        <span className="text-xl" role="img" aria-label={displayName}>
          {emoji}
        </span>
        <span className="text-sm font-bold text-stone-800">
          {displayName}
        </span>
      </div>

      {onRemove && (
        <button
          type="button"
          onClick={() => onRemove(ingredient)}
          className="p-2 min-w-[36px] min-h-[36px] flex items-center justify-center rounded-xl text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
          aria-label={`Remove ${displayName}`}
          title={`Remove ${displayName}`}
        >
          <Trash2 className="w-4 h-4" />
        </button>
      )}
    </div>
  )
}
