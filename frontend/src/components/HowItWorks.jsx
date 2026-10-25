import { UploadCloud, Scan, SlidersHorizontal, Utensils, ArrowRight } from 'lucide-react'

export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      title: 'Upload',
      description: 'Upload an image of your ingredients.',
      icon: UploadCloud,
      badge: 'Step 1',
    },
    {
      number: '02',
      title: 'Detect',
      description: 'Our computer vision model identifies the ingredients.',
      icon: Scan,
      badge: 'Step 2',
    },
    {
      number: '03',
      title: 'Choose Dish Style',
      description: 'Select your preferred candidate recipe style, dietary goals, and cooking preferences.',
      icon: SlidersHorizontal,
      badge: 'Step 3',
    },
    {
      number: '04',
      title: 'Cook',
      description: 'Get a personalized recipe with instructions and substitutions.',
      icon: Utensils,
      badge: 'Step 4',
    },
  ]

  return (
    <section id="how-it-works" className="py-20 md:py-28 bg-[#faf8f5]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-100/70 border border-amber-200 text-amber-800 text-xs font-semibold uppercase tracking-wider mb-3">
            Workflow Process
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-stone-900">
            How DishGenie Works
          </h2>
          <p className="mt-4 text-base sm:text-lg text-stone-600">
            A seamless journey from taking a photo of what is in your fridge to enjoying a homemade dish.
          </p>
        </div>

        {/* 4 Connected Steps Grid */}
        <div className="relative">
          
          {/* Desktop Connecting Line behind cards */}
          <div className="hidden lg:block absolute top-1/2 left-8 right-8 h-0.5 bg-gradient-to-r from-orange-200 via-amber-200 to-orange-200 -translate-y-8 z-0"></div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 relative z-10">
            {steps.map((step, idx) => {
              const Icon = step.icon
              return (
                <div
                  key={step.number}
                  className="bg-white rounded-3xl p-6 sm:p-7 border border-stone-200/90 shadow-sm hover:shadow-xl hover:shadow-orange-950/5 transition-all duration-300 hover:-translate-y-1.5 flex flex-col justify-between"
                >
                  <div>
                    {/* Top Step Number & Icon */}
                    <div className="flex items-center justify-between mb-6">
                      <div className="w-12 h-12 rounded-2xl bg-orange-50 border border-orange-100 flex items-center justify-center text-orange-600 shadow-xs">
                        <Icon className="w-6 h-6" />
                      </div>
                      <span className="font-mono text-2xl font-black text-stone-300">
                        {step.number}
                      </span>
                    </div>

                    {/* Step Title */}
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-xl font-bold text-stone-900">
                        {step.title}
                      </h3>
                    </div>

                    {/* Step Description */}
                    <p className="text-sm text-stone-600 leading-relaxed">
                      {step.description}
                    </p>
                  </div>

                  {/* Step Footer with Indicator */}
                  <div className="mt-6 pt-4 border-t border-stone-100 flex items-center justify-between text-xs font-semibold text-orange-700">
                    <span>{step.badge}</span>
                    {idx < steps.length - 1 && (
                      <span className="text-stone-300">
                        <ArrowRight className="w-3.5 h-3.5" />
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>

      </div>
    </section>
  )
}
