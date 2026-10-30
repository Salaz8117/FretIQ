import { Music, Github, Sparkles, Zap, Globe, Brain } from 'lucide-react'

function Footer() {
  return (
    <footer className="border-t border-border bg-bg-card/50 mt-auto">
      <div className="container py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <a href="/" className="flex items-center gap-2 text-primary font-bold text-lg mb-4">
              <Music className="w-6 h-6" />
              <span>Music Chords</span>
            </a>
            <p className="text-secondary text-sm max-w-xs">
              Find chords, tabs, strumming patterns, and notes for any song across multiple instruments.
              Powered by AI and web search.
            </p>
          </div>

          {/* Features */}
          <div>
            <h4 className="font-semibold mb-4">Features</h4>
            <ul className="space-y-2 text-sm text-secondary">
              <li className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-primary" />
                AI-generated chords (GPT-4, Claude, Gemini)
              </li>
              <li className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-primary" />
                Web search (Ultimate Guitar, Chordify, more)
              </li>
              <li className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-primary" />
                Local AI support (Ollama, FreeLLMAPI)
              </li>
              <li className="flex items-center gap-2">
                <Brain className="w-4 h-4 text-primary" />
                8+ instruments supported
              </li>
            </ul>
          </div>

          {/* Instruments */}
          <div>
            <h4 className="font-semibold mb-4">Instruments</h4>
            <div className="flex flex-wrap gap-2">
              {['Guitar', 'Ukulele', 'Piano', 'Banjo', 'Mandolin', 'Bass', 'Violin', 'Cello'].map(inst => (
                <span key={inst} className="badge badge-outline text-xs">
                  {inst}
                </span>
              ))}
            </div>
          </div>

          {/* Links */}
          <div>
            <h4 className="font-semibold mb-4">Links</h4>
            <ul className="space-y-2 text-sm text-secondary">
              <li>
                <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-primary transition-colors">
                  <Github className="w-4 h-4" />
                  GitHub Repository
                </a>
              </li>
              <li>
                <a href="/api/docs" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 hover:text-primary transition-colors">
                  <Sparkles className="w-4 h-4" />
                  API Documentation
                </a>
              </li>
              <li>
                <a href="#feedback" className="flex items-center gap-2 hover:text-primary transition-colors">
                  <Zap className="w-4 h-4" />
                  Submit Feedback
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-border flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-muted">
          <p>Built with ❤️ for musicians everywhere</p>
          <div className="flex items-center gap-4">
            <span>v1.0.0</span>
            <a href="https://github.com/Salaz8117/ai-mastery-journey" target="_blank" rel="noopener noreferrer" className="hover:text-primary transition-colors">
              Part of AI Mastery Journey
            </a>
          </div>
        </div>
      </div>
    </footer>
  )
}

export default Footer