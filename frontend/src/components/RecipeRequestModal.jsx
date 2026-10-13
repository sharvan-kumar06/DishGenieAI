import { useState } from 'react'
import { Check, Copy, CheckCircle2, X, Sparkles, Code2, ArrowLeft } from 'lucide-react'
import { INGREDIENT_EMOJIS, formatIngredientName } from '../services/api'

export default function RecipeRequestModal({
  requestPayload,
  onClose,
  onEdit,
}) {
  const [copied, setCopied] = useState(false)

  if (!requestPayload) return null

  const jsonString = JSON.stringify(requestPayload, null, 2)

  const handleCopy = () => {
    navigator.clipboard.writeText(jsonString)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 bg-stone-900/60 backdrop-blur-xs animate-in fade-in duration-200 overflow-y-auto">
      <div className="bg-white rounded-3xl p-6 sm:p-8 max-w-2xl w-full shadow-2xl border border-stone-200 space-y-6 my-auto animate-in zoom-in-95 duration-200">
        
        {/* Modal Header */}
        <div className="flex items-start justify-between pb-4 border-b border-stone-100">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-2xl bg-emerald-50 border border-emerald-200 flex items-center justify-center text-emerald-600 shadow-xs">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                Step 5 Workflow Complete
              </div>
              <h3 className="text-xl font-extrabold text-stone-900 mt-1">
                Recipe Request Payload Ready
              </h3>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-stone-400 hover:text-stone-700 hover:bg-stone-100 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Selected Summary Chips */}
        <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200/80 space-y-3">
          <p className="text-xs font-bold uppercase tracking-wider text-stone-600">
            Confirmed Inputs Summary
          </p>

          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs text-stone-500 font-semibold">Ingredients:</span>
            {requestPayload.ingredients.map((ing) => (
              <span
                key={ing}
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-xl bg-white border border-stone-200 text-xs font-bold text-stone-800 shadow-2xs"
              >
                <span>{INGREDIENT_EMOJIS[ing] || '🥗'}</span>
                <span>{formatIngredientName(ing)}</span>
              </span>
            ))}
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-stone-200/60 text-xs">
            <div>
              <span className="text-stone-400 block text-[11px]">Diet</span>
              <span className="font-bold text-stone-800">{requestPayload.preferences.diet}</span>
            </div>
            <div>
              <span className="text-stone-400 block text-[11px]">Cuisine</span>
              <span className="font-bold text-stone-800">{requestPayload.preferences.cuisine}</span>
            </div>
            <div>
              <span className="text-stone-400 block text-[11px]">Duration</span>
              <span className="font-bold text-stone-800">{requestPayload.preferences.cookingTime} mins</span>
            </div>
            <div>
              <span className="text-stone-400 block text-[11px]">Skill / Servings</span>
              <span className="font-bold text-stone-800">
                {requestPayload.preferences.difficulty} • {requestPayload.preferences.servings}p
              </span>
            </div>
          </div>

          {requestPayload.preferences.additionalIngredients && (
            <div className="pt-2 border-t border-stone-200/60 text-xs">
              <span className="text-stone-400 block text-[11px]">Pantry Additions</span>
              <span className="font-medium text-stone-800">
                {requestPayload.preferences.additionalIngredients}
              </span>
            </div>
          )}
        </div>

        {/* JSON Code Viewer with Copy Button */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs font-bold text-stone-700">
              <Code2 className="w-4 h-4 text-orange-600" />
              <span>Structured Payload (JSON)</span>
            </div>
            <button
              type="button"
              onClick={handleCopy}
              className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg text-xs font-semibold text-stone-600 hover:text-stone-900 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="text-emerald-700">Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy JSON</span>
                </>
              )}
            </button>
          </div>

          <pre className="p-4 rounded-2xl bg-stone-900 text-amber-200 text-xs font-mono overflow-x-auto max-h-56 leading-relaxed border border-stone-800 shadow-inner">
            <code>{jsonString}</code>
          </pre>
        </div>

        {/* Developer / Project Note */}
        <div className="p-3.5 rounded-xl bg-orange-50 border border-orange-200 text-xs text-orange-900">
          <p className="font-semibold flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-orange-600" />
            Local GenAI Payload Architecture
          </p>
          <p className="mt-1 text-orange-800">
            This structured request object is sent directly to the local Qwen2.5 GenAI and SQLite recipe database endpoint to synthesize step-by-step cooking instructions, substitutions, and shopping lists.
          </p>
        </div>

        {/* Modal Actions */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-end gap-3">
          <button
            type="button"
            onClick={onEdit}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl text-xs font-bold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Edit Preferences</span>
          </button>
          <button
            type="button"
            onClick={onClose}
            className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-2.5 rounded-xl text-xs font-bold text-white bg-stone-900 hover:bg-stone-800 transition-colors cursor-pointer"
          >
            Done
          </button>
        </div>

      </div>
    </div>
  )
}
