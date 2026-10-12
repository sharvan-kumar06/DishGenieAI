import { Link } from 'react-router-dom'
import { UtensilsCrossed, ArrowLeft, Sparkles } from 'lucide-react'

export default function NotFound() {
  return (
    <div className="min-h-[75vh] flex items-center justify-center px-4 py-16 animate-in fade-in duration-200">
      <div className="max-w-lg w-full bg-white rounded-3xl p-6 sm:p-12 border border-stone-200 shadow-xl shadow-stone-900/5 text-center space-y-6">
        
        {/* Animated Icon Badge */}
        <div className="relative w-20 h-20 mx-auto flex items-center justify-center">
          <div className="absolute inset-0 rounded-3xl bg-amber-100/60 blur-lg animate-pulse"></div>
          <div className="relative w-20 h-20 rounded-3xl bg-amber-50 border border-amber-200 flex items-center justify-center text-orange-600 shadow-inner">
            <UtensilsCrossed className="w-10 h-10" />
          </div>
        </div>

        {/* 404 Badge */}
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-stone-100 text-stone-600 text-xs font-mono font-bold">
          <span>Error 404</span>
          <span className="text-stone-300">•</span>
          <span>Page Not Found</span>
        </div>

        {/* Heading */}
        <div className="space-y-2">
          <h1 className="text-3xl sm:text-4xl font-extrabold text-stone-900 tracking-tight">
            Oops! This recipe doesn't exist.
          </h1>
          <p className="text-sm sm:text-base text-stone-600 max-w-sm mx-auto leading-relaxed">
            The page or recipe you are looking for may have been moved, removed, or hasn't been cooked yet in DishGenie's kitchen.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full text-sm font-bold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/20 hover:shadow-orange-500/30 transition-all hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Back to DishGenie</span>
          </Link>

          <Link
            to="/detect"
            className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-3.5 rounded-full text-sm font-semibold text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2"
          >
            <Sparkles className="w-4 h-4 text-orange-500" />
            <span>Start Cooking</span>
          </Link>
        </div>

      </div>
    </div>
  )
}
