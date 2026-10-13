import { Link } from 'react-router-dom'
import {
  UtensilsCrossed,
  Sparkles,
  Camera,
  Server,
  Code2,
  Cpu,
  ShieldCheck,
  CheckCircle2,
  ArrowRight,
  ArrowDown,
  Sliders,
  FileCheck,
  Users,
  Clock,
  BookOpen,
} from 'lucide-react'

export default function AboutPage() {
  const techStack = [
    {
      layer: 'Frontend Client',
      tools: ['React 18', 'Vite', 'JavaScript / JSX', 'Tailwind CSS', 'React Router'],
      description: 'Single-page responsive user interface with drag-and-drop image upload, interactive ingredient tagging, and print-ready recipe sheets.',
      color: 'border-blue-200 bg-blue-50/50',
      badgeColor: 'bg-blue-100 text-blue-800',
    },
    {
      layer: 'Backend API Service',
      tools: ['FastAPI', 'Python 3.11', 'Uvicorn', 'Pydantic V2', 'CORS Middleware'],
      description: 'Asynchronous RESTful server providing multipart image handling, model caching across lifespans, and structured data validation.',
      color: 'border-emerald-200 bg-emerald-50/50',
      badgeColor: 'bg-emerald-100 text-emerald-800',
    },
    {
      layer: 'Computer Vision Model',
      tools: ['TensorFlow 2.19', 'Keras', 'Custom CNN', '247 Produce & Food Classes', 'PIL'],
      description: 'Trained convolutional neural network predicting single-vegetable classes with softmax probabilities and top-3 ranked confidence outputs.',
      color: 'border-orange-200 bg-orange-50/50',
      badgeColor: 'bg-orange-100 text-orange-800',
    },
    {
      layer: 'Generative AI & Recipe DB',
      tools: ['Hugging Face Transformers', 'Qwen2.5-3B-Instruct', 'SQLite FTS5', 'PyTorch'],
      description: 'Pretrained causal language model combined with persistent SQLite database retrieval (RAG) to synthesize customized recipes without external APIs.',
      color: 'border-purple-200 bg-purple-50/50',
      badgeColor: 'bg-purple-100 text-purple-800',
    },
  ]

  const highlights = [
    {
      title: 'Image-Based Ingredient Detection',
      icon: Camera,
      description: 'Identify ingredients directly from photos using an integrated Convolutional Neural Network trained on 247 produce and food categories.',
    },
    {
      title: 'User-Controlled Confirmation',
      icon: CheckCircle2,
      description: 'Human-in-the-loop validation gives you full control to verify, change, remove, or manually add ingredients before recipe generation.',
    },
    {
      title: 'Personalized Recipe Synthesis',
      icon: Sparkles,
      description: 'Transforms verified pantry ingredients into customized recipes with structured titles, ingredients, instructions, and portioning.',
    },
    {
      title: 'Dietary & Cuisine Preferences',
      icon: Sliders,
      description: 'Tailors each generated meal to specific diets (Vegetarian, Vegan, Non-Veg) and world cuisines (Indian, Italian, Mexican, etc.).',
    },
    {
      title: 'Cooking Time & Difficulty Selection',
      icon: Clock,
      description: 'Respects kitchen constraints with selectable preparation windows (15, 30, 45, 60+ minutes) and appropriate skill levels.',
    },
    {
      title: 'Interactive Shopping Lists',
      icon: FileCheck,
      description: 'Identifies missing pantry essentials and generates interactive, checkable shopping lists with state tracking.',
    },
    {
      title: '100% Local AI Processing',
      icon: Cpu,
      description: 'Both the CNN model and the Qwen2.5 language model run on your local machine—zero paid APIs, complete privacy.',
    },
  ]

  return (
    <div className="min-h-screen py-12 md:py-20 px-4 sm:px-6 lg:px-8 max-w-6xl mx-auto space-y-16 animate-in fade-in duration-300">
      
      {/* 1. Header & What is DishGenie */}
      <div className="text-center max-w-3xl mx-auto space-y-4">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-amber-100/80 border border-amber-200 text-amber-800 text-xs font-bold uppercase tracking-wider shadow-xs">
          <UtensilsCrossed className="w-4 h-4 text-amber-600" />
          <span>About The Project</span>
        </div>
        <h1 className="text-3xl sm:text-4xl lg:text-5xl font-extrabold text-stone-900 tracking-tight">
          What is DishGenie?
        </h1>
        <p className="text-base sm:text-lg text-stone-600 leading-relaxed">
          DishGenie is an AI-powered recipe assistance system that combines computer vision and local generative AI to help users turn available kitchen ingredients into delicious, practical meal ideas.
        </p>
      </div>

      {/* 2. Core Idea: Two-Stage AI Architecture */}
      <div className="bg-white rounded-3xl p-6 sm:p-10 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-8">
        <div>
          <span className="text-xs font-bold uppercase tracking-wider text-orange-600">The Core Philosophy</span>
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 mt-1">
            Bridging Computer Vision & Generative AI
          </h2>
          <p className="text-sm sm:text-base text-stone-600 mt-2 leading-relaxed max-w-3xl">
            Instead of relying on a single generalist model, DishGenie divides the cooking pipeline into two distinct, specialized AI stages with human verification connecting them.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Stage 1 */}
          <div className="p-6 rounded-2xl bg-orange-50/60 border border-orange-200 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-orange-500 text-white flex items-center justify-center font-bold">
                1
              </div>
              <div>
                <h3 className="font-extrabold text-stone-900 text-base">Stage 1: Computer Vision</h3>
                <span className="text-xs text-orange-700 font-medium">TensorFlow CNN Feature Extraction</span>
              </div>
            </div>
            <p className="text-sm text-stone-600 leading-relaxed">
              Analyzes raw food photos and predicts ingredient labels with confidence scores across 247 trained produce and food categories.
            </p>
          </div>

          {/* Stage 2 */}
          <div className="p-6 rounded-2xl bg-amber-50/60 border border-amber-200 space-y-3">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-600 text-white flex items-center justify-center font-bold">
                2
              </div>
              <div>
                <h3 className="font-extrabold text-stone-900 text-base">Stage 2: Generative AI & Recipe DB</h3>
                <span className="text-xs text-amber-800 font-medium">Local Qwen2.5 Language Synthesis & SQLite</span>
              </div>
            </div>
            <p className="text-sm text-stone-600 leading-relaxed">
              Retrieves matched recipes from the local SQLite database and uses Qwen2.5 to synthesize complete culinary recipes, instructions, substitutions, and shopping checklists.
            </p>
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 flex items-start gap-3 text-xs sm:text-sm text-stone-700">
          <ShieldCheck className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <p>
            <strong className="text-stone-900">Human in the Loop:</strong> The user retains full control to inspect, confirm, or edit detected ingredients before recipe generation begins—preventing vision classification errors from propagating into cooking instructions.
          </p>
        </div>
      </div>

      {/* 3. Visual System Architecture Diagram */}
      <div className="bg-white rounded-3xl p-6 sm:p-10 border border-stone-200 shadow-xl shadow-stone-900/5 space-y-8">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900">
            System Architecture
          </h2>
          <p className="text-xs sm:text-sm text-stone-500">
            A visual overview of data flow from client upload to on-device model execution
          </p>
        </div>

        {/* Polished Flow Diagram */}
        <div className="max-w-2xl mx-auto space-y-3">
          
          {/* Node 1: User */}
          <div className="p-4 rounded-2xl bg-stone-900 text-white text-center shadow-md">
            <div className="flex items-center justify-center gap-2 font-bold text-sm">
              <Users className="w-4 h-4 text-amber-400" />
              <span>USER</span>
            </div>
            <p className="text-xs text-stone-300 mt-0.5">Uploads food photo, confirms pantry, selects preferences</p>
          </div>

          <div className="flex justify-center text-stone-400">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Node 2: React Frontend */}
          <div className="p-4 rounded-2xl bg-blue-50 border border-blue-200 text-center shadow-xs">
            <div className="flex items-center justify-center gap-2 font-bold text-sm text-blue-900">
              <Code2 className="w-4 h-4 text-blue-600" />
              <span>REACT FRONTEND (Vite Client)</span>
            </div>
            <p className="text-xs text-blue-700 mt-0.5">Handles UI state, camera inputs, and responsive displays</p>
          </div>

          <div className="flex justify-center text-stone-400">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Node 3: FastAPI Backend */}
          <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200 text-center shadow-xs">
            <div className="flex items-center justify-center gap-2 font-bold text-sm text-emerald-900">
              <Server className="w-4 h-4 text-emerald-600" />
              <span>FASTAPI BACKEND (Python REST Service)</span>
            </div>
            <p className="text-xs text-emerald-700 mt-0.5">Asynchronous routing, input validation, and model lifecycle management</p>
          </div>

          <div className="flex justify-center text-stone-400">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Service Boxes Container */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            
            {/* Box A: Vision Service */}
            <div className="p-5 rounded-2xl bg-orange-50/70 border-2 border-orange-300 space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-orange-200 text-orange-900">
                Service 1
              </span>
              <h4 className="font-extrabold text-stone-900 text-sm">Computer Vision Service</h4>
              <p className="text-xs text-stone-600">
                TensorFlow / Keras CNN model predicts vegetable class from image
              </p>
            </div>

            {/* Box B: Recipe Service */}
            <div className="p-5 rounded-2xl bg-purple-50/70 border-2 border-purple-300 space-y-2">
              <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-purple-200 text-purple-900">
                Service 2
              </span>
              <h4 className="font-extrabold text-stone-900 text-sm">Recipe Generation Service</h4>
              <p className="text-xs text-stone-600">
                Local Qwen2.5 model and SQLite database synthesize tailored cooking steps
              </p>
            </div>

          </div>

          <div className="flex justify-center text-stone-400">
            <ArrowDown className="w-4 h-4" />
          </div>

          {/* Node 4: React Recipe Page */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-orange-500 to-amber-600 text-white text-center shadow-md">
            <div className="flex items-center justify-center gap-2 font-bold text-sm">
              <BookOpen className="w-4 h-4 text-white" />
              <span>REACT RECIPE PAGE (/recipe)</span>
            </div>
            <p className="text-xs text-orange-100 mt-0.5">Renders verified ingredients, cooking steps, substitutions, and shopping checklist</p>
          </div>

        </div>
      </div>

      {/* 4. Actual Technology Stack Breakdown */}
      <div className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900">
            Technology Stack
          </h2>
          <p className="text-xs sm:text-sm text-stone-500">
            Libraries and frameworks actively powering the DishGenie platform
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {techStack.map((tech) => (
            <div
              key={tech.layer}
              className={`p-6 rounded-3xl border ${tech.color} shadow-xs space-y-4`}
            >
              <div className="flex items-center justify-between">
                <h3 className="font-extrabold text-stone-900 text-base">{tech.layer}</h3>
                <span className={`text-[11px] font-bold px-2.5 py-1 rounded-full ${tech.badgeColor}`}>
                  Active
                </span>
              </div>

              <div className="flex flex-wrap gap-1.5">
                {tech.tools.map((t) => (
                  <span
                    key={t}
                    className="px-2.5 py-1 rounded-xl bg-white border border-stone-200 text-xs font-semibold text-stone-800 shadow-2xs font-mono"
                  >
                    {t}
                  </span>
                ))}
              </div>

              <p className="text-xs sm:text-sm text-stone-600 leading-relaxed">
                {tech.description}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* 5. Project Highlights */}
      <div className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900">
            Key Capabilities
          </h2>
          <p className="text-xs sm:text-sm text-stone-500">
            Core features engineered for college PBL demonstration
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {highlights.map((item) => {
            const Icon = item.icon
            return (
              <div
                key={item.title}
                className="bg-white rounded-3xl p-6 border border-stone-200 shadow-xs hover:border-orange-200 transition-colors space-y-3"
              >
                <div className="w-10 h-10 rounded-2xl bg-orange-50 border border-orange-200 flex items-center justify-center text-orange-600">
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-bold text-stone-900 text-sm">{item.title}</h3>
                <p className="text-xs text-stone-600 leading-relaxed">
                  {item.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* 6. Bottom Call to Action */}
      <div className="rounded-3xl bg-gradient-to-br from-stone-900 via-stone-800 to-amber-950 text-white p-8 sm:p-12 text-center space-y-6 shadow-2xl relative overflow-hidden">
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-orange-500/20 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-2xl mx-auto space-y-4">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
            Ready to turn your ingredients into a recipe?
          </h2>
          <p className="text-sm sm:text-base text-stone-300">
            Experience the full two-stage AI pipeline right in your browser.
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
