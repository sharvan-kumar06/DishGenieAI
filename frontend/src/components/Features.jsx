import { Camera, Sparkles, ShoppingBag } from 'lucide-react'
import FeatureCard from './FeatureCard'

export default function Features() {
  const features = [
    {
      icon: Camera,
      title: 'Detect Ingredients',
      description: 'Upload a food image and identify ingredients using computer vision.',
      tag: 'CNN Vision',
    },
    {
      icon: Sparkles,
      title: 'Generate Recipes',
      description: 'Turn your ingredients and preferences into personalized recipes.',
      tag: 'Local GenAI',
    },
    {
      icon: ShoppingBag,
      title: 'Smart Shopping List',
      description: 'Get a convenient list of additional ingredients you may need.',
      tag: 'Pantry Optimizer',
    },
  ]

  return (
    <section id="features" className="py-20 md:py-28 bg-white border-y border-stone-200/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Section Heading */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-50 border border-orange-200/70 text-orange-700 text-xs font-semibold uppercase tracking-wider mb-3">
            Core Capabilities
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-stone-900">
            Your Smart Kitchen Assistant
          </h2>
          <p className="mt-4 text-base sm:text-lg text-stone-600">
            DishGenie connects visual ingredient recognition with generative intelligence to streamline meal planning.
          </p>
        </div>

        {/* 3 Feature Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {features.map((feature) => (
            <FeatureCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              tag={feature.tag}
            />
          ))}
        </div>

        {/* Informative Note for PBL Demonstration */}
        <div className="mt-12 text-center px-2">
          <p className="text-xs text-stone-600 bg-stone-50 border border-stone-200 inline-block px-4 py-2.5 rounded-2xl sm:rounded-full max-w-full text-left sm:text-center leading-relaxed">
            💡 Powered by a trained TensorFlow CNN and local FLAN-T5 model running on-device for this college PBL project.
          </p>
        </div>

      </div>
    </section>
  )
}
