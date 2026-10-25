import { Link } from 'react-router-dom'
import { Sparkles, ArrowRight, Camera, CheckCircle2, Clock } from 'lucide-react'

export default function Hero() {
  const handleScroll = (href) => {
    const elem = document.querySelector(href)
    if (elem) elem.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <section className="relative overflow-hidden pt-10 pb-20 md:pt-16 md:pb-28">
      {/* Subtle warm background glow blobs */}
      <div className="absolute top-0 right-1/4 w-96 h-96 bg-orange-200/40 rounded-full blur-3xl -z-10 pointer-events-none animate-glow" />
      <div className="absolute top-1/3 left-10 w-80 h-80 bg-amber-200/30 rounded-full blur-3xl -z-10 pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
          
          {/* Left Column: Content */}
          <div className="lg:col-span-7 text-center lg:text-left space-y-6">
            {/* Pill Badge */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-orange-100/80 border border-orange-200 text-orange-800 text-xs font-semibold shadow-xs">
              <Sparkles className="w-3.5 h-3.5 text-orange-600" />
              <span>Smart Recipe Assistant • AI Kitchen SaaS</span>
            </div>

            {/* Main Heading */}
            <h1 className="text-3xl sm:text-5xl xl:text-6xl font-extrabold tracking-tight text-stone-900 leading-[1.15] sm:leading-[1.12]">
              Turn Ingredients Into{' '}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-orange-600 via-amber-600 to-amber-500">
                Delicious Possibilities.
              </span>
            </h1>

            {/* Supporting Text */}
            <p className="text-sm sm:text-lg text-stone-600 max-w-2xl mx-auto lg:mx-0 leading-relaxed font-normal">
              Upload a food image, discover your ingredients, and let DishGenie create a personalized recipe for you.
            </p>

            {/* Action Buttons */}
            <div className="pt-2 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link
                to="/detect"
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-7 py-3.5 rounded-full text-base font-semibold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/25 hover:shadow-lg hover:shadow-orange-500/30 transition-all duration-200 hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
              >
                <span>Start Cooking</span>
                <ArrowRight className="w-4 h-4" />
              </Link>

              <button
                type="button"
                onClick={() => handleScroll('#how-it-works')}
                className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-7 py-3.5 rounded-full text-base font-semibold text-stone-700 bg-white border border-stone-200/90 hover:bg-stone-50 hover:border-stone-300 shadow-xs transition-all duration-200 hover:-translate-y-0.5 cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 focus-visible:ring-offset-2"
              >
                <span>How It Works</span>
              </button>
            </div>

            {/* Trust / Capability Highlights */}
            <div className="pt-6 border-t border-stone-200/60 grid grid-cols-3 gap-2 sm:gap-4 max-w-lg mx-auto lg:mx-0 text-left">
              <div>
                <p className="text-xl sm:text-2xl font-bold text-stone-900">100%</p>
                <p className="text-xs text-stone-500 mt-0.5">Custom to your pantry</p>
              </div>
              <div>
                <p className="text-xl sm:text-2xl font-bold text-stone-900">Zero</p>
                <p className="text-xs text-stone-500 mt-0.5">Food waste goal</p>
              </div>
              <div>
                <p className="text-xl sm:text-2xl font-bold text-stone-900">Vision + AI</p>
                <p className="text-xs text-stone-500 mt-0.5">Two-stage pipeline</p>
              </div>
            </div>
          </div>

          {/* Right Column: Food-Tech Visual Showcase */}
          <div className="lg:col-span-5 relative flex justify-center">
            
            {/* Visual Card Container */}
            <div className="w-full max-w-md bg-white rounded-3xl p-5 sm:p-6 shadow-xl shadow-stone-900/5 border border-stone-200/80 relative">
              
              {/* Card Header Bar */}
              <div className="flex items-center justify-between pb-4 border-b border-stone-100">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-rose-400"></div>
                  <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                  <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                </div>
                <div className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-orange-700 bg-orange-50 px-2.5 py-1 rounded-full border border-orange-100">
                  <Camera className="w-3 h-3 text-orange-600" />
                  Vision Detection Demo
                </div>
              </div>

              {/* Graphic Stage: Simulated Food Photography with Ingredient Detection Bounding Markers */}
              <div className="mt-4 relative rounded-2xl bg-gradient-to-br from-amber-50 via-orange-50/50 to-stone-100 border border-stone-200/70 p-6 sm:p-8 overflow-hidden min-h-[260px] flex flex-col justify-between">
                
                {/* Background Food Art SVG Elements */}
                <div className="absolute inset-0 opacity-15 flex items-center justify-center pointer-events-none">
                  <div className="w-48 h-48 rounded-full border-4 border-dashed border-orange-400"></div>
                </div>

                {/* Simulated Computer Vision Scanning Target */}
                <div className="relative z-10 flex flex-col items-center justify-center text-center py-4">
                  <div className="w-20 h-20 rounded-2xl bg-white shadow-md border border-orange-200/70 flex items-center justify-center text-4xl mb-3">
                    🥗
                  </div>
                  <div className="text-sm font-bold text-stone-800">Fresh Harvest Bowl</div>
                  <div className="text-xs text-stone-500">Input Image Preview</div>
                </div>

                {/* Simulated Detected Ingredient Chips */}
                <div className="relative z-10 space-y-2 pt-2">
                  <div className="flex items-center justify-between text-xs bg-white/90 backdrop-blur-xs px-3 py-2 rounded-xl border border-stone-200 shadow-xs">
                    <span className="flex items-center gap-2 font-medium text-stone-800">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      Fresh Tomatoes
                    </span>
                    <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      Detected 98%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs bg-white/90 backdrop-blur-xs px-3 py-2 rounded-xl border border-stone-200 shadow-xs">
                    <span className="flex items-center gap-2 font-medium text-stone-800">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      Sweet Bell Pepper
                    </span>
                    <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      Detected 95%
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs bg-white/90 backdrop-blur-xs px-3 py-2 rounded-xl border border-stone-200 shadow-xs">
                    <span className="flex items-center gap-2 font-medium text-stone-800">
                      <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                      Garlic & Sweet Basil
                    </span>
                    <span className="text-[11px] font-mono font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md">
                      Detected 92%
                    </span>
                  </div>
                </div>
              </div>

              {/* Floating Match Card */}
              <div className="mt-4 bg-stone-900 text-white rounded-2xl p-4 shadow-lg flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-orange-500/20 text-orange-400 flex items-center justify-center">
                    <Sparkles className="w-5 h-5 text-orange-400" />
                  </div>
                  <div>
                    <p className="text-xs text-stone-400 font-medium">Recipe Match</p>
                    <p className="text-sm font-semibold text-white">Creamy Tuscan Pasta</p>
                  </div>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-amber-300 bg-amber-400/10 px-2.5 py-1 rounded-full font-medium">
                  <Clock className="w-3.5 h-3.5" />
                  25 min
                </div>
              </div>

              {/* Bottom Notification */}
              <div className="mt-3 flex items-center justify-center gap-1.5 text-[11px] text-stone-600">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Simulated concept preview • Local GenAI pipeline planned</span>
              </div>
            </div>
          </div>

        </div>
      </div>
    </section>
  )
}
