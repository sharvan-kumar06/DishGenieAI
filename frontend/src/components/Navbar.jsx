import { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { UtensilsCrossed, Menu, X, ArrowRight } from 'lucide-react'

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)
  const location = useLocation()

  const navLinks = [
    { label: 'Home', href: '/' },
    { label: 'Studio', href: '/detect' },
    { label: 'History', href: '/history' },
    { label: 'Favorites', href: '/favorites' },
  ]

  // Auto-close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false)
  }, [location.pathname])

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && mobileMenuOpen) {
        setMobileMenuOpen(false)
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [mobileMenuOpen])

  const handleLinkClick = (href) => {
    setMobileMenuOpen(false)
    if (location.pathname === href) {
      window.scrollTo({ top: 0, behavior: 'smooth' })
    }
  }

  return (
    <header className="sticky top-0 z-50 bg-[#faf8f5]/85 backdrop-blur-md border-b border-stone-200/80 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-20">
          {/* Brand Logo */}
          <Link
            to="/"
            onClick={() => handleLinkClick('/')}
            className="flex items-center gap-3 group rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
          >
            <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-amber-600 via-orange-500 to-amber-500 flex items-center justify-center text-white shadow-md shadow-orange-500/20 group-hover:scale-105 transition-transform duration-200">
              <UtensilsCrossed className="w-5 h-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold tracking-tight text-stone-900 group-hover:text-amber-700 transition-colors">
                Dish<span className="text-orange-600">Genie</span>
              </span>
              <span className="text-[10px] font-medium tracking-wider uppercase text-stone-600 -mt-0.5">
                Smart Recipe Assistant
              </span>
            </div>
          </Link>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.href
              return (
                <Link
                  key={link.label}
                  to={link.href}
                  onClick={() => handleLinkClick(link.href)}
                  className={`text-sm font-medium transition-colors relative py-1 hover:text-stone-900 hover:after:w-full after:transition-all after:duration-200 after:absolute after:bottom-0 after:left-0 after:h-0.5 after:bg-orange-500 rounded-md focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    isActive
                      ? 'text-orange-600 font-bold after:w-full'
                      : 'text-stone-600 after:w-0'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
          </nav>

          {/* Desktop Right CTA -> /detect */}
          <div className="hidden md:flex items-center gap-3">
            <Link
              to="/detect"
              onClick={() => handleLinkClick('/detect')}
              className={`inline-flex items-center gap-2 px-5 py-2.5 rounded-full text-sm font-semibold text-white bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700 shadow-md shadow-orange-500/20 hover:shadow-lg hover:shadow-orange-500/30 transition-all duration-200 hover:-translate-y-0.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2 ${
                location.pathname === '/detect' ? 'ring-2 ring-orange-400 ring-offset-2' : ''
              }`}
            >
              <span>Get Started</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden w-11 h-11 flex items-center justify-center rounded-xl text-stone-600 hover:text-stone-900 hover:bg-stone-100 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500"
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-drawer"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer Menu */}
      {mobileMenuOpen && (
        <div
          id="mobile-nav-drawer"
          className="md:hidden bg-[#faf8f5] border-b border-stone-200 px-4 pt-3 pb-6 shadow-lg animate-in fade-in slide-in-from-top duration-200"
        >
          <div className="flex flex-col gap-2">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.href
              return (
                <Link
                  key={link.label}
                  to={link.href}
                  onClick={() => handleLinkClick(link.href)}
                  className={`px-4 py-3 rounded-xl text-base font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 ${
                    isActive
                      ? 'bg-orange-50 text-orange-600 font-bold'
                      : 'text-stone-700 hover:bg-stone-100/80'
                  }`}
                >
                  {link.label}
                </Link>
              )
            })}
            <div className="pt-2">
              <Link
                to="/detect"
                onClick={() => handleLinkClick('/detect')}
                className="w-full flex items-center justify-center gap-2 px-5 py-3.5 rounded-xl text-sm font-semibold text-white bg-gradient-to-r from-orange-500 to-amber-600 shadow-md shadow-orange-500/20 focus:outline-none focus-visible:ring-2 focus-visible:ring-orange-500 focus-visible:ring-offset-2"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
