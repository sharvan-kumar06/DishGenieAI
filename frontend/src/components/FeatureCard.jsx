export default function FeatureCard({ icon: Icon, title, description, tag }) {
  return (
    <div className="group relative bg-white rounded-3xl p-8 border border-stone-200/80 shadow-xs hover:shadow-xl hover:shadow-orange-950/5 transition-all duration-300 hover:-translate-y-1.5 flex flex-col justify-between">
      <div>
        {/* Header with Icon and Stage Badge */}
        <div className="flex items-center justify-between mb-6">
          <div className="w-14 h-14 rounded-2xl bg-orange-50 border border-orange-100/80 flex items-center justify-center text-orange-600 group-hover:scale-110 group-hover:bg-gradient-to-tr group-hover:from-orange-500 group-hover:to-amber-500 group-hover:text-white group-hover:shadow-md group-hover:shadow-orange-500/20 transition-all duration-300">
            <Icon className="w-7 h-7" />
          </div>
          <span className="text-[11px] font-semibold uppercase tracking-wider text-stone-600 bg-stone-100 px-3 py-1 rounded-full border border-stone-200">
            {tag}
          </span>
        </div>

        {/* Feature Title */}
        <h3 className="text-xl font-bold text-stone-900 mb-3 group-hover:text-orange-600 transition-colors">
          {title}
        </h3>

        {/* Feature Description */}
        <p className="text-sm text-stone-600 leading-relaxed">
          {description}
        </p>
      </div>

      {/* Card Footer Indicator */}
      <div className="mt-8 pt-4 border-t border-stone-100 flex items-center justify-between text-xs text-stone-600">
        <span>Part of Planned Pipeline</span>
        <span className="w-1.5 h-1.5 rounded-full bg-orange-400 group-hover:scale-150 transition-transform"></span>
      </div>
    </div>
  )
}
