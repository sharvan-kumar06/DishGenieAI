import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Detect from './pages/Detect'
import Recipe from './pages/Recipe'
import HistoryPage from './pages/HistoryPage'
import FavoritesPage from './pages/FavoritesPage'
import NotFound from './pages/NotFound'
import Footer from './components/Footer'
import ScrollToTop from './components/ScrollToTop'

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-[#faf8f5] text-stone-900 selection:bg-orange-200 selection:text-orange-900">
      <ScrollToTop />
      <Navbar />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/detect" element={<Detect />} />
          <Route path="/recipe" element={<Recipe />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/favorites" element={<FavoritesPage />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </div>
  )
}
