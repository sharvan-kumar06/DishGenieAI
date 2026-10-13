import { Link } from 'react-router-dom'
import {
  Camera,
  Scan,
  CheckCircle2,
  Sliders,
  Sparkles,
  Utensils,
  ArrowRight,
  ShieldCheck,
  Layers,
  ArrowDown,
} from 'lucide-react'

export default function HowItWorksPage() {
  const pipelineNodes = [
    { label: 'Food Image', icon: Camera, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200' },
    { label: 'CNN Vision', icon: Scan, color: 'text-orange-600', bg: 'bg-orange-50', border: 'border-orange-200' },
    { label: 'Ingredients', icon: CheckCircle2, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200' },
    { label: 'Preferences', icon: Sliders, color: 'text-blue-600', bg: 'bg-blue-50', border: 'border-blue-200' },
    { label: 'Local GenAI', icon: Sparkles, color: 'text-purple-600', bg: 'bg-purple-50', border: 'border-purple-200' },
    { label: 'Recipe Output', icon: Utensils, color: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200' },
  ]

  const steps = [
    {
      step: '01',
      title: 'Upload Food Image',
      tag: 'Input Stage',
      icon: Camera,
      description:
        'Start by uploading or dragging a photo of a vegetable from your pantry or fridge. DishGenie accepts standard JPG, JPEG, and PNG images and sends the image data to our backend computer vision service for inspection.',
      notes: 'Image preprocessing resizes and normalizes the photo to match the neural network input format.',
    },
    {
      step: '02',
      title: 'Ingredient Detection',
      tag: 'CNN Vision Analysis',
      icon: Scan,
      description:
        'A custom Convolutional Neural Network (CNN) trained on 247 distinct produce and food classes analyzes the image features—such as texture, contour, and coloration—to predict the ingredient with an associated confidence score.',
      notes: 'Important: The CNN classifies one vegetable per image. You can scan or add additional vegetables sequentially to build your pantry.',
    },
    {
      step: '03',
      title: 'Confirm & Refine Ingredients',
      tag: 'Human in the Loop',
      icon: CheckCircle2,
      description:
        'You review the detected ingredient before any recipe is created. You can accept the prediction with a single click, correct it using our 247-class ingredient selector, remove items, or add multiple vegetables.',
      notes: 'Human confirmation ensures that potential vision model inaccuracies never ruin your final recipe.',
    },
    {
      step: '04',
      title: 'Set Culinary Preferences',
      tag: 'Constraint Guidance',
      icon: Sliders,
      description:
        'Customize your meal parameters to match your kitchen reality. Configure Diet Type (Vegetarian, Vegan, Non-Vegetarian), Cuisine Style (Indian, Italian, Mexican, etc.), Cooking Time (15 to 60+ min), Cooking Skill (Easy, Medium, Hard), Portion Size, and complementary pantry spices.',
      notes: 'Preferences ensure generated instructions fit your dietary restrictions and available cooking time.',
    },
    {
      step: '05',
      title: 'Generate Recipe with Local AI',
      tag: 'On-Device Synthesis',
      icon: Sparkles,
      description:
        'Your verified pantry ingredients and preference parameters are passed to our local SQLite recipe database for candidate retrieval, then synthesized by a pretrained Qwen2.5-1.5B model running directly in Python via Hugging Face Transformers.',
      notes: 'Zero external cloud APIs: All retrieval and text generation execute on-device without OpenAI, Gemini, or third-party cloud costs.',
    },
    {
      step: '06',
      title: 'Get Your Personalized Recipe',
      tag: 'Culinary Output',
      icon: Utensils,
      description:
        'DishGenie parses the generated output into a structured, readable format. You receive a complete Recipe Name, culinary Description, required Ingredients, numbered step-by-step Instructions, smart Substitutions, and an interactive Shopping List.',
      notes: 'Features print-friendly layouts and interactive shopping checkboxes that track completed items.',
    },
  ]

  return (
    <div className="min-h-screen py-12 md:py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-16 animate-in fade-in duration-300">
      
      {/* 1. Header Section */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-orange-100/80 border border-orange-200 text-orange-800 text-xs font-bold uppercase tracking-wider shadow-xs">
          <Layers className="w-4 h-4 text-orange-600" />
          <span>System Architecture & Pipeline</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-stone-900 tracking-tight">
          How DishGenie Works
        </h1>
        <p className="text-base sm:text-lg text-stone-600 leading-relaxed">
          From a photo of raw vegetables to a customized, step-by-step recipe—powered by a two-stage pipeline combining computer vision and local Generative AI.
        </p>
      </div>

      {/* 2. Visual Pipeline Flow */}
      <div className="bg-white rounded-3xl p-6 sm:p-10 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-6">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pb-4 border-b border-stone-100">
          <div>
            <h2 className="text-lg font-bold text-stone-900">
              The DishGenie AI Pipeline
            </h2>
            <p className="text-xs text-stone-500">
              End-to-end data flow from user image capture to structured culinary instructions
            </p>
          </div>
          <span className="text-xs font-semibold px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
            100% Local Inference
          </span>
        </div>

        {/* Pipeline Diagram (Horizontal on Desktop, Vertical on Mobile) */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-6 gap-4 items-center">
          {pipelineNodes.map((node, idx) => {
            const Icon = node.icon
            return (
              <div key={node.label} className="flex flex-col lg:flex-row items-center w-full">
                <div
                  className={`w-full p-4 rounded-2xl ${node.bg} border ${node.border} text-center flex flex-col items-center justify-center space-y-2 shadow-xs transition-all hover:-translate-y-1`}
                >
                  <div className={`w-10 h-10 rounded-xl bg-white flex items-center justify-center ${node.color} shadow-xs`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <span className="text-xs font-extrabold text-stone-800 tracking-tight">
                    {node.label}
                  </span>
                  <span className="text-[10px] text-stone-500 font-mono">
                    Step {idx + 1}
                  </span>
                </div>

                {/* Arrow Connector (Down on Mobile, Right on Desktop) */}
                {idx < pipelineNodes.length - 1 && (
                  <div className="lg:hidden py-1 text-stone-300">
                    <ArrowDown className="w-4 h-4 text-stone-400" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>

      {/* 3. Detailed 6-Step Breakdown */}
      <div className="space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900">
            Step-by-Step Workflow
          </h2>
          <p className="text-sm text-stone-600">
            Here is what happens under the hood during each phase of recipe creation.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
          {steps.map((item) => {
            const StepIcon = item.icon
            return (
              <div
                key={item.step}
                className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-xl shadow-stone-900/5 flex flex-col justify-between space-y-6 hover:border-orange-200 transition-colors"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="w-10 h-10 rounded-2xl bg-stone-900 text-white font-mono text-sm font-black flex items-center justify-center shadow-xs">
                      {item.step}
                    </span>
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                      {item.tag}
                    </span>
                  </div>

                  <div className="space-y-2">
                    <h3 className="text-xl font-bold text-stone-900 flex items-center gap-2">
                      <StepIcon className="w-5 h-5 text-orange-600" />
                      <span>{item.title}</span>
                    </h3>
                    <p className="text-sm text-stone-600 leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </div>

                <div className="pt-4 border-t border-stone-100 flex items-start gap-2 text-xs text-stone-500 bg-stone-50/70 p-3.5 rounded-2xl">
                  <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span className="leading-snug">{item.notes}</span>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* 4. Bottom Call to Action */}
      <div className="rounded-3xl bg-gradient-to-br from-stone-900 via-stone-800 to-amber-950 text-white p-8 sm:p-12 text-center space-y-6 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-orange-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-2xl mx-auto space-y-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Ready to turn your ingredients into a recipe?
          </h2>
          <p className="text-sm sm:text-base text-stone-300">
            Upload a vegetable photo, confirm your pantry, and let our local AI create your custom cooking plan.
          </p>
          <div className="pt-2 flex justify-center">
            <Link
              to="/detect"
              className="inline-flex items-center gap-2.5 px-8 py-4 rounded-full text-base font-bold text-stone-900 bg-gradient-to-r from-amber-400 to-orange-400 hover:from-amber-300 hover:to-orange-300 shadow-lg shadow-orange-500/25 transition-all hover:-translate-y-0.5 cursor-pointer"
            >
              <span>Try DishGenie</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        </div>
      </div>

    </div>
  )
}
