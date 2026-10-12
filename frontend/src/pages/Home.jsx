import Hero from '../components/Hero'
import Features from '../components/Features'
import HowItWorks from '../components/HowItWorks'
import RecipePreview from '../components/RecipePreview'
import CTA from '../components/CTA'

export default function Home() {
  return (
    <div>
      <Hero />
      <Features />
      <HowItWorks />
      <RecipePreview />
      <CTA />
    </div>
  )
}
