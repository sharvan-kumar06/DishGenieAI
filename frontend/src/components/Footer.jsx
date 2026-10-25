import { Link } from 'react-router-dom'
import { UtensilsCrossed } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-stone-900 text-stone-300 border-t border-stone-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-14 lg:py-16">
        <div className="grid grid-cols-1 md:grid-cols-12 gap-10 items-center justify-between">
          
          {/* Brand Info */}
          <div className="md:col-span-6 space-y-3">
            <Link to="/" className="inline-flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-orange-500/20 text-orange-400 flex items-center justify-center border border-orange-500/30">
                <UtensilsCrossed className="w-5 h-5" />
              </div>
              <span className="text-xl font-bold tracking-tight text-white">
                Dish<span className="text-orange-400">Genie</span>
              </span>
            </Link>
            
            <p className="text-stone-400 text-sm italic">
              "Smart recipes. Simple cooking."
            </p>
            
            <p className="text-xs text-stone-500 max-w-sm">
              An AI-assisted culinary system that bridges raw ingredient detection with generative recipe synthesis.
            </p>
          </div>

          {/* Navigation Links */}
          <div className="md:col-span-6 flex flex-wrap items-center justify-start md:justify-end gap-6 sm:gap-8">
            <Link
              to="/"
              className="text-sm font-medium text-stone-400 hover:text-white transition-colors"
            >
              Home
            </Link>
            <Link
              to="/detect"
              className="text-sm font-medium text-stone-400 hover:text-white transition-colors"
            >
              Studio
            </Link>
            <Link
              to="/history"
              className="text-sm font-medium text-stone-400 hover:text-white transition-colors"
            >
              History
            </Link>
            <Link
              to="/favorites"
              className="text-sm font-medium text-stone-400 hover:text-white transition-colors"
            >
              Favorites
            </Link>
            <Link
              to="/detect"
              className="text-sm font-semibold text-orange-400 hover:text-orange-300 transition-colors"
            >
              Get Started
            </Link>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-stone-800 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-stone-500">
          <p>© {new Date().getFullYear()} DishGenie. All rights reserved.</p>
          <p className="inline-flex items-center gap-1.5 text-stone-400 font-medium bg-stone-800/60 px-3 py-1.5 rounded-full border border-stone-700/60">
            <span>Intelligent On-Device Recipe Generation System</span>
          </p>
        </div>
      </div>
    </footer>
  )
}
