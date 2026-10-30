import { Music, Github, Sun, Moon } from 'lucide-react'
import { useState, useEffect } from 'react'
import { AuthButton } from '../hooks/useAuth'

function Header() {
  const [isDark, setIsDark] = useState(false)

  useEffect(() => {
    // Check system preference
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    setIsDark(mediaQuery.matches)
    
    const handler = (e) => setIsDark(e.matches)
    mediaQuery.addEventListener('change', handler)
    return () => mediaQuery.removeEventListener('change', handler)
  }, [])

  const toggleTheme = () => {
    setIsDark(!isDark)
    document.documentElement.classList.toggle('dark')
  }

  return (
    <header className="border-b border-border bg-bg-card/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="container flex items-center justify-between h-16">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 text-primary hover:text-primary-hover transition-colors" aria-label="FretIQ Home">
          <Music className="w-8 h-8" />
          <span className="font-bold text-xl hidden sm:block">Music Chords</span>
        </a>

        <div className="flex items-center gap-4">
          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            className="btn btn-ghost btn-icon p-2 rounded-lg"
            aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
          </button>

          {/* Auth button */}
          <AuthButton />
        </div>
      </div>
    </header>
  )
}

export default Header