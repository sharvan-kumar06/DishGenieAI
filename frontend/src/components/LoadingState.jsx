import { Loader2, Sparkles } from 'lucide-react'

/**
 * DishGenie Global / Reusable Loading Component
 * 
 * Supports:
 * - 'fullscreen': Modal/overlay for blocking operations (e.g. recipe generation)
 * - 'card': Centered card loading state for sections
 * - 'inline': Compact inline spinner for buttons or headers
 */
export default function LoadingState({
  message = 'Loading...',
  subMessage = '',
  variant = 'card',
  className = '',
}) {
  if (variant === 'inline') {
    return (
      <div
        role="status"
        aria-live="polite"
        className={`inline-flex items-center gap-2 text-xs font-semibold text-stone-600 ${className}`}
      >
        <Loader2 className="w-4 h-4 text-orange-500 animate-spin shrink-0" aria-hidden="true" />
        <span>{message}</span>
        <span className="sr-only">{message}</span>
      </div>
    )
  }

  if (variant === 'fullscreen') {
    return (
      <div
        role="status"
        aria-live="polite"
        className="fixed inset-0 z-50 bg-[#faf8f5]/95 backdrop-blur-md flex flex-col items-center justify-center p-6 text-center animate-in fade-in duration-300"
      >
        <div className="max-w-md w-full space-y-6">
          {/* Subtle animated cooking vessel badge */}
          <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
            <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-orange-400 to-amber-300 opacity-20 blur-xl animate-pulse"></div>
            <div className="w-20 h-20 rounded-3xl bg-white border border-orange-200 shadow-xl flex items-center justify-center text-3xl">
              🍳
            </div>
            <div className="absolute -top-1 -right-1 w-7 h-7 rounded-full bg-orange-500 text-white flex items-center justify-center shadow-md animate-bounce">
              <Sparkles className="w-3.5 h-3.5" aria-hidden="true" />
            </div>
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
              {message}
            </h2>
            {subMessage && (
              <p className="text-xs sm:text-sm text-stone-600 max-w-sm mx-auto leading-relaxed">
                {subMessage}
              </p>
            )}
          </div>

          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-stone-200 text-xs font-semibold text-stone-600 shadow-xs">
            <Loader2 className="w-3.5 h-3.5 text-orange-500 animate-spin shrink-0" aria-hidden="true" />
            <span>Processing with local AI...</span>
          </div>
          <span className="sr-only">{message}</span>
        </div>
      </div>
    )
  }

  // Default 'card' variant
  return (
    <div
      role="status"
      aria-live="polite"
      className={`p-8 rounded-3xl bg-amber-50/70 border border-amber-200/80 text-center space-y-3 ${className}`}
    >
      <div className="w-12 h-12 mx-auto rounded-2xl bg-white border border-amber-200 flex items-center justify-center text-orange-600 shadow-xs">
        <Loader2 className="w-6 h-6 animate-spin" aria-hidden="true" />
      </div>
      <div className="space-y-1">
        <h3 className="font-bold text-stone-900 text-base">{message}</h3>
        {subMessage && (
          <p className="text-xs text-stone-600 max-w-sm mx-auto leading-relaxed">
            {subMessage}
          </p>
        )}
      </div>
      <span className="sr-only">{message}</span>
    </div>
  )
}
