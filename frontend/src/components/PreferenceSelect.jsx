export default function PreferenceSelect({
  label,
  value,
  options,
  onChange,
  hint,
  error,
}) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <label className="text-xs font-bold uppercase tracking-wider text-stone-700">
          {label}
        </label>
        {hint && <span className="text-[11px] text-stone-400">{hint}</span>}
      </div>

      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const optValue = typeof opt === 'object' ? opt.value : opt
          const optLabel = typeof opt === 'object' ? opt.label : String(opt)
          const isSelected = value === optValue

          return (
            <button
              key={String(optValue)}
              type="button"
              onClick={() => onChange(optValue)}
              className={`px-3.5 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-1 ${
                isSelected
                  ? 'bg-gradient-to-r from-orange-500 to-amber-500 text-white shadow-sm shadow-orange-500/20 scale-[1.02]'
                  : 'bg-white text-stone-700 hover:bg-stone-50 border border-stone-200/90 hover:border-stone-300'
              } ${error ? 'border-rose-300' : ''}`}
            >
              {optLabel}
            </button>
          )
        })}
      </div>

      {error && (
        <p className="text-xs text-rose-600 font-medium flex items-center gap-1 animate-in fade-in duration-200" role="alert">
          <span>⚠️</span>
          <span>{error}</span>
        </p>
      )}
    </div>
  )
}
