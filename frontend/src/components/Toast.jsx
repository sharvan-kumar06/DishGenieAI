import { useEffect } from 'react'
import { CheckCircle2, Heart, Sparkles, X } from 'lucide-react'

/**
 * Subtle toast notification for user feedback
 * (e.g. "Ingredient added", "Recipe favorited", "Recipe saved")
 */
export default function Toast({ message, type = 'success', onClose, duration = 3000 }) {
  useEffect(() => {
    if (!duration || !onClose) return
    const timer = setTimeout(() => {
      onClose()
    }, duration)
    return () => clearTimeout(timer)
  }, [duration, onClose])

  if (!message) return null

  const getIcon = () => {
    switch (type) {
      case 'favorite':
        return <Heart className="w-4 h-4 text-rose-500 fill-rose-500 shrink-0" aria-hidden="true" />
      case 'sparkle':
        return <Sparkles className="w-4 h-4 text-amber-500 shrink-0" aria-hidden="true" />
      case 'success':
      default:
        return <CheckCircle2 className="w-4 h-4 text-emerald-500 shrink-0" aria-hidden="true" />
    }
  }

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed bottom-6 right-4 sm:right-6 left-4 sm:left-auto max-w-sm z-50 flex items-center justify-between sm:justify-start gap-3 px-4 py-3 rounded-2xl bg-stone-900/95 text-white text-xs font-semibold shadow-xl shadow-stone-900/20 backdrop-blur-xs border border-stone-800 animate-in slide-in-from-bottom-3 duration-200"
    >
      {getIcon()}
      <span>{message}</span>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="ml-2 p-1 rounded-lg text-stone-400 hover:text-white hover:bg-stone-800 transition-colors cursor-pointer"
          aria-label="Dismiss notification"
        >
          <X className="w-3.5 h-3.5" aria-hidden="true" />
        </button>
      )}
    </div>
  )
}
